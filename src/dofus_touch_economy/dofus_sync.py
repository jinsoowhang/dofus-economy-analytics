"""Import one pinned, client-derived Dofus 3 release without market-price guesses."""

from __future__ import annotations

import hashlib
import json
import re
import tarfile
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from dofus_touch_economy.icon_fetcher import _fetch_json
from dofus_touch_economy.models import (
    ImportBatch,
    Item,
    PriceObservation,
    Recipe,
    RecipeIngredient,
    SourceItemName,
    SourceRecord,
)
from dofus_touch_economy.normalization import normalize_item_name
from dofus_touch_economy.repositories.prices import PriceRepository

RELEASE_URL = "https://api.github.com/repos/dofusdude/dofus3-main/releases/latest"
ASSETS = ("MAPPED_ITEMS.json", "recipes.json", "jobs.json", "en.json")
DATASET = "dofus_pc_release"
BENCHMARK_SOURCE = "touch_blair_benchmark"


@dataclass(frozen=True)
class DofusSyncSummary:
    version: str
    item_count: int
    recipe_count: int
    skipped_recipe_count: int
    created_batch: bool
    checksum: str
    rejected_item_count: int = 0


def download_release(directory: Path) -> Path:
    """Resolve latest once; every asset then comes from that same immutable tag."""
    release = _fetch_json(RELEASE_URL, None)
    version = release.get("tag_name")
    if not isinstance(version, str) or not version or any(c not in "0123456789." for c in version):
        raise ValueError("Invalid Dofus release version")
    target = directory / version
    target.mkdir(parents=True, exist_ok=True)
    assets = {asset["name"]: asset["browser_download_url"] for asset in release["assets"]}
    from urllib.request import Request, urlopen

    for name in ASSETS:
        expected = f"https://github.com/dofusdude/dofus3-main/releases/download/{version}/{name}"
        if assets.get(name) != expected:
            raise ValueError(f"Missing or unexpected release asset: {name}")
        path = target / name
        if path.is_file():
            continue
        request = Request(expected, headers={"User-Agent": "DofusEconomy/0.1"})
        with urlopen(request, timeout=120) as response:
            payload = response.read()
        json.loads(payload)
        temporary = path.with_suffix(".download")
        temporary.write_bytes(payload)
        temporary.replace(path)
    (target / "release.json").write_text(json.dumps(release), encoding="utf-8")
    return target


def _rows(payload: Any, class_name: str) -> list[dict[str, Any]]:
    references = payload["references"]["RefIds"]
    return [entry["data"] for entry in references if entry["type"]["class"] == class_name]


