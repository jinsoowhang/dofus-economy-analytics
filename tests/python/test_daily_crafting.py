from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import event, func, select

from dofus_touch_economy.models import (
    ImportBatch,
    Item,
    PriceObservation,
    Recipe,
    RecipeIngredient,
    SaleListing,
    SourceRecord,
)
from dofus_touch_economy.services.recipes import RecipeCatalogService

AS_OF = datetime(2026, 10, 12, 20, tzinfo=UTC)
PROFESSIONS = ("Tailor", "Shoemaker", "Jeweller")


@pytest.fixture
def crafting_catalog(session):
    materials = {
        name: Item(display_name=name, normalized_name=name.lower(), identity_category="resource")
        for name in "ABCDEFGH"
    }
    batch = ImportBatch(
        dataset="synthetic_crafting",
        filename="synthetic.json",
        checksum="d" * 64,
        accepted_count=0,
        status="completed",
    )
    session.add_all([batch, *materials.values()])
    session.flush()
    for material in materials.values():
        if material.display_name != "H":
            session.add(
                PriceObservation(
                    item=material,
                    lot_quantity=1,
                    total_price=10,
                    observed_at=AS_OF - timedelta(days=2),
                    market_context="Dodge",
                    source="manual",
                )
            )
    row_number = 0

    def craft(
        name,
        ingredients,
        price=100,
        *,
        sold_price=None,
        active=False,
        profession="Tailor",
        excluded=False,
        sold_at=None,
    ):
        nonlocal row_number
        row_number += 1
        batch.accepted_count += 1
        item = Item(
            display_name=name,
            normalized_name=name.lower(),
            identity_category="hat",
            category="Hat",
            touch_catalog_status="excluded" if excluded else None,
        )
        recipe = Recipe(
            crafted_item=item,
            profession=profession,
            source_record=SourceRecord(
                import_batch=batch,
                row_number=row_number,
                raw_payload_json="{}",
                status="accepted",
            ),
        )
        recipe.ingredients = [
            RecipeIngredient(
                item=materials[name],
                raw_name=name,
                normalized_name=name.lower(),
                quantity=1,
                position=position,
            )
            for position, name in enumerate(ingredients, 1)
        ]
        session.add(recipe)
        if price is not None:
            session.add(
                PriceObservation(
                    item=item,
                    lot_quantity=1,
                    total_price=price,
                    observed_at=AS_OF - timedelta(days=1),
                    market_context="Dodge",
                    source="manual",
                )
            )
        if sold_price is not None:
            session.add(
                SaleListing(
                    item=item,
                    lot_quantity=1,
                    asking_price=sold_price,
                    selling_started_at=AS_OF - timedelta(days=5),
                    date_sold=sold_at or AS_OF - timedelta(days=1),
                )
            )
        if active:
            session.add(
                SaleListing(item=item, lot_quantity=1, asking_price=price, selling_started_at=AS_OF)
            )
        session.commit()
        return item

    return craft


def choices(session):
    return RecipeCatalogService(session, "Dodge").daily_crafting_items(
        professions=PROFESSIONS, maximum_level=60, as_of=AS_OF
    )


def test_daily_crafting_keeps_top_restock_anchors_and_minimizes_new_ingredients(
    session, crafting_catalog
):
    craft = crafting_catalog
    craft("Anchor One", "AB", 100, sold_price=1000)
    craft("Anchor Two", "BC", 90, sold_price=900)
    craft("Other Restock", "A", 40, sold_price=800)
    craft("Shared High Profit", "ABC", 200)
    craft("Shared Low Profit", "A", 15)
    craft("One New Ingredient", "AD", 50)
    craft("Uses Added Ingredient", "D", 100)
    craft("Unrelated High Profit", "F", 10000)

    result = choices(session)
    assert [choice.item.display_name for choice in result] == [
        "Anchor One",
        "Anchor Two",
        "Shared High Profit",
        "Other Restock",
        "Shared Low Profit",
        "One New Ingredient",
        "Uses Added Ingredient",
    ]
    assert [choice.is_anchor for choice in result] == [
        True,
        True,
        False,
        False,
        False,
        False,
        False,
    ]
    assert [choice.new_ingredient_count for choice in result[2:]] == [0, 0, 0, 1, 0]
    assert result[3].reason == "Shared ingredients · Out of stock"
    assert result[2].reason == "Shared ingredients · Profit opportunity"
    assert len({choice.item.item_uuid for choice in result}) == 7


