# Session Notes — 2026-10-19

## Resume multi-user economies and hosted access requests

- Resumed the paused October 18 implementation from the working tree, approved
  multi-user design, ADR 0005, and ignored migration/browser/check reports. The
  task-observer skill was unavailable; no observer logs were created. Preserved
  preexisting work and did not commit, push, publish BigQuery data, or send Slack
  messages.
- Success criteria: preserve every legacy field while assigning existing private
  records to the owner; isolate all accounts' Sales and reports, including the
  administrator; share anonymous prices within each world; gate access by durable
  approvals; report SMTP delivery truthfully; prevent stale-tab/browser state
  crossover; validate locally and against disposable hosted state before cutover.
- Completed owner-scoped SQLAlchemy sessions, account admission/approval routes,
  durable notification state, contributor permissions, anonymous completed-sale
  price publication, and owner-only analytical exports. Account persistence now
  lives in its repository, while service code owns admission and mail commands.
- Closed additional ownership write paths: legacy bulk mapping/save APIs, ORM
  bulk inserts, executemany writes, owner reassignment through ordered/parameterized
  updates, and contributor reassignment. Added cross-account delete/identity-map,
  concurrent first-login, lazy/joined/select-in relationship, and immutable-session
  scope checks. A grouped price-history deletion now checks the selected
  observation's contributor before invalidating the acting contributor's rows.
- Browser state uses account/world keys for carts, selections, checklist, craft
  quantities, and remembered world. Dynamically created forms carry the originating
  account. Hosted pages disable shared HTMX history snapshots; focus/Back checks
  refresh after an account switch. Added SMTP-config filenames to Git, Docker, and
  public-file exclusions. Updated architecture, hosting, public information pages,
  and the existing screenshot workflow reference for these boundaries.
- Repeated fresh online-backup migration rehearsals for both real local databases.
  Applied `0012` locally inside a write lock with a second locked online backup,
  exact comparisons of every preexisting table/column/value before commit, and
  saved-state integrity/foreign-key checks. All prior data remains unchanged; Touch
  retains 827 sold and 203 active listings, and PC has no fabricated Sales. All
  legacy listing/capture owner keys and price contributor keys are `owner`.
  Both worlds' Home, Sales, and Dashboard render after migration. Private evidence
  and backup paths: `data/reports/vps-deployment-2026-10-18/local-ownership-applied.json`.
- Deployed the reviewed application source to the existing disposable VPS state,
  backing up the old source, image, configuration, and empty databases privately.
  Used the already-private owner email, re-inspected the trusted NPM peer, migrated
  both empty workspaces, and replaced the gateway allowlist with application
  approvals. No local operational database or icon cache was transferred. The
  deployment archive SHA-256 and rollback location are in the ignored
  `resumed-accounts-deploy.json` report. Source remains uncommitted locally.
- Verified the real running application's pending/approved/denied gates, API/assets,
  both worlds' private Sales, shared prices, note privacy, known-UUID mutation
  denial, owner-control restriction, exact-origin writes, and stale-tab rejection.
  All synthetic accounts, items, observations, and Sales rows were removed. The
  real reserved owner account was never bound to a synthetic Google subject.
- Public HTTPS checks confirm Google redirects for operational pages/assets and
  OpenAPI, 401 for unauthenticated APIs, and 200 for about/privacy/stylesheet.
  Gateway checks confirm minimal scopes, callback, secure host-only cookies, and
  forged-credential rejection. An isolated instance of the pinned proxy image
  proves authenticated headers replace supplied user/email headers; its containers
  and network were removed. The pinned Google provider source also maps the
  verified Google subject to the user header; no Google tokens enter FastAPI.
- Confirmed nonroot/read-only containers, unpublished app/auth ports, app-only
  backend networking, and Google-secret isolation. Restarted the app and verified
  health, account-registry persistence, clean empty disposable databases, and
  integrity. Existing NPM routing was not edited during this deployment.
- Verification: `scripts/check.sh` passed, including all 126 dbt build/test nodes,
  SQL lint, Python checks, compilation, and public-file policy. After the final
  account repository and regression changes, all **515 Python tests** passed; all
  56 focused account/security/world tests passed. Desktop/mobile Playwright checks
  passed for separate carts, dynamic form account pinning, disabled shared history,
  stale-tab denial, account-switch refresh, truthful pending screens, no repeat
  successful notification, approval controls, and no horizontal page overflow or
  JavaScript errors. Final lint/format, public-file, and whitespace checks passed.
  The preexisting Starlette/httpx deprecation warning remains unrelated.

## Remaining real-account and cutover steps

- Requested the private SMTP configuration path and confirmation of real owner
  Google sign-in. Neither was provided during the resumed work. The latest runtime
  check confirms the reserved owner has no bound Google subject yet.
