# Session Notes 2026-10-18

## Rename the project

- The owner requested `dofus-economy-analytics` locally and on GitHub. Success
  criteria: the new repository URL resolves, `origin` targets it, the local project
  opens under the new directory, active links and distribution metadata agree,
  existing commands work, and scoped changes pass project verification.
- Renamed GitHub to `jinsoowhang/dofus-economy-analytics`, updated `origin`, and
  expanded the repository/distribution description to cover Dofus and Dofus Touch.
  Updated public source links, clone instructions, and the suggested VPS checkout
  path. Regenerated the lockfile with `uv`; dependency versions are unchanged.
- Kept the Python import package, CLI commands, dbt project/profile and macro
  namespace, operational paths, and hosted configuration stable. Historical design
  documents/session records retain their original names. No deployment, warehouse
  publication, or operational data changes are part of this rename.
- Windows refused both Linux and native directory renames because nested
  directories were in use. Moved all contents into the new project path, splitting
  locked directories as necessary. Verified the original tree contains only empty
  directory shells, and both operational SQLite files retain their size and
  modification time. Preserved ignored local state and the old private worktree.
  Updated the existing installed catch-up skill symlink to the new checkout.
- The full `./scripts/check.sh` passed before relocation: 496 Python tests, lint
  and formatting, compilation, dbt debug/parse/seed, all 126 dbt build/test nodes,
  SQL lint, and public-file policy. Recreated the root virtual environment with
  `uv` from the unchanged locked dependencies to refresh absolute console-script
  paths after relocation.
- From the renamed checkout, all 24 package/static-asset tests pass, the direct
  `dofus-web --help` entry point works, and distribution metadata, imports, and
  every project console-script interpreter path resolve correctly. dbt parse,
  public-file policy, and whitespace checks pass again. GitHub metadata and
  `git ls-remote origin HEAD` confirm the new repository name and remote access.
- Publish the naming changes and session record as one atomic commit on `main`.
  The only remaining cleanup is removing Windows-locked empty directories at the
  old checkout path after the application holding them closes.

## Clean up obsolete folder locations

- The owner requested removing confusion from multiple economy analytics folders.
  The canonical checkout is `Project/Games/dofus-economy-analytics`.
- Verified the old root folder had no files or nested links; removed its empty
  directories and the obsolete Games junction. Updated the workspace project
  index and memory, and renamed/repaired the Windows `Dofus Economy.lnk` shortcut.
- Repaired the installed screenshot catch-up skill symlink and the existing
  private feature worktree's Git links after relocation. The feature worktree is
  clean and preserved. Historical session records retain their original paths.
- Confirmed both operational SQLite files retain their pre-cleanup size and
  modification time. No application source, dependency versions, or data changed.
- Recreated the root virtual environment with Python 3.12 and
  `uv sync --locked --all-groups`. Package imports and every project console
  script now resolve through the canonical Games location. All 24 package and
  static-asset tests pass; the direct web entry point, dbt parse, public-file
  policy, and whitespace checks pass. The full application/dbt build suite was not repeated
  because this cleanup changes only navigation, environment paths, and records.

## Reconcile yesterday's Touch sales from Slack

- The owner requested updating Sales from October 17 screenshots in `#dofus-touch`.
  Used `.agents/skills/dofus-sales-catch-up/SKILL.md` (also installed at
  `/home/jwhang/.codex/skills/dofus-sales-catch-up/SKILL.md`). Task-observer was not
  available in the active skill catalog; no observer logs were generated.
- Success criteria: inspect every eligible attachment and thread, skip previously
  reconciled evidence, preserve repeated complete sales, resolve exact active
  listings within Tailor/Shoemaker/Jeweller, retain actual prices, allocate from the
  last verified report, rehearse before one atomic write, and verify saved state.
- Found one owner message with two images and no thread replies. Archived and
  hashed both attachments privately. Neither appears in earlier manual audits or
  capture-file records. Channel history contains no uploads between the last
  committed October 12 checkpoint and this report.
- Visually ordered the login/start screen before its continuation. Removed two
  established scroll-overlap rows, preserving all other repeated notifications.
  Matched 26 existing quantity-one equipment listings for 1,455,000 kamas; no price
  corrections or unreadable/clipped sales. Twelve resource occurrences remain
  reviewed exclusions, unchanged.
- Kept the previously approved complete August 22–September 12 weekday baseline;
  reconstructed non-estimated SQLite counts exactly match the previous audit.
  Allocated October 13–17 as 5/5/6/4/6 sales, with revenue respectively
  196,000/215,000/244,000/355,000/445,000 kamas. Individual dates and times, and
  resulting daily profit/timing metrics, are estimates. Small sample size and
  inventory changes limit the allocation; charts currently have no estimate badges.
