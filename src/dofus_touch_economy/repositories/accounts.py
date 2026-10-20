from datetime import datetime

from sqlalchemy import or_, select, text, update
from sqlalchemy.orm import Session

from dofus_touch_economy.models import UserAccount
from dofus_touch_economy.ownership import OWNER_ID


class AccountRepository:
    def __init__(self, session: Session):
        self._session = session

    def lock_registry(self) -> None:
        self._session.execute(text("BEGIN IMMEDIATE"))

    def get(self, account_id: str) -> UserAccount | None:
        return self._session.get(UserAccount, account_id)

    def by_subject(self, subject: str) -> UserAccount | None:
        return self._session.scalar(
            select(UserAccount).where(UserAccount.google_subject == subject)
        )

    def by_email(self, email: str) -> UserAccount | None:
        return self._session.scalar(select(UserAccount).where(UserAccount.email == email))

    def add(self, account: UserAccount) -> None:
        self._session.add(account)

    def requests(self) -> list[UserAccount]:
        return list(
            self._session.scalars(
                select(UserAccount)
                .where(UserAccount.id != OWNER_ID)
                .order_by(UserAccount.requested_at.desc(), UserAccount.id)
            )
        )

    def decide(self, account_id: str, status: str, decided_at: datetime) -> bool:
        return (
            self._session.execute(
                update(UserAccount)
                .where(UserAccount.id == account_id)
                .values(status=status, decided_at=decided_at)
            ).rowcount
            == 1
        )

    def claim_notification(self, account_id: str, now: datetime, retry_before: datetime) -> bool:
        return (
            self._session.execute(
                update(UserAccount)
                .where(
                    UserAccount.id == account_id,
                    UserAccount.status == "pending",
                    UserAccount.notification_sent_at.is_(None),
                    or_(
                        UserAccount.notification_attempted_at.is_(None),
                        UserAccount.notification_attempted_at < retry_before,
                    ),
                )
                .values(notification_attempted_at=now)
            ).rowcount
            == 1
        )

    def notification_sent(self, account_id: str, now: datetime) -> None:
        self._session.execute(
            update(UserAccount).where(UserAccount.id == account_id).values(notification_sent_at=now)
        )