- The protected SMTP configuration currently contains `{}`. Failed notification
  attempts remain durable and throttled; the screen explicitly says the request
  was saved and email is pending. SMTP acceptance and actual owner receipt still
  need verification; no invite email was sent in this session.
- **Local SQLite remains authoritative.** Configure SMTP, verify real owner and
  applicant sign-in, deliver an invite request, and exercise approval before final
  live cutover. Stop local writers and take fresh backups at that point, including
  any Sales recorded after today's migration. Preserve the VPS Touch account
  registry when transferring local history so real identity bindings, approvals,
  and mail state survive. Check disposable databases for any intervening real
  writes before replacing them. Transfer/verify both databases and shared icons,
  then make the VPS the sole writer, including screenshot reconciliation.
- Current private checkpoint: `data/reports/vps-deployment-2026-10-18/status.json`.
  Do not repeat already-completed local migrations or deploy from the older archive.

## Public homepage and Sign out placement

- The owner requested a homepage with an optional Google sign-in action instead
  of immediately entering Google login, and Sign out at the right of the page.
- Added a public static homepage at `/` with a **Sign in with Google** button,
  brief product information, access-request guidance, and about/privacy links.
  NPM checks the existing gateway session through an internal auth subrequest:
  signed-out visitors see static public content, while valid sessions continue
  through the full gateway to the existing private Home or account-approval page.
  The internal check cannot be requested directly. Other operational paths and
  assets retain their authentication and account-approval gates.
- Moved Sign out outside primary navigation to the right of the game/server
  controls. On mobile it sits at the top right with space reserved beside the
  brand. Pending/denied accounts also receive a right-aligned header button.
  Both buttons explicitly return to `/` after the gateway clears the session.
- Verified all 79 focused hosted-security, account, Home, and static-asset tests;
  repository Ruff lint/formatting, public-file policy, and whitespace checks pass.
  Desktop/mobile browser checks cover 320–1440px, right-aligned controls, public
  sign-in visibility, account switching, stale tabs, and no page overflow or script
  errors. Visually reviewed the landing and mobile app screenshots privately.
- Rehearsed the complete proxy configuration in isolated containers using the
  actual NPM image, pinned login proxy, static service, and a synthetic upstream.
  Verified public root responses, forged-cookie/header rejection, protected APIs
  and assets, hidden internal session route, explicit Google login, a real signed
  synthetic cookie reaching private Home, and logout clearing that cookie and
  returning to the landing page. Removed the test containers and network.
- This is a template, CSS, static-content, and proxy change. No application Python
  behavior, database schema, operational records, or warehouse models changed;
  the full analytics check script was not repeated after the earlier passing run.
  Local SQLite remains authoritative, and the separate real Google/SMTP/live-data
  cutover work remains pending.
- Deployed the new app image, static homepage, and NPM routing after making private
  source/image/database/route backups. No migrations or state replacements ran.
  Nginx validation passes for both public service and NPM; the certificate and all
  nine unrelated proxy hosts are preserved. Public HTTPS now returns 200 at `/`
  without a login redirect, starts Google only from the sign-in action, clears
  supplied session cookies on logout, and returns to the homepage. Other protected
  pages/assets still redirect, APIs still return 401, forged identity/cookies do
  not unlock them, and the internal auth path returns 404. Deployment and live
  checks are in ignored `landing-ui-deploy.json` and `landing-live-https.json`.

## Publish the pending work to GitHub

- The owner requested pushing the pending work to the configured remote. Target:
  `origin/main` at `jinsoowhang/dofus-economy-analytics`. Read-only remote inspection
  confirmed its starting head matched the local base; no force push is required.
- Split publication into three atomic commits: October 18 operational/session
  records; approved private economies, account access requests, and related
  documentation; then the public homepage and right-aligned Sign out controls.
  Each feature commit includes its session record and durable memory updates.
- Ran the complete `scripts/check.sh` against the final application tree: all
  **515 Python tests** and **126 dbt build/test nodes** pass, along with Ruff,
  formatting, compilation, SQL lint, and public-file policy. Independently exported
  the account-isolation index before the homepage changes and verified all 89
  focused account/security/Home/assets/snapshot/migration tests against that
  intermediate commit using the existing locked environment without reinstalling.
- Publication checks include intentional path staging, whitespace checks, a
  complete-history Gitleaks scan with redacted private output, exact remote-head
  verification after the normal push, and a clean working tree. Check logs and the
  push result stay in ignored `data/reports/github-publication-2026-10-19/`.
- No database write, data transfer, deployed-service change, BigQuery sync, or
  external message is part of this GitHub publication. SMTP verification, real
  owner/applicant Google sign-in, and final authoritative VPS cutover remain pending.
