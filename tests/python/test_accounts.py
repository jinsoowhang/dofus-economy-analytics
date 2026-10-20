from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, func, insert, select, update
from sqlalchemy.orm import aliased, joinedload, selectinload

from dofus_touch_economy.app import create_app
from dofus_touch_economy.models import Item, PriceObservation, SaleListing, UserAccount
from dofus_touch_economy.schemas import PriceObservationCreate, SaleListingCreate, SalePriceUpdate
from dofus_touch_economy.services.accounts import AccountConflict
from dofus_touch_economy.services.catalog import CatalogService
from dofus_touch_economy.services.pricing import ObservationConflict, PriceService
from dofus_touch_economy.services.sales import SaleListingNotFound, SalesService


@pytest.fixture
def accounts_app(app, session_factory):
    settings = replace(
        app.state.settings,
        accounts_enabled=True,
        owner_email="owner@example.test",
        public_origin="https://economy.example.test",
        allowed_hosts=("economy.example.test",),
    )
    result = create_app(settings=settings, session_factory=session_factory)
    result.state.accounts.notifier = MagicMock()
    return result


def headers(subject="owner-google-id", email="owner@example.test", **extra):
    return {
        "x-forwarded-user": subject,
        "x-forwarded-email": email,
        "origin": "https://economy.example.test",
        **extra,
    }


@pytest.fixture
def accounts_client(accounts_app):
    with TestClient(accounts_app, base_url="https://economy.example.test") as client:
        yield client


def test_pending_request_sends_once_and_is_approved_without_sales_visibility(
    accounts_app,
    accounts_client,
    session_factory,
    catalog_item,
):
    user = headers("alice-google-id", "alice@example.test")
    for _ in range(3):
        response = accounts_client.get("/", headers=user)
        assert response.status_code == 200
        assert "Invite request has been sent" in response.text
        assert "alice@example.test" in response.text
        assert 'href="/sales"' not in response.text
    assert accounts_app.state.accounts.notifier.call_count == 1
    assert accounts_client.get("/api/v1/items", headers=user).status_code == 403
    assert accounts_client.get("/static/app.css", headers=user).url.path == "/access-request"
    assert accounts_client.get("/openapi.json", headers=user).url.path == "/access-request"
    with session_factory() as session:
        row = session.scalar(select(UserAccount).where(UserAccount.email == "alice@example.test"))
        alice_id = row.id
        own_listing = SalesService(session, "Dodge").start(
            SaleListingCreate(item_uuid=catalog_item.uuid, asking_price=100)
        )
    # A pending user cannot approve themselves, including with a forged actor ID.
    assert (
        accounts_client.post(
            f"/admin/access-requests/{alice_id}/approve", headers=user, data={"account_id": "owner"}
        ).status_code
        == 403
    )
    response = accounts_client.get("/admin/access-requests", headers=headers())
    assert response.status_code == 200 and "alice@example.test" in response.text
    assert (
        accounts_client.post(
            f"/admin/access-requests/{alice_id}/approve",
            headers=headers(),
            data={"account_id": "owner"},
        ).status_code
        == 200
    )
    response = accounts_client.get("/", headers=user)
    assert response.status_code == 200 and "Invite request" not in response.text
    assert "Access requests" not in response.text
    assert "BigQuery Sync" not in response.text
    assert str(own_listing.uuid) not in accounts_client.get("/sales", headers=user).text
    assert accounts_client.get("/bigquery-sync", headers=user).status_code == 403
    assert accounts_client.get("/admin/access-requests", headers=user).status_code == 403
    # Known owner UUIDs do not allow another account to mark a listing sold.
    response = accounts_client.post(f"/sales/{own_listing.uuid}/sold", headers=user)
    assert response.status_code == 404
    with session_factory() as session:
        assert (
            session.scalar(
                select(SaleListing).where(SaleListing.uuid == own_listing.uuid)
            ).date_sold
            is None
        )
    accounts_client.post(
        f"/admin/access-requests/{alice_id}/deny", headers=headers(), data={"account_id": "owner"}
    )
    assert "Access has not been approved" in accounts_client.get("/", headers=user).text
    assert accounts_client.get("/api/v1/items", headers=user).status_code == 403


