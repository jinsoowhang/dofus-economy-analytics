from dataclasses import replace
from datetime import UTC, datetime
from urllib.parse import parse_qs, urlsplit

import pytest
from sqlalchemy import func, select

from dofus_touch_economy.database import Base, create_engine_for_url, create_session_factory
from dofus_touch_economy.models import Item, PriceObservation, SaleListing
from dofus_touch_economy.services.recipes import RecipeCatalogService
from dofus_touch_economy.worlds import WORLD_COOKIE, WORLDS, validate_world_paths, world_settings


@pytest.fixture
def pc_catalog(app):
    settings = world_settings(app.state.settings, WORLDS[1])
    engine = create_engine_for_url(settings.database_url)
    Base.metadata.create_all(engine)
    factory = create_session_factory(engine)
    with factory() as session:
        item = Item(
            display_name="PC Ore",
            normalized_name="pc ore",
            category="Ore",
            identity_category="dofus:1",
        )
        session.add(item)
        session.flush()
        session.add(
            PriceObservation(
                item_id=item.id,
                lot_quantity=1,
                total_price=700,
                observed_at=datetime.now(UTC),
                market_context="Tal Kasha",
            )
        )
        session.add(SaleListing(item_id=item.id, lot_quantity=1, asking_price=900))
        session.commit()
    yield factory, item
    engine.dispose()


def test_selector_remembers_selection_and_all_pages_use_pc(client, catalog_item, pc_catalog):
    selected = client.get(
        "/select-world",
        params={"game": "dofus", "server": "dofus-tal-kasha"},
        follow_redirects=False,
    )
    assert selected.status_code == 303
    assert client.cookies[WORLD_COOKIE] == "dofus-tal-kasha"
    assert "HttpOnly" in selected.headers["set-cookie"]
    assert parse_qs(urlsplit(selected.headers["location"]).query)["world"] == ["dofus-tal-kasha"]
    for path in [
        "/",
        "/items",
        "/recipes",
        "/recipe-calculator",
        "/sales",
        "/dashboard",
        "/insights",
        "/price-priorities",
        "/sales/price-review",
        "/best-sellers",
        "/out-of-stock-items",
        "/profit-opportunities",
        "/todays-crafting-items",
        "/bigquery-sync",
    ]:
        page = client.get(path)
        assert page.status_code == 200, (path, page.text[:500])
        assert 'data-world="dofus-tal-kasha"' in page.text
        assert "not observed Tal Kasha prices" in page.text
        assert "Synthetic Ore" not in page.text
    results = client.get("/api/v1/items").json()
    assert [item["display_name"] for item in results] == ["PC Ore"]
    assert results[0]["current_price"]["total_price"] == 700
    assert (
        client.get("/api/v1/items", params={"world": "touch-blair"}).json()[0]["display_name"]
        == "Synthetic Ore"
    )


def test_stale_tab_forms_and_api_writes_cannot_cross_worlds(
    client, session_factory, catalog_item, pc_catalog
):
    factory, item = pc_catalog
    client.cookies.set(WORLD_COOKIE, "touch-blair")
    response = client.post(
        f"/items/{item.uuid}/price",
        data={"current_price": "880", "world": "dofus-tal-kasha"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert "world=dofus-tal-kasha" in response.headers["location"]
    with factory() as session:
        prices = list(session.scalars(select(PriceObservation).order_by(PriceObservation.id)))
        assert [price.total_price for price in prices] == [700, 880]
    with session_factory() as session:
        assert session.scalar(select(func.count()).select_from(PriceObservation)) == 0
    blocked = client.post(
        f"/api/v1/items/{catalog_item.uuid}/price-observations",
        headers={"X-Economy-World": "dofus-tal-kasha"},
        json={"lot_quantity": 1, "total_price": 999, "observed_at": datetime.now(UTC).isoformat()},
    )
    assert blocked.status_code == 404
    assert client.get(f"/api/v1/items/{item.uuid}?world=touch-blair").status_code == 404
    # A form-only Blair selection must also survive the redirect when another
    # tab has changed the remembered preference to PC (including without JS).
    client.cookies.set(WORLD_COOKIE, "dofus-tal-kasha")
    reverse = client.post(
        f"/items/{catalog_item.uuid}/price",
        data={"current_price": "77", "world": "touch-blair"},
        follow_redirects=False,
    )
    assert reverse.status_code == 303
    assert "world=touch-blair" in reverse.headers["location"]
    assert client.get(reverse.headers["location"]).status_code == 200


@pytest.mark.parametrize(
    "query,headers",
    [
        ("world=unknown", {}),
        ("world=touch-blair&world=dofus-tal-kasha", {}),
        ("world=touch-blair", {"X-Economy-World": "dofus-tal-kasha"}),
    ],
)
def test_invalid_and_conflicting_worlds_are_rejected(client, query, headers):
    assert client.get(f"/items?{query}", headers=headers).status_code == 400


def test_conflicting_form_is_rejected_before_writes(client, pc_catalog):
    _, item = pc_catalog
    response = client.post(
        f"/items/{item.uuid}/price?world=touch-blair",
        data={"current_price": "999", "world": "dofus-tal-kasha"},
    )
    assert response.status_code == 400


def test_bad_cookie_recovers_and_invalid_game_server_is_rejected(client):
    client.cookies.set(WORLD_COOKIE, "obsolete")
    assert client.get("/").headers["X-Economy-World"] == "touch-blair"
    assert client.get("/select-world?game=dofus&server=touch-blair").status_code == 400
    assert client.get("/items?world=dofus-tal-kasha").status_code == 503


def test_world_databases_and_bigquery_targets_are_distinct(app):
    settings = app.state.settings
    pc = world_settings(settings, WORLDS[1])
    assert pc.database_path != settings.database_path
    assert set(pc.bigquery_datasets).isdisjoint(settings.bigquery_datasets)
    assert (
        app.state.world_sync_managers[WORLDS[0].key]
        is not app.state.world_sync_managers[WORLDS[1].key]
    )
    with pytest.raises(ValueError, match="different paths"):
        validate_world_paths(replace(settings, dofus_database_path=settings.database_path))


@pytest.mark.parametrize(
    "world,expected",
    [
        ("touch-blair", ("Shoemaker", "Jeweller", "Tailor")),
        ("dofus-tal-kasha", ("Hunter", "Jeweller", "Shoemaker")),
    ],
)
def test_crafting_defaults_follow_world_and_allow_explicit_filters(
    client, pc_catalog, monkeypatch, world, expected
):
    calls = []
    original = RecipeCatalogService.daily_crafting_items

    def daily_crafting_items(service, **kwargs):
        calls.append(kwargs["professions"])
        return original(service, **kwargs)

    monkeypatch.setattr(RecipeCatalogService, "daily_crafting_items", daily_crafting_items)
    daily = client.get("/todays-crafting-items", params={"world": world})
    assert daily.status_code == 200
    assert ", ".join(expected) in daily.text
    assert calls == [expected]
    opportunities = client.get("/profit-opportunities", params={"world": world})
    assert opportunities.status_code == 200
    for profession in expected:
        assert f'name="profession" value="{profession}" checked' in opportunities.text
    override = client.get("/profit-opportunities", params={"world": world, "profession": "Tailor"})
    assert 'name="profession" value="Tailor" checked' in override.text
    assert 'name="profession" value="Jeweller" checked' not in override.text
