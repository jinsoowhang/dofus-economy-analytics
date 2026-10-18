# Session Notes 2026-10-11

## Private VPS hosting and public repository preparation

- The user requested VPS hosting, Gmail sign-in, and keeping the project suitable
  for public GitHub publication. Located the reference projects under the local
  `AI & Automation` directory and confirmed their actual VPS through deployment
  records. Read-only SSH inspection confirmed the existing Nginx Proxy Manager,
  Docker network, and sufficient resources. A different saved SSH alias failed
  host-key verification; it was not modified or bypassed.
- Chose a Google OAuth2 Proxy gateway with a private verified-email allowlist in
  front of the existing single-user FastAPI app. NPM owns HTTPS. No app/auth port
  is published, and only the gateway joins NPM's existing network. SQLite remains
  the operational database, with one worker and persistent external state. This
  authorizes full access for listed accounts; it does not add user-separated data.
- Added the Dockerfile, a restricted build context, Compose configuration, public
  deployment environment example, NPM security/cache configuration, and a runbook.
  OAuth secrets and the allowlist mount only into the nonroot gateway, outside
  the checkout; app/icon state uses an external directory owned by the app UID.
  No real server addresses, personal emails, or credentials were added to source.
- Added optional `DOFUS_PUBLIC_ORIGIN` validation and hosted Origin/Referer checks
  on every unsafe method, rejecting missing sources, cross-origin/scheme writes,
  malformed origins, and cross-site Fetch Metadata. Local behavior and the
  loopback-only CLI remain intact. Hosted navigation includes proxy Sign out.
- Strengthened ignore/public-file rules for private deployment configuration,
  allowlists, OAuth/cookie secret files, credential JSON, nested secret directories,
  and private keys. Added pinned Gitleaks full-history scanning to GitHub CI.
- Verification: full `./scripts/check.sh` passed Python lint/formatting, all 478
  Python tests, package compilation, dbt debug/parse/seed, all 126 build/test nodes,
  SQL lint, and public-file policy. Gitleaks v8.30.1 was checksum-verified and found
  no secrets in all 225 Git commits or the proposed public-file export. Focused
  security tests cover actual denied and accepted writes plus trusted hosts.
- Built the image and ran the Compose stack on the actual VPS with synthetic
  SQLite state and fake OAuth credentials, on a disposable network. All migrations
  passed. Verified zero published ports, nonroot/read-only containers, Google login
  redirects, host-only Secure/HttpOnly/SameSite cookies, denied unauthenticated API
  calls, protected assets/docs, spoofed identity/token/cookie denial, hosted write
  checks, app secret isolation, SQLite integrity/foreign keys, and restart persistence.
  Removed the synthetic containers, networks, state, and temporary source afterward.
  An initial SSH-streamed test ended after migration because Compose consumed its
  script stdin; reran the isolated test with stdin disabled for migration and
  verified the complete successful result.
- Existing NPM locations define their own `add_header`, so the final Advanced
  snippet uses OpenResty's `more_set_headers` to preserve security/cache headers
  on location and error responses. The actual snippet passed syntax validation and
  an HTTP 401 header check in an isolated container using the VPS's exact NPM image.
  The CI scanner command also passed against a synthetic Git repository owned by
  a different UID. Follow-up focused checks passed after the final file-policy and
  default-environment test changes. The public runbook records setup, exact Google
  callback requirements, data cutover, backup/rollback, and final live checks.
- Requested the desired hostname and owner Gmail address asynchronously. Those
  answers and a Google OAuth Web client remain needed to finish live deployment.
  Real sign-in, owner/other-account authorization, and public HTTPS checks are
  pending; synthetic redirects do not establish a working Google callback.
- Live SQLite, icons, existing VPS applications, NPM routing, and DNS were not
  changed. No commits or pushes were made. Before cutover, stop local writers and
  choose the authoritative VPS database; local screenshot workflows and the
  optional Slack worker cannot continue independently against the old local copy.
- Private diagnostic logs, source export, verified scanner binary, and the synthetic
  test driver remain in ignored `data/reports/vps-preparation-2026-10-11/`.