def test_missing_or_conflicting_identity_fails_closed(accounts_client):
    assert accounts_client.get("/").status_code == 401
    assert (
        accounts_client.get("/", headers={"x-forwarded-email": "owner@example.test"}).status_code
        == 401
    )
    assert accounts_client.get("/", headers=headers()).status_code == 200
    assert accounts_client.get("/", headers=headers("different-subject")).status_code == 403
    assert (
        accounts_client.get(
            "/", headers=headers(email="owner@example.test,other@example.test")
        ).status_code
        == 403
    )
    assert accounts_client.get("/healthz").json() == {"status": "ok"}


def test_stale_account_tab_cannot_submit_as_another_account(accounts_app, accounts_client):
    accounts_client.get("/", headers=headers())
    alice = accounts_app.state.accounts.identify("alice", "alice@example.test")
    accounts_app.state.accounts.decide(alice.id, "approved")
    response = accounts_client.post(
        "/api/v1/items",
        headers=headers("alice", "alice@example.test", **{"x-economy-account": "owner"}),
        json={"display_name": "Wrong Account Ore", "category": "Ore"},
    )
    assert response.status_code == 409
    response = accounts_client.post(
        "/items",
        headers=headers("alice", "alice@example.test"),
        data={"account_id": "owner", "display_name": "Wrong Account Ore"},
    )
    assert response.status_code == 409


def test_failed_mail_is_truthful_durable_and_throttled(
    accounts_app, accounts_client, session_factory
):
    notifier = accounts_app.state.accounts.notifier
    notifier.side_effect = OSError("SMTP unavailable")
    user = headers("alice", "alice@example.test")
    for _ in range(2):
        response = accounts_client.get("/", headers=user)
        assert "Your invite request has been saved" in response.text
        assert "Email notification is pending" in response.text
    assert notifier.call_count == 1
    with session_factory() as session:
        alice = session.scalar(select(UserAccount).where(UserAccount.email == "alice@example.test"))
        alice.notification_attempted_at = datetime.now(UTC) - timedelta(minutes=11)
        session.commit()
    notifier.side_effect = None
    assert "Invite request has been sent" in accounts_client.get("/", headers=user).text
    assert notifier.call_count == 2


def test_google_subject_stays_stable_and_email_cannot_claim_another_account(accounts_app):
    service = accounts_app.state.accounts
    alice = service.identify("alice", "alice@example.test")
    service.decide(alice.id, "approved")
    changed = service.identify("alice", "alice-new@example.test")
    assert changed.id == alice.id and changed.status == "approved"
    with pytest.raises(AccountConflict):
        service.identify("different-subject", "alice-new@example.test")
    with pytest.raises(AccountConflict):
        service.decide("owner", "denied")


def test_private_rows_are_scoped_in_aggregates_aliases_joins_and_bulk_commands(
    session_factory,
    catalog_item,
):
    with session_factory() as session:
        listing = SalesService(session, "Dodge").start(
            SaleListingCreate(item_uuid=catalog_item.uuid, asking_price=1234)
        )
    with session_factory(info={"owner_id": "alice", "is_admin": False}) as session:
        service = SalesService(session, "Dodge")
        assert service.active() == []
        assert session.scalar(select(func.count(SaleListing.id))) == 0
        alias = aliased(SaleListing)
        assert session.scalar(select(func.count(alias.id))) == 0
        subquery = select(SaleListing.id).subquery()
        assert session.scalar(select(func.count()).select_from(subquery)) == 0
        assert session.execute(select(Item.id, SaleListing.id).join(SaleListing)).all() == []
        assert service.active_counts_by_item() == {}
        assert CatalogService(session, "Dodge").detail(catalog_item.uuid).active_sale_count == 0
        assert (
            session.execute(
                update(SaleListing).where(SaleListing.uuid == listing.uuid).values(asking_price=1)
            ).rowcount
            == 0
        )
        session.commit()
        for action in [
            lambda: service.mark_sold(listing.uuid),
            lambda: service.update_price(listing.uuid, SalePriceUpdate(asking_price=1)),
            lambda: service.duplicate(listing.uuid),
            lambda: service.delete_active_many([listing.uuid]),
        ]:
            with pytest.raises(SaleListingNotFound):
                action()
        own = service.start(SaleListingCreate(item_uuid=catalog_item.uuid, asking_price=2000))
        assert [x.uuid for x in service.active()] == [own.uuid]
    with session_factory(info={"owner_id": "owner", "is_admin": True}) as session:
        assert [x.uuid for x in SalesService(session, "Dodge").active()] == [listing.uuid]
        assert session.scalar(select(func.count(SaleListing.id))) == 1


