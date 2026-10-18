# Session Notes 2026-10-12

## Reconcile the two newest Slack sales screenshots

- The owner requested reading the two newest sales screenshots in Duchess Nikki's
  `#dofus-touch` channel and reconciling the project's local sales records. Applied
  `.agents/skills/dofus-sales-catch-up/SKILL.md` through its installed user-directory
  symlink and operational reference. The task-observer skill was unavailable.
- Read the latest channel message and its two attachments, `IMG_9547.png` and
  `IMG_9548.png`. Downloaded byte-identical evidence into ignored private storage,
  recorded SHA-256 hashes, and checked both prior manual audits and capture records
  to rule out replay. Visually transcribed 49 complete sale occurrences, preserving
  quantities, whole-kama lot totals, row order, and repeated identical sales.
  No complete scroll overlap was established; the clipped bottom fragment of the
  first screenshot was excluded rather than inferred. Enlarged Bliblycerin Tusk
  to confirm its exact spelling before matching.
- Fifteen quantity-one equipment notifications resolve uniquely within the approved
  Tailor/Shoemaker/Jeweller scope. All match existing asking prices, totaling
  695,000 kamas. Thirty-four resource notifications remain out of scope and unchanged;
  resource lots were not expanded and no missing listings were created.
- The committed October 11 audit establishes the prior coverage checkpoint. Used
  the October 12 Slack parent timestamp as the reporting-time proxy for this
  single-day interval, with `manual` source and no multi-day imputation. Exact
  individual sale times and derived timing metrics remain estimates. Reconstructed
  and verified the unchanged August 22–September 12 training baseline; did not
  extend it with estimated or incomplete observations.
- Created an integrity-checked online SQLite backup and rehearsed on an isolated
  database. Revalidated live table snapshots, evidence hashes, deterministic capture
  matches, and allocation under a write lock, then applied the batch atomically
  through SalesService. Before/after and saved-state checks prove exactly 15
  selected listings changed, no price observations appended, original listing
  starts and unrelated tables/history preserved, conserved revenue, and passing
  integrity/foreign-key checks. All 15 historical recipe costs are known. Counts
  moved from 786 sold/244 active to 801 sold/229 active, preserving the owner's
  independent stock additions since the earlier report.
- The committed private audit is
  `data/reports/manual-screenshot-sales-2026-10-12.json`; it includes evidence,
  transcript, allocation, original listing information, backup, rehearsal, and
  saved-state verification. Do not replay this batch. Slack attachments were
  retained, and no matching Downloads originals were present to clean up.
- Verification initially passed 60 of 61 focused Sales/capture/allocation tests.
  The unmodified repricing test failed because its observed timestamps contained
  both naive and UTC-aware representations of the same instant; its isolated
  rerun passed. No application or test source was changed for this operational
  reconciliation. The final focused rerun also passed 60 of 61 with the same
  repricing failure; the suite is not fully green. Saved-state reconciliation
  verification passed independently. Repository lint/formatting, private-driver
  checks, public-file policy, and `git diff --check` passed. Final Git status shows
  no private operational data, evidence, credentials, or observer files.
  The full application/dbt script is not needed for this operational-data and
  session-record update: no application algorithm, schema, or SQL changed.
- No staging, commits, pushes, Slack messages, BigQuery publication, Slack worker
  gate changes, or VPS cutover occurred. Existing pending hosting work remains
  intact; local SQLite is still authoritative. Private evidence, drivers, backups,
  and trial state remain ignored.

## Default sales skill to today's unprocessed Slack uploads

- The owner requested updating the sales skill to read today's uploads in
  `#dofus-touch` and recognize earlier reconciliation when invoked twice in one
  day. Used the skill-creator skill for this scoped instruction change.
- Updated `.agents/skills/dofus-sales-catch-up/SKILL.md` and its UI metadata to
  default to owner-uploaded images in Duchess Nikki's channel for the current
  Pacific date. Explicit supplied images, Downloads requests, or dates override
  that default. Added a linked Slack reference covering history pagination,
  exact message times, per-attachment progress, and unique run audit paths.