def test_daily_crafting_excludes_stocked_loss_unknown_and_ineligible_recipes(
    session, crafting_catalog
):
    craft = crafting_catalog
    eligible = craft("Eligible", "A", sold_price=100)
    craft("Stocked", "A", active=True, sold_price=5000)
    craft("Break Even", "AB", 20, sold_price=5000)
    craft("Loss", "AB", 1, sold_price=5000)
    craft("Unknown Cost", "H", sold_price=5000)
    craft("Unknown Sale Price", "A", None)
    craft("Wrong Profession", "A", profession="Miner")
    craft("Level Too High", "ABCDEFG", sold_price=5000)
    craft("Excluded Item", "A", excluded=True, sold_price=5000)
    craft("Excluded Ingredient", "AG", sold_price=5000)
    material = session.scalar(select(Item).where(Item.normalized_name == "g"))
    material.touch_catalog_status = "excluded"
    session.commit()
    assert [choice.item.item_uuid for choice in choices(session)] == [eligible.uuid]


def test_daily_crafting_falls_back_to_profit_and_updates_after_stock_and_price_changes(
    session, crafting_catalog
):
    high = crafting_catalog("High Profit", "A", 100)
    crafting_catalog("Similar", "A", 30)
    unrelated = crafting_catalog("Unrelated", "B", 200)
    assert [choice.item.display_name for choice in choices(session)] == [
        "Unrelated",
        "High Profit",
        "Similar",
    ]
    session.add(
        SaleListing(
            item_id=unrelated.id, lot_quantity=1, asking_price=200, selling_started_at=AS_OF
        )
    )
    session.commit()
    assert [choice.item.display_name for choice in choices(session)] == ["High Profit", "Similar"]
    session.add(
        PriceObservation(
            item_id=high.id,
            lot_quantity=1,
            total_price=5,
            observed_at=AS_OF,
            market_context="Dodge",
            source="manual",
        )
    )
    session.commit()
    assert [choice.item.display_name for choice in choices(session)] == ["Similar"]


def test_daily_crafting_does_not_anchor_future_sales_or_use_old_recipe_ingredients(
    session, crafting_catalog
):
    first = crafting_catalog("Past Sale", "A", sold_price=100)
    future = crafting_catalog(
        "Future Sale", "B", sold_price=5000, sold_at=AS_OF + timedelta(days=1)
    )
    result = choices(session)
    assert result[0].item.item_uuid == first.uuid and result[0].is_anchor
    assert result[1].item.item_uuid == future.uuid and not result[1].is_anchor
    recipe = session.scalar(select(Recipe).where(Recipe.crafted_item_id == future.id))
    # A newer complete recipe version changes overlap; old ingredients must not accumulate.
    version = Recipe(
        crafted_item=future,
        profession="Tailor",
        source_record=SourceRecord(
            import_batch=recipe.source_record.import_batch,
            row_number=3,
            raw_payload_json="{}",
            status="accepted",
        ),
        ingredients=[
            RecipeIngredient(
                item_id=first.recipes[0].ingredients[0].item_id,
                raw_name="A",
                normalized_name="a",
                quantity=1,
                position=1,
            )
        ],
    )
    session.add(version)
    session.commit()
    result = choices(session)
    assert result[1].shared_ingredient_count == 1 and result[1].new_ingredient_count == 0


def test_crafting_page_renders_cart_read_only_and_refreshes_eligibility(
    client, session, session_factory, crafting_catalog
):
    item = crafting_catalog("Home Craft", "A", sold_price=100)
    before = {
        model: session.scalar(select(func.count()).select_from(model))
        for model in (SaleListing, PriceObservation)
    }
    statements = []
    engine = session_factory.kw["bind"]

    def capture(_connection, _cursor, statement, _parameters, _context, _many):
        statements.append(statement)

    event.listen(engine, "before_cursor_execute", capture)
    try:
        response = client.get("/todays-crafting-items")
    finally:
        event.remove(engine, "before_cursor_execute", capture)
    assert response.status_code == 200
    assert len(statements) <= 4
    assert all(statement.lstrip().upper().startswith("SELECT") for statement in statements)
    assert "<h1>Today's Crafting Items</h1>" in response.text
    assert 'class="site-submenu-link is-active"' in response.text
    assert 'class="page-shell page-shell--wide"' in response.text
    sales_menu = response.text.split('aria-label="Sales navigation"', 1)[1].split("</div>", 1)[0]
    assert sales_menu.index("Profit Opportunities") < sales_menu.index("Today's Crafting Items")
    assert 'href="/todays-crafting-items"' in sales_menu
    assert 'aria-current="page"' in sales_menu
    assert "Home Craft" in response.text and "Top out of stock" in response.text
    assert f'data-item-uuid="{item.uuid}" data-craft-quantity="5"' in response.text
    assert 'data-cart-toggle="true"' in response.text
    assert 'src="/static/recipe-cart.js"' in response.text
    assert response.headers["cache-control"] == "no-store"
    for model, count in before.items():
        assert session.scalar(select(func.count()).select_from(model)) == count
    session.add(
        SaleListing(item_id=item.id, lot_quantity=1, asking_price=100, selling_started_at=AS_OF)
    )
    session.commit()
    response = client.get("/todays-crafting-items")
    assert "Home Craft" not in response.text
    assert "No fully priced, profitable recipes" in response.text