def test_shared_prices_hide_private_notes_and_contributors_cannot_invalidate_others(
    session_factory,
    catalog_item,
):
    with session_factory() as session:
        observation = PriceService(session, "Dodge").record(
            catalog_item.uuid,
            PriceObservationCreate(
                lot_quantity=1,
                total_price=100,
                observed_at=datetime.now(UTC),
                note="Private owner note",
            ),
        )
    with session_factory(info={"owner_id": "alice", "is_admin": False}) as session:
        prices = PriceService(session, "Dodge")
        assert prices.current_for_item(catalog_item.id).total_price == 100
        assert prices.history_for_item(catalog_item.id)[0].note is None
        with pytest.raises(ObservationConflict):
            prices.invalidate(observation.observation_uuid, "Not my contribution")
        own = prices.record(
            catalog_item.uuid,
            PriceObservationCreate(
                lot_quantity=1, total_price=200, observed_at=datetime.now(UTC), note="Alice note"
            ),
        )
        assert prices.history_for_item(catalog_item.id)[0].note == "Alice note"
        assert prices.invalidate(own.observation_uuid, "Mistyped").invalidated_at is not None
    with session_factory() as session:
        assert PriceService(session, "Dodge").current_for_item(catalog_item.id).total_price == 100


def test_new_listing_cannot_claim_someone_elses_owner(session_factory, catalog_item):
    with session_factory(info={"owner_id": "alice", "is_admin": False}) as session:
        session.add(
            SaleListing(owner_id="owner", item_id=catalog_item.id, asking_price=100, lot_quantity=1)
        )
        with pytest.raises(ValueError, match="another account"):
            session.commit()


def test_smtp_notification_contains_authenticated_review_link_only(accounts_app, tmp_path: Path):
    import json

    from dofus_touch_economy.services.accounts import send_invite_notification

    config = tmp_path / "smtp.json"
    config.write_text(
        json.dumps(
            {
                "host": "smtp.example.test",
                "username": "mailer",
                "password": "synthetic-password",
                "from_address": "mailer@example.test",
            }
        )
    )
    settings = replace(accounts_app.state.settings, invite_mail_config=config)
    account = accounts_app.state.accounts.identify("alice", "alice@example.test")
    with patch("dofus_touch_economy.services.accounts.smtplib.SMTP") as smtp:
        send_invite_notification(settings, account)
        connection = smtp.return_value.__enter__.return_value
        connection.starttls.assert_called_once()
        connection.login.assert_called_once_with("mailer", "synthetic-password")
        message = connection.send_message.call_args.args[0]
        assert message["To"] == "owner@example.test"
        assert "alice@example.test" in message.get_content()
        assert "https://economy.example.test/admin/access-requests" in message.get_content()
        assert "/approve" not in message.get_content()


