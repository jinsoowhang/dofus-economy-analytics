# Session Notes 2026-10-17

## Modern Dofus and game/server selection

- The owner selected modern PC Dofus, excluding Retro, on Tal Kasha and identified
  the existing Touch server as Blair. Authorized researching PC data sources,
  applying the selection throughout the website, remembering the last choice,
  and using existing Touch prices as initial benchmarks if a suitable online price
  feed was unavailable. The owner will record Tal Kasha observations while playing.
- Success criteria: both linked selectors appear in the shared header; every page,
  API, write, report, cart, and checklist uses the selected workspace; old tabs
  cannot write across worlds; Blair's operational rows remain unchanged; PC gets
  its own current catalog/recipes with explicit source and benchmark provenance;
  focused, browser, and full project checks pass.
- Chose independent SQLite files with the existing schema instead of adding game
  predicates and migrations across every repository. This deliberately trades
  future per-server catalog duplication for a firm isolation boundary and minimal
  disturbance to existing audit/history semantics. No existing Blair UUID or
  stored market identifier was renamed. The new PC path is configurable and must
  differ from Blair's path.
- Added header Game/Server controls, a browser preference cookie, explicit tab
  URLs, hidden form scope, HTMX/fetch context, scoped redirects, and independent
  browser storage. Blair retains previous cart/checklist keys. Invalid/conflicting
  explicit scopes fail before writes. Updated branding to Dofus Economy.
- Researched Dofusdude's Dofus 3 API and versioned main-channel assets, current
  DofusDB API conditions, deprecated Datafus, and Astrub's community price pages.
  Selected a single pinned Dofusdude release, including mapped items, raw recipes,
  jobs, English translations, and icon archive. Research and source links live in
  `docs/game-server-workspaces.md`. No game-client actions or price scraping ran.
- Added `dofus-sync-pc`: PC-only migrations, source validation, transactional import,
  idempotent content checksum, append-only recipe/source versions, stable official
  ID item identities, current membership checks using legacy visibility columns,
  and safe per-member PNG caching. Missing English identities are explicitly
  rejected and retained. Recipes outside the supported market categories are
  counted and skipped. PC uses recipe result levels up to 200; Touch retains the
  existing ingredient-slot requirement rule.
- Imported release 3.7.11.11 into the ignored PC database: 13,469 items and 4,501
  recipes; 13,462 icons cached and seven unavailable. One internal test item has
  no English category and is retained as rejected provenance. Skipped 242 recipes
  whose result/ingredients are outside the supported market catalog.
- Seeded 700 optional exact, unique, category-matched Blair benchmarks, preserving
  original lot values/time and source UUID notes. Source is
  `touch_blair_benchmark`; every Dofus page explains estimates, and item detail/API
  expose benchmark provenance. Existing PC price history is never overwritten.
  Unmatched prices remain missing; no Sales rows or Touch recipes were copied.
- BigQuery Sync selects a workspace-specific controller/database and keeps PC
  targets separate through `_dofus_tal_kasha` dataset suffixes. No analytical schema
  migration or cloud publication was needed. A read-only PC snapshot dry run
  validates 17,971 source records, 37,326 source-name records, 23,857 ingredients,
  and 700 price observations against schema 0011. PC cloud/dbt configuration remains
  a separate explicit setup step; existing hosted jobs still serve Blair.
- Preserved all prior uncommitted hosting, crafting-page, and skill changes.
  Read-only hashes/counts across every Blair table match the pre-change baseline.
  PC integrity and foreign-key checks pass. Private research data and verification
  artifacts stay under ignored `data/raw/` and `data/reports/game-server-2026-10-17/`.
- Full `./scripts/check.sh` passed all 494 Python tests, lint/formatting, package
  compilation, dbt debug/parse/seed, all 126 dbt build/test nodes, SQL lint, and
  public-file policy. A final form-only Blair redirect correction passed another
  57 focused workspace, price-write, and hosting-security tests; final repository
  lint/formatting, public-file policy, and whitespace checks also pass.
- Browser checks passed linked selectors, preference persistence, separate carts,
  calculator POST context, stale-tab writes, HTMX search context, and no viewport
  overflow at 1440px/390px, with zero page errors. These used disposable synthetic
  databases and cached Chromium with Firefox's cached runtime libraries, without
  system package changes. Desktop/mobile screenshots remain ignored.
- All 14 selected-PC pages render against the actual imported catalog. The local
  loopback website is running at `http://127.0.0.1:8000`; the process/log checkpoint
  is ignored `data/reports/game-server-2026-10-17/local-server.json`. Only the
  server started during this session was restarted to load the final code.
- No staging, commits, pushes, Slack messages, cloud publication, or VPS cutover
  occurred. Existing pending deployment work remains intact.

## Dofus profession preferences

- The owner will play Hunter, Jeweller, and Shoemaker in modern Dofus. Moved
  crafting profession defaults into the workspace definition and applied them to
  Today's Crafting Items and the initial Profit Opportunities filters. Touch keeps
  its existing Shoemaker/Jeweller/Tailor defaults. Explicit filters still override
  the defaults; other professions remain available in the catalog/calculator.
- Success criteria: PC recommendations receive exactly the owner's three
  professions, Touch behavior stays intact, and manual filters still work.
  Read-only inspection confirmed all three professions are already imported,
  including 47 Hunter recipes. Recipe ingredient definitions, observations, and
  Sales data require no edits for this preference.
- Verification: all 91 focused workspace, daily-crafting, and web tests passed,
  including both games' service inputs/default filters and manual overrides.
  Repository lint/formatting, public-file policy, and whitespace checks passed.
  The full warehouse script was not repeated for this scoped default change;
  no schema, ingredient, SQL, ingestion, or warehouse behavior changed.
- Restarted only the identified project server with the same loopback command
  and verified both games' profession descriptions over live HTTP. Updated the
  existing ignored local-server checkpoint. No operational data writes, staging,
  commits, pushes, or external publication occurred.

## Publish pending project changes to GitHub

- The owner requested pushing changes to the remote. `main` and `origin/main`
  matched before publication. Reviewed all pending public files and separated the
  screenshot catch-up workflow, private hosting preparation, daily crafting page,
  and modern Dofus game/server support into independently verifiable commits.
- The full local check passes 496 Python tests and all 126 dbt build/test nodes,
  with lint/formatting, compilation, SQL lint, and public-file policy. Intermediate
  commit trees receive focused checks before committing. Secret scans cover the
  existing Git history, proposed public-file export, and outgoing commits.
- Only code, synthetic fixtures, public documentation, and session records are
  included. Both operational databases, game downloads, icons, screenshot evidence,
  credentials, and private publication reports remain ignored. Publishing source
  does not deploy the VPS, transfer live state, or publish analytical snapshots.
- Target is `origin/main` using a normal fast-forward push. Private verification
  and push confirmation stay in `data/reports/github-publication-2026-10-17/`.