- Replay checks use provider file IDs and image hashes in committed audits and
  capture records. They recognize the already committed October 12 batch without
  migrating audits, skip identical-byte reuploads, and retain unresolved or newly
  attached images rather than relying only on a last-run timestamp. Mixed old/new
  attachments are handled individually; repeated sale names/prices remain valid
  occurrences unless visual overlap establishes prior processing.
- Same-day subsequent reports stay on that reporting date at the new message time
  with `manual` source. They bypass the existing next-day allocation helper rather
  than changing its interval contract or inventing a preceding day. Timing remains
  a reporting proxy. Slack originals are retained; Downloads cleanup and worker
  confirmation gates retain their existing scope.
- Verified skill frontmatter, linked reference, UI metadata, installed symlink,
  and compatibility of the existing committed audit's message/file/hash fields.
  Public-file policy and working-tree whitespace checks passed. No executable,
  application, schema, or SQL changes were made, so application/dbt suites were
  not repeated; the prior unrelated repricing-suite failure remains documented.
- No Sales writes or Slack mutations were performed for this skill update. No
  staging, commits, pushes, hosted publication, or changes to pending hosting work.

## Today's Crafting Items on Home

- The owner requested a seven-item crafting section between Today's To-Do tasks
  1 and 2. Confirmed two top Out of Stock starting items plus five recipes that
  reuse ingredients, zero active listings, positive estimated profit, and live
  recalculation. Used the existing Profit Opportunities profession defaults
  (Shoemaker/Jeweller/Tailor) and level-60 limit.
- Added an unnumbered section while preserving the existing daily task order,
  completion keys, weekly focus, and progress count. Rows show item/profession,
  selection reason, shared/new ingredient-type counts, current estimated profit,
  and existing Recipe Calculator Add/remove controls. Quantities use the existing
  cost-based defaults. Similarity counts refer to the original selection order
  even when users sort the table.
- Kept Out of Stock's profit-at-last-sale-price ranking for the first two eligible
  items. Selected subsequent recipes against the growing ingredient union,
  preferring actual overlap and then the fewest additional types, with current
  profit breaking ties. Real catalog item identities establish ingredient matches;
  incomplete prices/ingredients and catalog exclusions cannot enter the pool.
  The newest recipe version supplies the ingredients. Distinct eligible recipes
  fill remaining slots if restock or similar choices run out, and fewer than seven
  candidates produce a shorter list with an explicit count/empty state.
- Each Home request recomputes current eligibility; returning through browser Back
  reloads instead of restoring cached rows. No daily plan is frozen or persisted.
  The feature uses four bulk reads at most beyond the five existing snapshot
  queries, without per-row queries or historical cost reconstruction. SQL filters
  professions and required ingredient-slot levels before recipe materialization.
  This reduced the local full Home render sample from about 1.2 to 0.6 seconds.
- Added five synthetic behavioral tests for anchor ranking, seven distinct items,
  ingredient reuse after earlier additions, economic/scope/catalog exclusion,
  live stock and price changes, missing history, future sale handling, latest
  recipe versions, read-only Home rendering, calculator controls, and bounded
  query count. Updated the prior exact-five-query assertion to the new bounded
  count and checked the requested insertion point.
- Verification: full `./scripts/check.sh` passed 483 Python tests, lint/formatting,
  compilation, dbt debug/parse/seed, all 126 dbt build/test nodes, SQL lint, and
  public-file policy. The prior unrelated repricing failure did not recur in this
  full run. After the SQL filtering adjustment, all 51 focused Home/recipe/crafting
  tests passed again. Final repository lint/formatting, public-file policy, and
  working-tree whitespace checks passed; private artifacts remain ignored.
- Browser checks at 1440px and 390px passed seven-row rendering, no document-wide
  overflow, no JavaScript errors, cart add/remove with preserved quantities,
  calculator form submission, and unchanged checklist progression. Fixed the new
  table's mobile grid overflow with `min-width: 0` on Home panels; the table itself
  scrolls horizontally. The initial Chromium launch lacked a shared library;
  reused the existing cached Firefox runtime libraries without system changes.
  Private HTML, screenshots, browser driver/results, and check log remain under
  ignored `data/reports/`. Calculator POST was intercepted for browser validation
  rather than executed against operational state.