def test_accounts_share_market_but_private_reports_and_world_preferences_are_separate(
    accounts_app,
    accounts_client,
    session_factory,
    catalog_item,
):
    from dofus_touch_economy.database import Base, create_engine_for_url, create_session_factory
    from dofus_touch_economy.models import PriceObservation
    from dofus_touch_economy.services.home import HomeService
    from dofus_touch_economy.worlds import WORLDS, world_settings

    service = accounts_app.state.accounts
    alice = service.identify("alice", "alice@example.test")
    service.decide(alice.id, "approved")
    user = headers("alice", "alice@example.test")
    pc_settings = world_settings(accounts_app.state.settings, WORLDS[1])
    pc_engine = create_engine_for_url(pc_settings.database_url)
    Base.metadata.create_all(pc_engine)
    pc_factory = create_session_factory(pc_engine)
    with pc_factory() as session:
        pc_item = Item(
            display_name="PC-only Ore",
            normalized_name="pc-only ore",
            category="Ore",
            identity_category="dofus:1",
        )
        session.add(pc_item)
        session.commit()
    for factory, item, market in [
        (session_factory, catalog_item, "Dodge"),
        (pc_factory, pc_item, "Tal Kasha"),
    ]:
        with factory() as session:
            listing = SalesService(session, market).start(
                SaleListingCreate(item_uuid=item.uuid, asking_price=900)
            )
            SalesService(session, market).mark_sold(listing.uuid)
        for path in ["/sales", "/dashboard", "/insights", "/best-sellers", "/out-of-stock-items"]:
            world = "touch-blair" if factory is session_factory else "dofus-tal-kasha"
            response = accounts_client.get(path, params={"world": world}, headers=user)
            assert response.status_code == 200
            assert str(listing.uuid) not in response.text
        with factory(info={"owner_id": alice.id, "is_admin": False}) as session:
            report = HomeService(session, display_timezone=UTC).report(as_of=datetime.now(UTC))
            assert report.snapshot.active_count == 0
            assert report.snapshot.sold_today == 0
            assert report.snapshot.revenue_today == 0
            assert PriceService(session, market).current_for_item(item.id).total_price == 900
            SalesService(session, market).start(
                SaleListingCreate(item_uuid=item.uuid, asking_price=1200)
            )
        with factory() as session:
            assert SalesService(session, market).active() == []
            assert len(SalesService(session, market).sold()) == 1
            assert PriceService(session, market).current_for_item(item.id).total_price == 1200
            assert session.scalar(select(func.count(PriceObservation.id))) == 3
    # The registry is central even for a first visit to the PC workspace.
    with pc_factory() as session:
        assert session.scalar(select(func.count(UserAccount.id))) == 0
    selected = accounts_client.get(
        "/select-world",
        headers=user,
        params={"game": "dofus", "server": "dofus-tal-kasha"},
        follow_redirects=False,
    )
    assert f"dofus_world_{alice.id}" in selected.headers["set-cookie"]
    assert 'data-world="touch-blair"' in accounts_client.get("/", headers=headers()).text
    page = accounts_client.get("/", headers=user).text
    assert f'data-account="{alice.id}"' in page
    pc_engine.dispose()


def test_private_owner_is_immutable_in_flush_and_bulk_updates(session_factory, catalog_item):
    with session_factory() as session:
        listing = SalesService(session, "Dodge").start(
            SaleListingCreate(item_uuid=catalog_item.uuid, asking_price=100)
        )
        with pytest.raises(ValueError, match="cannot be changed"):
            session.execute(update(SaleListing).values(owner_id="alice"))
        with pytest.raises(ValueError, match="cannot be changed"):
            session.execute(update(SaleListing).ordered_values((SaleListing.owner_id, "alice")))
        with pytest.raises(ValueError, match="cannot be changed"):
            session.execute(update(SaleListing), {"owner_id": "alice"})
        stored = session.scalar(select(SaleListing).where(SaleListing.uuid == listing.uuid))
        stored.owner_id = "alice"
        with pytest.raises(ValueError, match="another account|cannot be changed"):
            session.commit()