- Persisted the plan, made an integrity-checked online backup, rehearsed on a copy,
  acquired a live write lock, and revalidated evidence, replay state, listing plan,
  allocation, and all operational tables. Committed through `SalesService` once.
  Saved-state checks prove exactly 26 listings changed, no observations appended,
  starts and unrelated tables preserved, integrity/foreign keys clean, all costs
  known, and 827 sold/203 active listings. The PC database is unchanged.
- Unique private checkpoint:
  `data/reports/manual-screenshot-sales-2026-10-18-230550428436Z.json`, status
  `committed`. Evidence, transcript, allocation, driver, and rehearsal stay under
  ignored `data/reports/sales-catch-up-2026-10-18-230550428436Z/`; the checkpoint
  records the backup path. Slack attachments remain available. Do not replay.
- Verification: all 61 focused Sales/capture/allocation tests pass, repository Ruff
  lint/formatting pass, public-file policy passes, and `git diff --check` passes.
  The full `scripts/check.sh` was not repeated for operational reconciliation;
  no application code, schema, or warehouse source changed. Preserved preexisting
  memory/session-note edits. No commit, push, Slack message, hosted snapshot, or
  worker-gate change was requested or performed.

## Configure VPS Google sign-in

- The owner supplied the Downloads path for a Google OAuth client JSON. Validated
  its Web application type and exact HTTPS callback without displaying its secret.
  The Audience screenshot already showed External/In production; preserved it.
  Existing allowlist contains one owner account; preserved it and the cookie secret.
- Success criteria: credentials remain private, the real domain redirects through
  Google, APIs/assets are protected, both empty test workspaces render, public
  branding pages stay reachable, and unrelated VPS routes are preserved. Live
  state transfer waits for the owner's actual Google sign-in result.
- Deployed pinned source `f2dad52` under `/opt/dofus-economy-analytics`, with no
  operational data or secrets in the image context. Built the app, migrated separate
  empty Touch and PC databases, and started the app/authentication containers.
  They run as nonroot with read-only roots, no published ports, and secrets mounted
  only into authentication. Runtime config stays outside the source checkout.
- Inspected the current NPM peer instead of reusing the earlier preparation IP,
  which had changed after a restart. Updated only the Dofus domain's upstream to
  the Google gateway. Preserved its certificate, HTTPS requirement, exact public
  branding exceptions, and all nine other proxy hosts. Saved the previous route
  privately for rollback; Nginx config validation passes.
- Verified public HTTPS responses: operational pages, assets, and OpenAPI redirect
  to Google; API returns 401; about/privacy/stylesheet return 200. Responses disable
  shared caching. Verified exact callback, minimal identity scopes, secure host-only
  cookies, forged-header/token/cookie denial, both test worlds rendering, missing/
  foreign-origin write denial, clean empty SQLite databases, and app secret isolation.
- All 38 focused workspace and hosted-security tests pass. Private evidence,
  deployment driver, status, and checks are under ignored
  `data/reports/vps-deployment-2026-10-18/`. Started a separate icon archive/manifest
  for eventual transfer, without moving live databases or stopping local writers.
  The private status records preparation progress; verify archive completion before use.
- Asked the owner to open the domain and complete Google sign-in. The site currently
  uses empty disposable test state. Local SQLite remains authoritative; final
  cutover must use fresh online backups of both databases and verify every table
  plus all icon hashes after transfer. Future screenshot updates must target the
  authoritative VPS after cutover rather than continuing to write the local copy.
- No source-code edit, commit, push, BigQuery publication, or Slack message occurred.
  Preserved preexisting memory/session-note edits. The complete warehouse script
  was not repeated for runtime configuration; focused tests and live checks cover
  the changed deployment boundary.

## Multi-user economy requirement

- The owner requested assigning existing economy/Sales history to their Google
  account and allowing other people to use their own accounts. Shared current
  market prices and common game data should coexist with private Sales records.
- Inspected the current schema/deployment boundary: listings have no owner, price
  observations are linked to listings, and authentication currently gates a shared
  application rather than identifying data owners. This requires ownership and
  query/write isolation before opening access to other accounts.
- Live-data transfer remains pending while admission, shared-price contributions,
  automatic price sharing from listings/sales, server scope, and administrator
  visibility are clarified. Existing owner-only gateway and empty VPS test state
  remain in place. No live data, user ownership, or access settings changed.
