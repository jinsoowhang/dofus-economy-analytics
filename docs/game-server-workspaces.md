# Game and server workspaces

The website supports modern PC Dofus (Dofus 3, excluding Retro) on Tal Kasha and
Dofus Touch on Blair. Game and Server controls in the shared header apply to every
operational page and API. A browser cookie remembers the selected workspace for
one year. A tab's explicit `world` query parameter takes precedence over that cookie.
Forms also carry their original world, and HTMX/fetch requests carry the same
context, so switching in another tab cannot redirect an old form's write.
Unknown or conflicting explicit selections fail before a database mutation.

## Operational storage

| Selection | Database | Stored price market |
| --- | --- | --- |
| Dofus Touch / Blair | `DOFUS_APP_DATABASE_PATH` (existing default `data/app/dofus_touch.sqlite3`) | Existing `DOFUS_MARKET_CONTEXT`, preserved verbatim |
| Dofus / Tal Kasha | `DOFUS_PC_DATABASE_PATH`, or `dofus_tal_kasha.sqlite3` beside the Blair database | `Tal Kasha` |

These paths must differ. Both databases use the existing Alembic schema. A request
selects a session factory without changing application-wide settings. No existing
item UUID, observation, recipe, listing, or import provenance moves out of Blair.
The existing synthetic test market names and configurable legacy market identifiers
continue to work; the website displays the owner's server name Blair independently.

Today's Crafting Items and the initial Profit Opportunities filters use each
workspace's professions: Hunter, Jeweller, and Shoemaker on Tal Kasha; Shoemaker,
Jeweller, and Tailor on Blair. Explicit filters override these defaults. The full
recipe catalog remains available, and shopping lists use the imported ingredients
for the crafts selected in the calculator.

Calculator carts, calculation selections, pending Sales cleanup, checklist progress,
and table/scroll restoration use separate browser storage keys. Blair retains the
previous keys so existing browser state survives this change. Shared icon filenames
use item UUIDs, which are independent across the databases.

Separate databases deliberately duplicate catalogs if more servers are introduced.
This keeps the existing services, schema, and audit trails isolated without adding
game predicates to every operational query. Additional servers require an explicit
workspace definition and separate database; the selector does not accept arbitrary
database paths. Back up both database files and the separate icon cache. Existing
Touch imports, recipe/catalog sync commands, and screenshot reconciliation still
target Blair; a web selection never retargets a background worker or CLI process.

## Modern Dofus source research

Research date: October 17, 2026.

- [Dofusdude's main-channel releases](https://github.com/dofusdude/dofus3-main/releases)
  publish versioned client-derived assets produced with
  [Doduda](https://github.com/dofusdude/doduda). The initial import used release
  [3.7.11.11](https://github.com/dofusdude/dofus3-main/releases/tag/3.7.11.11).
  `MAPPED_ITEMS.json` provides English names, categories, IDs, pods, and icon IDs;
  raw `recipes.json`, `jobs.json`, and `en.json` supply recipe quantities and order,
  professions, and result levels from the same release. This is catalog data,
  not live market-price data.
- The [Dofusdude API](https://docs.dofusdu.de/dofus3/) also provides item, recipe,
  and icon endpoints. A pinned release was selected so related imports cannot
  mix multiple changing game versions or require thousands of per-item requests.
- [Astrub's Tal Kasha market](https://www.astrub.net/tal-kasha/prix-anciens)
  exposes community observations with dates and lot sizes. Research did not find a
  documented bulk export/API appropriate for this importer. No community prices
  were scraped or imported, and no companion/game-client integration was enabled.
- The [DofusDB API landing page](https://api.dofusdb.fr/) currently describes
  noncommercial, attribution/share-alike, and AI-related usage restrictions. It was
  not selected as the new PC catalog source. The existing Touch fallback code was
  outside this change.

Game data and artwork remain the property of their respective owners. Downloads,
normalized operational records, and icon caches remain ignored local artifacts;
no upstream game records are added to public fixtures.

## Importing and refreshing Dofus

```bash
uv run dofus-sync-pc
uv run dofus-sync-pc --benchmark-touch
# Reuse a previously downloaded release without fetching catalog JSON:
uv run dofus-sync-pc --source-directory data/raw/dofus_pc/3.7.11.11 --skip-icons
```

The command migrates only the PC database, resolves the latest release once, and
caches all required assets under that version in ignored `data/raw/dofus_pc/`.
It validates the source before catalog writes, then imports catalog rows and
recipes in one transaction. A content checksum makes an identical import a no-op;
changed releases append source/recipe provenance while preserving item UUIDs,
price observations, and Sales history.

PC item identity uses `identity_category = dofus:<Ankama ID>`, with the unmodified
English category kept separately for display. Distinct official same-name variants
remain distinct; recipes join exact official IDs. Equipment, consumable, resource,
and cosmetic categories are in scope; recipes involving out-of-scope IDs are
counted and skipped. Missing English identities are retained as rejected source
records with validation messages. Invalid quantities or inconsistent recipes abort
the import before catalog writes. Raw payloads preserve release and source fields.

The existing `touch_catalog_*` visibility columns retain their historical schema
names. In the independent PC database, they record PC release membership: present
official IDs are verified and IDs missing from a later release are excluded with
a PC-specific reason. Prior source rows and history remain available for audit.
Recipe profession requirements use explicit `requiredProfessionLevel` provenance
derived from the PC recipe's `resultLevel`, up to level 200. Touch continues to use
its existing ingredient-slot rule. Website filters and calculators use these same
requirements.

The icon archive comes from the same pinned release. Only matching regular PNG
members are read; archive paths are never extracted. Missing icons are reported
without blocking the catalog.

## Starting price benchmarks

`--benchmark-touch` reads the current valid Blair price for exact normalized names
with matching categories, requiring a unique name in both active catalogs. It
preserves lot quantity, lot total, original observation time, and source observation
UUID in the new record's note. Source is `touch_blair_benchmark`, and the PC market
is `Tal Kasha`. It creates no Sales listings and never copies Touch recipes.

Every Dofus page identifies possible Touch benchmarks and their effect on cost,
profit, and recommendations. Item detail identifies an active benchmark explicitly;
the API's current-price response includes its source. Unmatched items stay unpriced.
Entering a current Tal Kasha observation uses the existing append-only workflow.
The usual timestamp ordering still applies: a deliberately backdated observation
does not supersede a more recent benchmark. Re-running the seed never overwrites
an item with any existing PC price history, even invalidated history.

## Analytical publication

BigQuery Sync reads only the currently selected database. Blair retains its
existing dataset names; PC uses the same configured base names with
`_dofus_tal_kasha` appended, preventing one world's latest snapshot manifest from
replacing the other world's analytical source. Each workspace has its own process
local sync state. No cloud dataset was created by this local implementation.

The snapshot contract and dbt model graph are unchanged. To publish PC snapshots,
provision the separate datasets and grant the loader access, then configure a
separate dbt target/source dataset for that workspace. Existing hosted dbt jobs
remain Blair's jobs until explicitly configured otherwise. The CLI loader's default
is still Blair; preview PC explicitly with:

```bash
uv run dofus-load-bigquery --database-path data/app/dofus_tal_kasha.sqlite3 --dry-run
```