def test_ownership_cannot_be_bypassed_by_bulk_mapping_apis(session_factory, catalog_item):
    with session_factory() as session:
        listing = SalesService(session, "Dodge").start(
            SaleListingCreate(item_uuid=catalog_item.uuid, asking_price=100)
        )
        stored = session.scalar(select(SaleListing).where(SaleListing.uuid == listing.uuid))
        listing_id = stored.id
    with session_factory(info={"owner_id": "alice", "is_admin": False}) as session:
        for command in [
            lambda: session.bulk_update_mappings(
                SaleListing, [{"id": listing_id, "asking_price": 1}]
            ),
            lambda: session.bulk_insert_mappings(SaleListing, [{"owner_id": "owner"}]),
            lambda: session.bulk_save_objects([SaleListing(owner_id="owner")]),
            lambda: session.execute(insert(SaleListing), [{"owner_id": "owner"}]),
            lambda: session.execute(update(SaleListing), [{"id": listing_id, "owner_id": "alice"}]),
        ]:
            with pytest.raises(ValueError, match="ownership-validated"):
                command()
        assert (
            session.execute(delete(SaleListing).where(SaleListing.id == listing_id)).rowcount == 0
        )
        assert session.get(SaleListing, listing_id) is None
        session.commit()
    with session_factory() as session:
        assert session.get(SaleListing, listing_id).asking_price == 100


def test_price_contributor_cannot_be_transferred_and_daily_delete_checks_actor(
    session_factory, catalog_item
):
    observed_at = datetime.now(UTC)
    with session_factory() as session:
        owner = PriceService(session, "Dodge").record(
            catalog_item.uuid,
            PriceObservationCreate(lot_quantity=1, total_price=100, observed_at=observed_at),
        )
    with session_factory(info={"owner_id": "alice", "is_admin": False}) as session:
        prices = PriceService(session, "Dodge")
        own = prices.record(
            catalog_item.uuid,
            PriceObservationCreate(lot_quantity=1, total_price=100, observed_at=observed_at),
        )
        with pytest.raises(ObservationConflict):
            prices.invalidate_history_row(owner.observation_uuid, "Wrong contributor")
        with pytest.raises(ValueError, match="contributor cannot be changed"):
            session.execute(update(PriceObservation).values(contributor_id="owner"))
        assert prices.invalidate_history_row(own.observation_uuid, "Mistyped") == 1
    with session_factory() as session:
        assert PriceService(session, "Dodge").current_for_item(catalog_item.id) is not None
        assert (
            session.scalar(
                select(PriceObservation).where(PriceObservation.uuid == owner.observation_uuid)
            ).invalidated_at
            is None
        )


def test_account_pages_disable_shared_htmx_history(accounts_client):
    page = accounts_client.get("/sales", headers=headers())
    assert 'hx-history="false"' in page.text
    assert '"historyCacheSize":0' in page.text


def test_concurrent_first_visits_create_one_request_and_send_once(accounts_app, session_factory):
    with ThreadPoolExecutor(max_workers=4) as pool:
        accounts = list(
            pool.map(
                lambda _: accounts_app.state.accounts.identify("alice", "alice@example.test"),
                range(8),
            )
        )
    assert len({account.id for account in accounts}) == 1
    assert accounts_app.state.accounts.notifier.call_count == 1
    with session_factory() as session:
        assert session.scalar(select(func.count(UserAccount.id))) == 2


@pytest.mark.parametrize("loading", [None, joinedload, selectinload])
def test_shared_item_relationships_and_session_info_cannot_leak_private_listings(
    session_factory, catalog_item, loading
):
    with session_factory() as session:
        SalesService(session, "Dodge").start(
            SaleListingCreate(item_uuid=catalog_item.uuid, asking_price=100)
        )
    with session_factory(info={"owner_id": "alice", "is_admin": False}) as session:
        session.info["owner_id"] = "owner"
        assert session.owner_id == "alice"
        query = select(Item).where(Item.id == catalog_item.id)
        if loading:
            query = query.options(loading(Item.sale_listings))
        item = session.execute(query).unique().scalar_one()
        assert item.sale_listings == []
