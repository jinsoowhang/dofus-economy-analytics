"""Enforce private row ownership across existing projections and commands.

Web sessions always carry the approved account's scope. Local commands default to
the original owner. Core connections/raw SQLite are trusted maintenance interfaces
and must never be exposed through request parameters or a web session.
"""

from sqlalchemy import event, inspect
from sqlalchemy.orm import Session, with_loader_criteria

OWNER_ID = "owner"


def _updates_identity(state, column_name):
    keys = list(state.statement._values or {})
    keys.extend(key for key, _value in state.statement._ordered_values or ())
    if isinstance(state.parameters, dict):
        keys.extend(state.parameters)
    return any(getattr(key, "key", key) == column_name for key in keys)


class EconomySession(Session):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._owner_id = self.info.get("owner_id", OWNER_ID)
        self._is_admin = self.info.get("is_admin", self._owner_id == OWNER_ID)
        if not self.owner_id:
            raise ValueError("An economy session requires an owner")

    @property
    def owner_id(self):
        return self._owner_id

    @property
    def is_admin(self):
        return self._is_admin

    # These legacy APIs skip both ORM statement events and flush validation.
    # Economy writes must use add()/flush() or scoped ORM update/delete statements.
    def bulk_save_objects(self, *args, **kwargs):
        raise ValueError("Use ownership-validated ORM flushes for economy writes")

    def bulk_insert_mappings(self, *args, **kwargs):
        raise ValueError("Use ownership-validated ORM flushes for economy writes")

    def bulk_update_mappings(self, *args, **kwargs):
        raise ValueError("Use ownership-validated ORM flushes for economy writes")


@event.listens_for(EconomySession, "do_orm_execute")
def _scope_private_statements(state):
    from dofus_touch_economy.models import PriceObservation, PrivatelyOwned

    owner_id = state.session.owner_id
    model = state.bind_mapper.class_ if state.bind_mapper is not None else None
    if (
        state.is_insert
        and model is not None
        and (issubclass(model, PrivatelyOwned) or model is PriceObservation)
    ):
        raise ValueError("Use ownership-validated ORM flushes for economy inserts")
    if state.is_select or state.is_update or state.is_delete:
        state.statement = state.statement.options(
            with_loader_criteria(
                PrivatelyOwned, lambda row: row.owner_id == owner_id, include_aliases=True
            )
        )
    if (state.is_update or state.is_delete) and state.bind_mapper is not None:
        model = state.bind_mapper.class_
        if state.is_executemany and (
            issubclass(model, PrivatelyOwned) or model is PriceObservation
        ):
            raise ValueError("Use ownership-validated ORM flushes for bulk economy writes")
        if issubclass(model, PrivatelyOwned):
            state.statement = state.statement.where(model.owner_id == owner_id)
            if state.is_update and _updates_identity(state, "owner_id"):
                raise ValueError("Listing ownership cannot be changed")
        if model is PriceObservation and not state.session.is_admin:
            state.statement = state.statement.where(PriceObservation.contributor_id == owner_id)
        if (
            model is PriceObservation
            and state.is_update
            and _updates_identity(state, "contributor_id")
        ):
            raise ValueError("Price contributor cannot be changed")


@event.listens_for(EconomySession, "before_flush")
def _guard_private_objects(session, _context, _instances):
    from dofus_touch_economy.models import PriceObservation, PrivatelyOwned

    for obj in session.new | session.dirty | session.deleted:
        if isinstance(obj, PrivatelyOwned):
            if obj in session.new and obj.owner_id is None:
                obj.owner_id = session.owner_id
            if obj.owner_id != session.owner_id:
                raise ValueError("Private record belongs to another account")
            if obj not in session.new and inspect(obj).attrs.owner_id.history.has_changes():
                raise ValueError("Listing ownership cannot be changed")
        if isinstance(obj, PriceObservation):
            if obj in session.new:
                if obj.contributor_id not in (None, session.owner_id):
                    raise ValueError("Price contributor does not match the account")
                obj.contributor_id = session.owner_id
            elif inspect(obj).attrs.contributor_id.history.has_changes() or (
                not session.is_admin and obj.contributor_id != session.owner_id
            ):
                raise ValueError("Price contribution belongs to another account")