def sync_dofus_release(
    session_factory: sessionmaker[Session], source_directory: Path
) -> DofusSyncSummary:
    release = json.loads((source_directory / "release.json").read_bytes())
    version = release["tag_name"]
    payloads = {name: json.loads((source_directory / name).read_bytes()) for name in ASSETS}
    digest = hashlib.sha256()
    digest.update(str(version).encode())
    for name in ASSETS:
        digest.update(name.encode())
        digest.update((source_directory / name).read_bytes())
    checksum = digest.hexdigest()
    translations = payloads["en.json"]["entries"]
    jobs = {
        row["id"]: translations[str(row["nameId"])]
        for row in _rows(payloads["jobs.json"], "JobData")
    }
    # Only normal equipment, consumables, resources, and cosmetics. Quest and
    # hidden/system categories are intentionally outside this market catalog.
    candidates = [
        row for row in payloads["MAPPED_ITEMS.json"] if row["type"]["categoryId"] in (0, 1, 2, 5)
    ]
    by_id: dict[int, dict[str, Any]] = {}
    rejected_items: list[dict[str, Any]] = []
    for row in candidates:
        item_id = row["ankama_id"]
        name = row["name"].get("en")
        category = row["type"]["name"].get("en")
        if type(item_id) is not int or item_id <= 0 or item_id in by_id:
            raise ValueError("Invalid or duplicate Dofus item ID")
        if (
            not isinstance(name, str)
            or not name.strip()
            or not isinstance(category, str)
            or not category.strip()
        ):
            rejected_items.append(row)
            continue
        if type(row.get("pods")) is not int or row["pods"] < 0:
            raise ValueError(f"Invalid item weight: {item_id}")
        by_id[item_id] = row
    if not by_id:
        raise ValueError("Dofus release has no market items")

    recipes: list[dict[str, Any]] = []
    skipped = 0
    result_ids: set[int] = set()
    for row in _rows(payloads["recipes.json"], "RecipeData"):
        result_id = row["resultId"]
        if result_id not in by_id:
            skipped += 1
            continue
        ids, quantities = row["ingredientIds"]["Array"], row["quantities"]["Array"]
        if any(item_id not in by_id for item_id in ids):
            skipped += 1
            continue
        if result_id in result_ids or not 1 <= len(ids) <= 8 or len(ids) != len(quantities):
            raise ValueError(f"Invalid Dofus recipe ingredients: {result_id}")
        if any(type(quantity) is not int or quantity <= 0 for quantity in quantities):
            raise ValueError(f"Invalid Dofus recipe quantity: {result_id}")
        if (
            row["jobId"] not in jobs
            or type(row["resultLevel"]) is not int
            or not 1 <= row["resultLevel"] <= 200
        ):
            raise ValueError(f"Invalid Dofus recipe profession/level: {result_id}")
        result_ids.add(result_id)
        recipes.append(row)

    with session_factory() as session:
        if (
            session.scalar(
                select(ImportBatch.id).where(
                    ImportBatch.dataset == DATASET,
                    ImportBatch.checksum == checksum,
                    ImportBatch.status == "completed",
                )
            )
            is not None
        ):
            return DofusSyncSummary(
                version, len(by_id), len(recipes), skipped, False, checksum, len(rejected_items)
            )
        batch = ImportBatch(
            dataset=DATASET,
            filename=f"dofus3-{version}.json",
            checksum=checksum,
            accepted_count=len(by_id) + len(recipes),
            rejected_count=len(rejected_items),
            warning_count=skipped,
            status="started",
        )
        session.add(batch)
        existing = {item.identity_category: item for item in session.scalars(select(Item))}
        items: dict[int, Item] = {}
        checked_at = datetime.now(UTC)
        current_identities = {f"dofus:{item_id}" for item_id in by_id}
        for identity, item in existing.items():
            if identity.startswith("dofus:") and identity not in current_identities:
                item.touch_catalog_status = "excluded"
                item.touch_catalog_checked_at = checked_at
                item.touch_catalog_exclusion_reason = f"Absent from Dofus PC release {version}"
        row_number = 0
        for item_id, row in sorted(by_id.items()):
            # PC identities use authoritative IDs; same-name variants remain
            # distinct and never resolve ingredients by fuzzy or name-only joins.
            identity = f"dofus:{item_id}"
            item = existing.get(identity)
            if item is None:
                item = Item(identity_category=identity, created_source="imported")
                session.add(item)
            item.display_name = row["name"]["en"]
            item.normalized_name = normalize_item_name(item.display_name)
            item.category = row["type"]["name"]["en"]
            item.weight = row["pods"]
            # These legacy-named columns are the existing visibility contract;
            # inside this database they describe PC membership, never Touch.
            item.touch_catalog_status = "verified"
            item.touch_catalog_checked_at = checked_at
            item.touch_catalog_exclusion_reason = None
            row_number += 1
            record = SourceRecord(
                import_batch=batch,
                row_number=row_number,
                raw_payload_json=json.dumps({"release": version, "item": row}, ensure_ascii=False),
                status="accepted",
                validation_messages_json="[]",
            )
            record.source_item_names.append(
                SourceItemName(
                    source_field="item",
                    position=0,
                    raw_name=item.display_name,
                    normalized_name=item.normalized_name,
                    item=item,
                    resolution_status="matched",
                )
            )
            session.add(record)
            items[item_id] = item
        for row in recipes:
            row_number += 1
            # Preserve the original row; the explicit marker differentiates PC
            # level requirements from Touch's ingredient-slot display rule.
            record = SourceRecord(
                import_batch=batch,
                row_number=row_number,
                raw_payload_json=json.dumps(
                    {
                        "release": version,
                        "recipe": row,
                        "requiredProfessionLevel": row["resultLevel"],
                    },
                    ensure_ascii=False,
                ),
                status="accepted",
                validation_messages_json="[]",
            )
            recipe = Recipe(
                crafted_item=items[row["resultId"]],
                profession=jobs[row["jobId"]],
                source_record=record,
            )
            for position, (item_id, quantity) in enumerate(
                zip(
                    row["ingredientIds"]["Array"],
                    row["quantities"]["Array"],
                    strict=True,
                ),
                start=1,
            ):
                item = items[item_id]
                recipe.ingredients.append(
                    RecipeIngredient(
                        position=position,
                        item=item,
                        raw_name=item.display_name,
                        normalized_name=item.normalized_name,
                        quantity=quantity,
                    )
                )
                record.source_item_names.append(
                    SourceItemName(
                        source_field=f"ingredient_{position}",
                        position=position,
                        raw_name=item.display_name,
                        normalized_name=item.normalized_name,
                        item=item,
                        resolution_status="matched",
                    )
                )
            session.add(record)
        for row in rejected_items:
            row_number += 1
            session.add(
                SourceRecord(
                    import_batch=batch,
                    row_number=row_number,
                    raw_payload_json=json.dumps(
                        {"release": version, "item": row}, ensure_ascii=False
                    ),
                    status="rejected",
                    validation_messages_json=json.dumps(
                        ["Missing English item name or category; identity was not inferred"]
                    ),
                )
            )
        batch.status = "completed"
        batch.completed_at = datetime.now(UTC)
        session.commit()
    return DofusSyncSummary(
        version, len(by_id), len(recipes), skipped, True, checksum, len(rejected_items)
    )