## Follow-up: default proxy page

- The user reported NPM's default congratulations page at the proposed address.
  Read-only VPS inspection confirmed no Dofus containers or production directories;
  live hosting still awaits owner Gmail and Google OAuth Web-client configuration.
  Asked for those missing details. No routing, DNS, secrets, or application state
  was changed. The existing VPS services were preserved.
- This diagnostic/doc-only follow-up does not warrant rerunning application or dbt
  tests; the earlier full and isolated deployment checks cover unchanged source.

## Owner sign-in configuration

- The user supplied the single allowed Gmail address. Saved it to ignored
  `.secrets/vps/allowed_emails` and the private preparation report, then provisioned
  the same allowlist and a cryptographically random 32-byte cookie secret under
  the VPS's root-protected configuration directory. Mounted secret files belong to
  gateway UID 65532 and have mode 600. Existing differing files are preserved by
  refusing replacement; existing cookie secrets are retained. No personal email or
  secret value was written to the public working record.
- Inspected only the client type of an existing local Google OAuth credential. It
  is an installed/Desktop client, which cannot substitute for the required Google
  OAuth Web application client. Its secret was not copied, printed, or used.
- Updated the runbook's provisioning snippet to preserve matching existing files
  and session secrets rather than failing on previously provisioned configuration.
  OAuth Web credentials and callback configuration still block live sign-in and
  routing. Application source, operational SQLite, existing sites, and DNS remain
  unchanged. Verification is limited to private-file checks, snippet syntax,
  public-file policy, and working-tree whitespace for this configuration follow-up.

## Required public Google branding pages

- The owner's actual console required a homepage and privacy-policy URL. Corrected
  the earlier guidance to leave those blank in Testing. Created source-safe public
  information, privacy, and stylesheet files plus a separate static-service Compose
  configuration. The homepage explains catalog/pricing/recipe/sales functionality,
  private account access, public source, and fan-project status and links to privacy.
  The policy describes basic Google identity scopes, encrypted session cookies,
  browser preferences, operational records and manual analytics snapshots,
  diagnostics, limited sharing, revocation, retention, and privacy requests.
- Public files contain no actual personal email, secret, VPS address, or observed
  record. Privacy requests use the support address displayed on Google's consent
  screen. Added Privacy navigation in hosted mode. The public static service mounts
  no credentials or databases, stays off the app backend network, runs as UID 101
  with a read-only filesystem and dropped capabilities, and publishes no port.
  Only exact public-page/CSS paths are served; other requests return 404 and writes
  are denied. NPM exact locations preserve those public pages after login cutover.
- Built and verified the static service on the existing VPS proxy network. Used
  root-authorized NPM administration with an in-memory, five-minute token for an
  existing enabled administrator; no password, signing key, or token was printed
  or persisted. Changed the target hostname only through NPM's management API,
  preserving its configuration generation, audit, and certificate-renewal lifecycle.
  Created an integrity-checked, mode-600 SQLite backup of NPM in private server
  storage before writes. The eight unrelated active proxy-host records are unchanged.
- Issued a managed Let's Encrypt certificate and enabled Force SSL. An initial
  post-create check saw the API's stale pre-configuration metadata; re-fetched the
  saved record, confirmed Nginx was online, and continued the same target host.
  No duplicate host or certificate was created. Default Python user agents receive
  Cloudflare 1010; normal browser user agents receive the public pages with HTTP
  200 and no-store headers. Cloudflare configuration was preserved.
- Public HTTPS checks verify About, Privacy, and CSS content through Cloudflare,
  with sales and API paths returning 404 while the login application remains pending.
  Scoped Python verification passed 123 hosted-security, web, Home, public-file, and
  documented-command tests plus repository lint/formatting. NPM configuration
  validation passed. SQLite/application behavior and dbt models did not change, so
  the previous full 478-test/126-node check was not repeated for this follow-up.
- The initial information-only deployment lives separately from the future private
  application checkout. No operational SQLite or icon state was moved, no Google
  OAuth client secret was supplied, and no commits or pushes were made. The owner
  can now fill the required branding URLs and continue creating the OAuth Web client.

