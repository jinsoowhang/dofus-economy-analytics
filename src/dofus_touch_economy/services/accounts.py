"""Account admission and durable, throttled invite notification delivery."""

import json
import smtplib
import ssl
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from email.message import EmailMessage
from uuid import uuid4

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from dofus_touch_economy.config import Settings
from dofus_touch_economy.models import UserAccount
from dofus_touch_economy.ownership import OWNER_ID
from dofus_touch_economy.repositories.accounts import AccountRepository


class AccountConflict(ValueError):
    pass


@dataclass(frozen=True)
class Account:
    id: str
    email: str
    status: str
    is_admin: bool
    notification_sent: bool


def _account(row: UserAccount) -> Account:
    return Account(
        row.id, row.email, row.status, row.is_admin, row.notification_sent_at is not None
    )


def send_invite_notification(settings: Settings, account: Account) -> None:
    if settings.invite_mail_config is None:
        raise OSError("Invite mail configuration is unavailable")
    config = json.loads(settings.invite_mail_config.read_text())
    message = EmailMessage()
    message["From"] = config["from_address"]
    message["To"] = settings.owner_email
    message["Subject"] = "Dofus Economy access request"
    message.set_content(
        f"{account.email} requested access to Dofus Economy.\n\n"
        f"Review and approve or deny the request after signing in:\n"
        f"{settings.public_origin}/admin/access-requests\n\n"
        "This email does not approve access. Sales and personal reports stay private.\n"
    )
    context = ssl.create_default_context()
    port = int(config.get("port", 587))
    if config.get("implicit_tls", False):
        smtp = smtplib.SMTP_SSL(config["host"], port, timeout=10, context=context)
    else:
        smtp = smtplib.SMTP(config["host"], port, timeout=10)
    with smtp as connection:
        if not config.get("implicit_tls", False):
            connection.starttls(context=context)
        connection.login(config["username"], config["password"])
        connection.send_message(message)


class AccountService:
    def __init__(self, factory: sessionmaker[Session], settings: Settings, *, notifier=None):
        self.factory = factory
        self.settings = settings
        self.notifier = notifier or send_invite_notification

    def identify(self, subject: str, email: str) -> Account:
        email = email.strip().lower()
        if (
            not subject
            or len(subject) > 255
            or not subject.isascii()
            or len(email) > 320
            or email.count("@") != 1
            or any(char.isspace() or ord(char) < 32 for char in email + subject)
            or "," in email
        ):
            raise AccountConflict("Invalid authenticated account")
        # Serialize bootstrap/first login so concurrent page/asset requests cannot
        # create duplicate accounts or accidentally bind a second owner identity.
        with self.factory() as session:
            repository = AccountRepository(session)
            repository.lock_registry()
            owner = repository.get(OWNER_ID)
            if owner is None:
                owner = UserAccount(
                    id=OWNER_ID, email=self.settings.owner_email, status="approved", is_admin=True
                )
                repository.add(owner)
                session.flush()
            elif owner.email != self.settings.owner_email:
                raise AccountConflict("Configured owner differs from the account registry")
            row = repository.by_subject(subject)
            if row is None:
                same_email = repository.by_email(email)
                if same_email is not None:
                    if same_email.id != OWNER_ID or same_email.google_subject is not None:
                        raise AccountConflict("Email belongs to a different Google identity")
                    row = same_email
                    row.google_subject = subject
                else:
                    row = UserAccount(id=uuid4().hex, google_subject=subject, email=email)
                    repository.add(row)
            elif row.email != email:
                if row.id == OWNER_ID:
                    raise AccountConflict("Owner email changed; update configuration explicitly")
                row.email = email
            try:
                session.commit()
            except IntegrityError as error:
                raise AccountConflict(
                    "Account identity conflicts with an existing account"
                ) from error
            account = _account(row)
        if account.status == "pending":
            self.notify(account.id)
            return self.get(account.id)
        return account

    def get(self, account_id: str) -> Account:
        with self.factory() as session:
            row = AccountRepository(session).get(account_id)
            if row is None:
                raise AccountConflict("Account not found")
            return _account(row)

    def requests(self) -> list[Account]:
        with self.factory() as session:
            return [_account(row) for row in AccountRepository(session).requests()]

    def decide(self, account_id: str, status: str) -> None:
        if account_id == OWNER_ID or status not in {"approved", "denied"}:
            raise AccountConflict("Invalid access decision")
        with self.factory() as session:
            if not AccountRepository(session).decide(account_id, status, datetime.now(UTC)):
                raise AccountConflict("Account not found")
            session.commit()

    def notify(self, account_id: str) -> bool:
        now = datetime.now(UTC)
        with self.factory() as session:
            claimed = AccountRepository(session).claim_notification(
                account_id, now, now - timedelta(minutes=10)
            )
            session.commit()
        if not claimed:
            return False
        account = self.get(account_id)
        try:
            self.notifier(self.settings, account)
        except (OSError, smtplib.SMTPException, ValueError, KeyError):
            # Keep the durable request and retry timestamp. Never log email
            # addresses, credentials, or SMTP exception text in public logs.
            return False
        with self.factory() as session:
            AccountRepository(session).notification_sent(account_id, datetime.now(UTC))
            session.commit()
        return True
