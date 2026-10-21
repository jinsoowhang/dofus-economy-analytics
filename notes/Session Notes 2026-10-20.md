# Session Notes — 2026-10-20

## Check hosted versus local website parity

- The owner asked whether the website works the same as local. Success criteria:
  compare deployed source, running service health, public authentication behavior,
  and database population without changing either runtime.
- Read-only SSH checks confirmed all 110 files under `src/`, `migrations/`, and
  `deploy/` match local SHA-256 hashes, with no extra remote files in those scopes.
  App and public-page containers are healthy; the login gateway is running.
- Both hosted worlds remain disposable login-check databases with zero items,
  price observations, recipes, and sale listings. Local Touch has 11,400 items,
  3,050 observations, 7,847 recipes, and 1,030 sale listings; local PC has 13,469
  items, 700 observations, 4,501 recipes, and zero sale listings. Local data remains
  authoritative, and there is no cross-host SQLite synchronization.
- SMTP is still unconfigured. Real Google sign-in, actual request-mail delivery,
  approval verification, and the documented final data/icon cutover remain pending.
- Live HTTPS checks: homepage/about return 200, Sales redirects to Google,
  unauthenticated item API returns 401, and the internal session path returns 404.
  The web browsing tool could not access the hostname; direct HTTPS checks worked.
- No runtime data, deployment, or application behavior changed. Full application
  and analytics tests were not rerun for this read-only investigation; focused
  runtime/source checks above directly verify the requested comparison.

## Populate hosted Touch / Blair from the owner's existing sales

- The owner clarified that hosted Touch should contain their sales-backed data.
  Completed a Touch-only production cutover; PC / Tal Kasha's local and hosted
  data remain unchanged. Missing SMTP configuration does not block the approved
  owner's access and was not treated as a prerequisite for this scoped transfer.
- Fresh inspection found the owner had now completed real Google sign-in: the
  configured owner email matched its bound subject and approved administrator
  record. Both disposable hosted worlds still had no operational records.
- Confirmed no Dofus web/worker processes were running on Linux or Windows. Took
  a fresh online Touch backup, verified integrity/foreign keys/schema/ownership,
  and compared deterministic hashes of every table's schema and complete rows.
  Rechecked the unchanged local source under `BEGIN IMMEDIATE` during cutover.
- Transferred 11,400 items, 7,847 recipes, 3,050 observations, 827 completed sales,
  203 active listings, and all other existing Touch operational rows unchanged.
  Hash-verified all 11,390 available Touch icons; ten icons were already absent
  locally. No new observations, listings, or sales were fabricated.
- Prepared a separate production state directory, preserving the old disposable
  state and private runtime configuration backups for rollback. Copied the empty
  hosted PC database unchanged to the new mount and preserved the complete hosted
  Touch account registry. No private identities or data entered tracked files.
- An isolated unpublished container rehearsed the copied state with the real
  owner's existing binding. Initial rehearsal found root-owned SQLite WAL/SHM
  sidecars; assigning all database files to the application UID fixed that
  deployment permission issue. No application-code change was needed. The final
  rehearsal renders Home, Sales, Dashboard, Item Search, Recipes, Insights, PC Home,
  CSS, and a byte-verified icon; Sales explicitly shows 203 active and 827 sold.
- Stopped the app and login gateway, backed up disposable databases/configuration,
  merged the latest account registry, set the production state mount, and started
  the app. Repeated route, exact operational-row, registry, and PC comparisons
  before reopening the gateway, preventing new user writes during comparison.
  Public content remained served independently. Automatic rollback was prepared
  and was not needed.
- **The VPS is now the sole authoritative Touch writer**, at
  `/var/lib/dofus-touch-economy/dofus_touch.sqlite3`. The local Touch database is a
  retained pre-cutover copy. Future screenshot reconciliation must use the
  existing private SSH/container workflow described in the catch-up skill's
  operational reference; do not keep updating the local Touch copy. Local PC
  remains authoritative for PC. No Slack automation or BigQuery sync was enabled.
- Verification: all 93 focused account/security/migration/world/Sales tests pass.
  Freshly started production app renders the same verified pages/data. Integrity,
  foreign keys, record preservation, icon checksums, and account preservation pass.
  Full analytics checks were not repeated because application code, migrations,
  and analytics models did not change. Private manifests, rehearsal logs, transfer
  results, post-cutover checks, and rollback locations are under ignored
  `data/reports/vps-touch-cutover-2026-10-20/`.
- Final public HTTPS checks pass: homepage/about 200, Sales and icons redirect to
  Google, unauthenticated API 401, and internal session path 404. App/public-page
  health, production mount, database integrity, and approved owner binding pass;
  all services remain unpublished on the host. Public-file and whitespace checks
  pass; only project memory and today's session note are tracked changes.
- SMTP remains unconfigured; request-email delivery and applicant approval testing
  remain separate outstanding work. Owner data access and Touch cutover are complete.

## Research and improve the public sign-in page

- The owner requested a less plain sign-in page and design research. Success
  criteria: a distinct Dofus-appropriate visual identity, one clear Google action,
  accurate access/privacy copy, responsive layout, accessible keyboard operation,
  and a live static-only update that preserves the production Touch deployment.
- Research informed these decisions:
  - [NN/g login guidance](https://www.nngroup.com/articles/checklist-registration-login/)
    recommends explaining registration benefits and minimizing input. Retained
    one Google action and added short, concrete workspace benefits.
  - [NN/g login-wall research](https://www.nngroup.com/articles/login-walls/)
    supports explaining product value before requiring sign-in. The public page
    illustrates crafting economics without exposing private operational records.
  - [Google branding guidance](https://developers.google.com/identity/branding-guidelines)
    and its official HTML configurator informed the light button, standard-color
    logo, sign-in wording, spacing, and Roboto/Arial font fallback. The existing
    gateway link remains unchanged; no Google SDK or external font was introduced.
  - [W3C contrast guidance](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum)
    informed legibility checks. All twelve checked text/focus color pairs exceed
    4.5:1 contrast, with a minimum of 4.88:1; the primary action is at least 48px tall.
- Implemented a forest-green/ivory/gold split layout, original inline SVG gem and
  coin artwork, a clearly labeled illustrative crafting ledger, focused sign-in
  panel, privacy reassurance, and truthful account-approval guidance. Mobile places
  sign-in before the decorative panel. Added a working skip link and reduced-motion
  and forced-colors handling. New CSS is scoped to `.landing`; existing public
  About/Privacy content and styles remain intact.
- Browser QA passes twelve width/color-scheme combinations from 320–1440px with
  no overflow or browser/CSP errors. Verified visible mobile sign-in, primary touch
  target, keyboard focus, skip-link-to-action sequence, unchanged Google redirect
  destination, and existing information pages. No external asset requests occur.
  Visually reviewed desktop/mobile screenshots under the ignored report directory.
- All 61 existing focused hosted-security/Home/static-asset tests pass. Public-file
  policy and whitespace checks pass. No new implementation-mirroring tests were
  added. Full Python/analytics checks were not repeated for an HTML/CSS-only change.
- Published only `deploy/public/index.html` and `deploy/public/public.css` after
  backing up the previous public files. Exact checksums match the running static
  service. App, gateway, and static-container IDs/start times remain unchanged;
  runtime configuration and database files were not part of deployment. No NPM,
  CSP, public-route, authentication, approval, or data-access changes were needed.
- Private research snapshots, screenshots, browser/contrast checks, deployment
  manifest, rollback location, and HTTPS results live under ignored
  `data/reports/signin-design-2026-10-20/`. Signed-in visitors still reach private
  Home; sign out to see the new entry page.