## Stopping checkpoint

- The owner requested stopping until the next usage-limit reset and will update
  Sales locally in the meantime. Local SQLite remains authoritative; the VPS serves
  information/privacy pages only and has no operational database or icon copy.
- Public About and Privacy pages are reachable over valid HTTPS. The origin
  certificate and the HTTP-to-HTTPS redirect were independently verified. OAuth
  Web-client credentials, actual owner/other-account sign-in verification, and
  operational cutover remain pending. Existing VPS sites and local Sales data are
  preserved. Code and session records remain uncommitted and unpushed.
- On resume, finish the Google Web-client callback setup and secure app deployment.
  Before any database transfer, stop local writers and take a fresh online backup
  that includes the owner's new local sales; do not deploy an earlier snapshot.
  Transfer icons separately, verify integrity and table counts, and settle the
  authoritative workflow for local screenshot reconciliation and the Slack worker.

## Sales catch-up and processed screenshot cleanup

- The owner invoked `$dofus-sales-catch-up` and requested updating it to delete the
  latest used screenshot from Downloads. Used skill-creator for the narrow change.
  The skill now requires verified private evidence retention, a committed sales
  audit, and saved-state verification before deleting exact processed originals.
  Blocked/uncertain/modified screenshots stay available; cleanup retries never
  replay committed Sales updates. The existing user-directory symlink shares the
  repository skill, so both discovery paths use the updated instructions.
- Found one new Downloads image, `IMG_9542.png`, saved October 11 at 16:40:46 Pacific.
  Visually transcribed all 20 complete sales, preserving repeated occurrences and
  observed quantities and lot totals. Enlarged Ouginiakal Belt to confirm its exact
  spelling before matching. Nine quantity-one equipment sales resolve uniquely
  within Tailor/Shoemaker/Jeweller scope and match existing active asking prices.
  Eleven resource-lot sales remain out of scope; they are retained in the private
  transcript but were not expanded or written to Sales. No expiration notices or
  confirmed screenshot overlap were present.
- Used the committed October 10 report as the prior coverage checkpoint. The
  established next-day interval contains October 11 only, so all nine sales use
  `manual` at the screenshot save time; no weekday-based multi-day imputation was
  needed. This timestamp remains a reporting proxy, not the exact individual sale
  times. Reconstructed the non-estimated August 22–September 12 daily baseline and
  verified its equality with the prior audit without extending training exposure.
- Recorded nine sales for 383,000 kamas, with zero price corrections and known
  historical recipe costs for all nine. Preserved the independent manual sale and
  stock changes since the earlier screenshot report. Before applying, copied and
  hash-verified the screenshot into ignored private evidence storage, created an
  integrity-checked online SQLite backup, and rehearsed on an isolated copy.
- Rechecked complete live table snapshots, the screenshot hash, capture plan, and
  date allocation under a write lock, then applied the batch through SalesService
  in one transaction. Pre-commit and saved-state checks confirm exactly the nine
  selected listings changed, no price observations appended, no listings created
  or deleted, original starts and unrelated tables/history preserved, conserved
  revenue, and passing integrity/foreign-key checks. Counts changed from 777 sold
  and 224 active to 786 sold and 215 active.
- After the committed audit was saved and verified, rechecked original/archive
  hashes and removed only `IMG_9542.png` from Downloads. Its byte-identical private
  copy and audit remain available. Cleanup status and completion time are recorded
  in `data/reports/manual-screenshot-sales-2026-10-11.json`. That committed audit is
  the replay checkpoint; do not apply the screenshot again.
- Verification passed skill validation, 56 focused allocation/Sales/capture tests,
  allocation CLI execution, and private-driver lint/formatting. Repository lint,
  formatting, public-file policy, and working-tree whitespace are also checked.
  The full dbt build is not repeated because this is an operational-data update
  plus skill instructions, with no application algorithm, schema, or SQL changes.
  Evidence, transcripts, drivers, trial database, and backup remain ignored. No
  staging, commits, pushes, BigQuery sync, Slack messages, or VPS cutover occurred;
  the paused hosting work and unrelated pending files remain intact.
