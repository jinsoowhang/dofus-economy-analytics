import json
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import func, select

from dofus_touch_economy.database import Base, create_engine_for_url, create_session_factory
from dofus_touch_economy.dofus_sync import (
    BENCHMARK_SOURCE,
    seed_touch_benchmarks,
    sync_dofus_release,
)
from dofus_touch_economy.models import ImportBatch, Item, PriceObservation, Recipe, SaleListing
from dofus_touch_economy.schemas import ItemCreate, PriceObservationCreate
from dofus_touch_economy.services.catalog import CatalogItemConflict, CatalogService
from dofus_touch_economy.services.pricing import PriceService
from dofus_touch_economy.services.recipes import RecipeCatalogService


@pytest.fixture
def pc_release(tmp_path):
    directory = tmp_path / "release"
    directory.mkdir()

    def unity(class_name, rows):
        return {
            "references": {"RefIds": [{"type": {"class": class_name}, "data": row} for row in rows]}
        }

    payloads = {
        "release.json": {"tag_name": "3.0.0.0"},
        "MAPPED_ITEMS.json": [
            {
                "ankama_id": item_id,
                "name": {"en": name},
                "type": {
                    "categoryId": 2 if item_id == 1 else 0,
                    "name": {"en": "Ore" if item_id == 1 else "Ring"},
                },
                "pods": 2,
                "iconId": item_id,
            }
            for item_id, name in [
                (1, "Synthetic Ore"),
                (2, "Synthetic Ring"),
                (3, "Synthetic Ring"),
            ]
        ],
        "recipes.json": unity(
            "RecipeData",
            [
                {
                    "resultId": 2,
                    "ingredientIds": {"Array": [1]},
                    "quantities": {"Array": [3]},
                    "jobId": 1,
                    "resultLevel": 150,
                }
            ],
        ),
        "jobs.json": unity("JobData", [{"id": 1, "nameId": 42}]),
        "en.json": {"entries": {"42": "Jeweller"}},
    }
    for name, data in payloads.items():
        (directory / name).write_text(json.dumps(data))
    return directory


def test_pc_import_uses_ids_and_own_recipes_preserves_history_and_is_idempotent(
    session_factory, pc_release
):
    first = sync_dofus_release(session_factory, pc_release)
    assert (first.item_count, first.recipe_count, first.created_batch) == (3, 1, True)
    assert sync_dofus_release(session_factory, pc_release).created_batch is False
    with session_factory() as session:
        assert session.scalar(select(func.count()).select_from(Item)) == 3
        rings = list(session.scalars(select(Item).where(Item.display_name == "Synthetic Ring")))
        assert len({item.uuid for item in rings}) == 2
        recipe = session.scalar(select(Recipe))
        assert recipe.crafted_item.identity_category == "dofus:2"
        assert recipe.ingredients[0].item.identity_category == "dofus:1"
        assert recipe.ingredients[0].quantity == 3
        detail = CatalogService(session, "Tal Kasha").detail(recipe.crafted_item.uuid)
        assert detail.recipe.profession == "Jeweller"
        assert detail.recipe.profession_level == 150
        rows = RecipeCatalogService(session, "Tal Kasha").browse()
        assert rows.rows[0].profession_level == 150
        with pytest.raises(CatalogItemConflict):
            CatalogService(session, "Tal Kasha").create_manual(
                ItemCreate(display_name="Synthetic Ring", category="Ring")
            )
        original_uuid = recipe.crafted_item.uuid
        PriceService(session, "Tal Kasha").record(
            original_uuid,
            PriceObservationCreate(lot_quantity=1, total_price=900, observed_at=datetime.now(UTC)),
        )
    path = pc_release / "recipes.json"
    changed = json.loads(path.read_text())
    changed["references"]["RefIds"][0]["data"]["quantities"]["Array"] = [4]
    path.write_text(json.dumps(changed))
    assert sync_dofus_release(session_factory, pc_release).created_batch is True
    with session_factory() as session:
        assert session.scalar(select(func.count()).select_from(Recipe)) == 2
        assert (
            session.scalar(select(Item.uuid).where(Item.identity_category == "dofus:2"))
            == original_uuid
        )
        assert (
            CatalogService(session, "Tal Kasha").detail(original_uuid).current_price.total_price
            == 900
        )
        assert session.scalar(select(SaleListing)) is None


def test_invalid_recipe_aborts_before_any_catalog_writes(session_factory, pc_release):
    path = pc_release / "recipes.json"
    data = json.loads(path.read_text())
    data["references"]["RefIds"][0]["data"]["quantities"]["Array"] = [-1]
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="quantity"):
        sync_dofus_release(session_factory, pc_release)
    with session_factory() as session:
        assert session.scalar(select(ImportBatch)) is None
        assert session.scalar(select(Item)) is None


def test_benchmarks_are_labeled_idempotent_and_never_override_pc_observations(
    session_factory, catalog_item, pc_release, tmp_path
):
    pc_engine = create_engine_for_url(f"sqlite+pysqlite:///{tmp_path / 'pc.sqlite3'}")
    Base.metadata.create_all(pc_engine)
    pc_factory = create_session_factory(pc_engine)
    try:
        sync_dofus_release(pc_factory, pc_release)
        with session_factory() as session:
            PriceService(session, "Dodge").record(
                catalog_item.uuid,
                PriceObservationCreate(
                    lot_quantity=10,
                    total_price=300,
                    observed_at=datetime.now(UTC) - timedelta(days=1),
                ),
            )
        assert seed_touch_benchmarks(session_factory, pc_factory, "Dodge") == 1
        assert seed_touch_benchmarks(session_factory, pc_factory, "Dodge") == 0
        with pc_factory() as session:
            item = session.scalar(select(Item).where(Item.identity_category == "dofus:1"))
            benchmark = PriceService(session, "Tal Kasha").current_for_item(item.id)
            assert benchmark.source == BENCHMARK_SOURCE
            assert benchmark.unit_price == 30
            assert benchmark.lot_quantity == 10
            PriceService(session, "Tal Kasha").record(
                item.uuid,
                PriceObservationCreate(
                    lot_quantity=1, total_price=45, observed_at=datetime.now(UTC)
                ),
            )
            assert PriceService(session, "Tal Kasha").current_for_item(item.id).source == "manual"
        assert seed_touch_benchmarks(session_factory, pc_factory, "Dodge") == 0
        with session_factory() as session:
            assert session.scalar(select(func.count()).select_from(PriceObservation)) == 1
    finally:
        pc_engine.dispose()