def seed_touch_benchmarks(
    touch_factory: sessionmaker[Session],
    dofus_factory: sessionmaker[Session],
    touch_market: str,
) -> int:
    """One-time exact, unambiguous matches; never replace any PC price history."""
    with touch_factory() as session:
        items = list(
            session.scalars(
                select(Item).where(
                    Item.touch_catalog_status.is_distinct_from("excluded"),
                )
            )
        )
        counts = Counter(item.normalized_name for item in items)
        prices = {
            price.item_id: price
            for price in PriceRepository(session).latest_valid_for_market(touch_market)
        }
        by_name = {
            item.normalized_name: (item, prices[item.id])
            for item in items
            if counts[item.normalized_name] == 1 and item.id in prices
        }
    with dofus_factory() as session:
        pc_items = list(
            session.scalars(
                select(Item).where(
                    Item.touch_catalog_status.is_distinct_from("excluded"),
                )
            )
        )
        counts = Counter(item.normalized_name for item in pc_items)
        observed = set(session.scalars(select(PriceObservation.item_id).distinct()))
        created = 0
        for item in pc_items:
            match = by_name.get(item.normalized_name)
            if item.id in observed or counts[item.normalized_name] != 1 or match is None:
                continue
            source_item, source_price = match
            if normalize_item_name(item.category or "") != normalize_item_name(
                source_item.category or ""
            ):
                continue
            session.add(
                PriceObservation(
                    item_id=item.id,
                    lot_quantity=source_price.lot_quantity,
                    total_price=source_price.total_price,
                    observed_at=source_price.observed_at,
                    market_context="Tal Kasha",
                    source=BENCHMARK_SOURCE,
                    note=(
                        "Unverified Dofus Touch Blair benchmark; source observation "
                        f"{source_price.uuid}. Not a Tal Kasha observation."
                    ),
                )
            )
            created += 1
        session.commit()
    return created


def cache_dofus_icons(
    session_factory: sessionmaker[Session], source_directory: Path, icon_directory: Path
) -> tuple[int, int]:
    """Read PNG members individually; never extract archive paths to the filesystem."""
    from urllib.request import Request, urlopen

    from dofus_touch_economy.icon_fetcher import PNG_SIGNATURE

    release = json.loads((source_directory / "release.json").read_bytes())
    version = release["tag_name"]
    if not re.fullmatch(r"[0-9]+(?:\.[0-9]+)+", version):
        raise ValueError("Invalid Dofus release version")
    archive = source_directory / "items_images_64.tar.gz"
    if not archive.is_file():
        url = f"https://github.com/dofusdude/dofus3-main/releases/download/{version}/items_images_64.tar.gz"
        with urlopen(
            Request(url, headers={"User-Agent": "DofusEconomy/0.1"}), timeout=120
        ) as response:
            payload = response.read()
        temporary = archive.with_suffix(".download")
        temporary.write_bytes(payload)
        temporary.replace(archive)
    source_items = json.loads((source_directory / "MAPPED_ITEMS.json").read_bytes())
    icon_ids = {f"dofus:{item['ankama_id']}": item["iconId"] for item in source_items}
    with session_factory() as session:
        targets: dict[int, list[Item]] = defaultdict(list)
        for item in session.scalars(select(Item)):
            if item.identity_category in icon_ids:
                targets[icon_ids[item.identity_category]].append(item)
        icon_directory.mkdir(parents=True, exist_ok=True)
        cached: set[int] = set()
        with tarfile.open(archive, mode="r:gz") as images:
            for member in images:
                match = re.fullmatch(r"data/img/item/1x/(\d+)-64\.png", member.name)
                if match is None or not member.isfile() or member.size > 2_000_000:
                    continue
                icon_id = int(match.group(1))
                if icon_id not in targets:
                    continue
                stream = images.extractfile(member)
                if stream is None:
                    continue
                with stream:
                    payload = stream.read()
                if not payload.startswith(PNG_SIGNATURE):
                    raise ValueError(f"Invalid Dofus icon PNG: {icon_id}")
                for item in targets[icon_id]:
                    path = icon_directory / f"{item.uuid}.png"
                    if not path.is_file():
                        path.write_bytes(payload)
                    item.icon_source_url = (
                        f"https://api.dofusdu.de/dofus3/v1/img/item/{icon_id}-64.png"
                    )
                    cached.add(item.id)
        session.commit()
        return len(cached), sum(map(len, targets.values())) - len(cached)