- The already-running local server retained the older Python route while loading
  updated templates, leaving the new section empty. Restarted only that identified
  project server gracefully, preserving its exact command, environment, and working
  directory. Verified the local Home URL now renders seven rows and all operational
  table contents are unchanged. The replacement loopback server remains running;
  its process and log are recorded in ignored
  `data/reports/home-crafting-local-server-2026-10-12.json` for future handoff.
- No operational Sales/price writes, staging, commits, pushes, BigQuery publication,
  Slack messages, or hosting cutover occurred. Prior pending hosting and skill
  changes were preserved.

## Move Today's Crafting Items into the Sales menu

- The owner requested moving the full crafting list from Home to a separate page
  under Sales. Added `/todays-crafting-items`, its alphabetized Sales submenu entry,
  active-menu state, and the standard wide layout. Moved the table into a standalone
  template with a page purpose, open collapsible Crafting Candidates section, and
  the same count, selection explanations, live economics, and calculator controls.
- Home keeps a short link between tasks 1 and 2 and returns to exactly five snapshot
  reads. Removed its recommendation calculation and recipe cart script. The
  selection service and all seven-item eligibility/ranking rules are unchanged.
  Table styles now use a page-specific class. Moved cached-page refresh behavior
  to a small crafting-page script; Home keeps its original checkbox restoration.
- Updated existing route/UI tests to cover the standalone page's read-only behavior,
  live eligibility, bounded four-query count, Sales navigation/active state, and
  calculator controls. Home tests verify five queries, the link's position, and no
  embedded crafting rows or cart script. All 127 focused Home/web/recipe/crafting
  tests passed. The previous full 483-test/126-node check remains applicable to the
  unchanged selection logic and warehouse; the full dbt sequence was not repeated
  for this route/template/navigation move.
- Browser, final lint/formatting, public-file, whitespace, and live server checks
  passed. Desktop/mobile checks covered navigating from the Home link, seven
  rows on the separate page, no document overflow or JavaScript errors, cart
  add/remove and quantity submission, and unchanged Home checklist progression.
  Restarted only the identified local project server with its existing command,
  environment, and working directory. Live HTTP checks confirm seven rows on the
  new page and zero embedded rows on Home, with all operational table contents
  preserved. The replacement loopback server remains running; its process/log
  checkpoint is `data/reports/crafting-page-local-server-2026-10-12.json`.
  Private browser artifacts remain under ignored `data/reports/`.
  No operational writes, staging, commits, pushes,
  cloud publication, Slack messages, or hosting cutover were requested or performed.

## Number Today's Crafting Items as task 2

- The owner requested making Today's Crafting Items the new second checklist task.
  Added it to HomeService's daily tasks with the stable `daily-crafting` key, its
  own checkbox, and the existing standalone-page link. Restocking, opportunities,
  and Dashboard are now tasks 3, 4, and 5. Weekly maintenance becomes task 6.
  Progress totals and weekly numbering derive from the task-list length; the
  existing task keys and saved checkmarks remain valid. Removed the superseded
  unnumbered Home block and its unused CSS.
- Updated existing Home tests for order, numbers, and five/six-task progress.
  All 91 focused Home/crafting/web tests passed, plus lint/formatting, public-file
  policy, and working-tree whitespace. Browser checks verify completing task 1
  advances Up next to Today's Crafting Items, its completion advances to restocking,
  and both checkmarks survive reload. Desktop/mobile rendering, navigation, and
  calculator controls continue to pass without JavaScript errors.
- Restarted only the local project server with its existing configuration. Live
  checks confirm task 2, renumbered later tasks, and six tasks on Monday; operational
  table contents are unchanged. The replacement server remains running, with its
  process/log in ignored `data/reports/crafting-task-local-server-2026-10-12.json`.
  Private browser verification artifacts remain ignored. The full dbt/application
  script was not repeated for this scoped checklist change; no selection algorithm,
  schema, SQL, or warehouse behavior changed. No operational writes, commits,
  pushes, cloud publication, Slack messages, or hosting cutover occurred.
