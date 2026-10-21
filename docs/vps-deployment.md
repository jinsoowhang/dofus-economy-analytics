# VPS hosting with Google sign-in

This deployment keeps the source public and operational records behind Google
sign-in and account approval. Anyone may sign in to request access. Pending users
see their request status; approved users share market prices within each game/server
and access only their own listings, sales, profits, and personal reports. The owner
manages approvals and price corrections without a page for other users' Sales.
See [ADR 0005](adr/0005-isolate-user-economies.md).

```text
Browser -> HTTPS / Nginx Proxy Manager -> OAuth2 Proxy -> FastAPI -> SQLite
                                             |
                                         Google login
```

Nginx Proxy Manager (NPM) owns the certificate and HTTP-to-HTTPS redirect. OAuth2
Proxy owns Google authentication, OAuth state, and secure session cookies. FastAPI
owns account approval and private-data authorization. Neither container publishes an application or authentication
port. The authentication container and public information service join the existing
NPM Docker network; FastAPI joins the application network. Keep NPM's admin UI private.

Signed-out visitors to `/` see a public homepage with a **Sign in with Google**
button. A valid gateway session continues to the account-approved Home checklist
at the same address. Sign out sits at the right of the application header and
returns to the public homepage after clearing the login session.

The homepage and exact `/about`, `/privacy`, `/public.css`, and `/theme.js` paths are served by
a separate static container with no application network, database, or secret mounts.
NPM uses an internal session-check subrequest only to choose which root page to
serve; private requests still pass through the full login gateway and application
approval checks. Every operational record and asset remains behind authentication.

Hosted writes require an Origin header matching the exact configured HTTPS origin,
or a matching Referer when Origin is absent. Cross-site Fetch Metadata is denied.
This applies to HTML and API writes. The deployment disables shared caching and
uses Secure, HttpOnly, host-only, SameSite=Lax login cookies. A programmatic write
also needs an authenticated session and a matching Origin; setting Origin alone
does not authenticate it. `dofus-web` remains loopback-only for local use. The
container uses a separate Uvicorn command on its unpublished Docker network.

## Requirements and Google configuration

Use a Linux VPS with Docker Compose and an existing NPM container, a hostname you
control, and a Google OAuth **Web application** client. A Desktop client or
BigQuery service-account credential does not provide browser sign-in.

In Google Cloud's Google Auth Platform, configure the app audience and branding,
then create a Web application client with this authorized redirect URI, replacing
the example hostname:

```text
https://economy.example.com/oauth2/callback
```

The redirect URI must match exactly. Use only `openid email profile` scopes; no
Gmail inbox permission is needed. During External/Testing configuration, add the
owner as a test user. Production status and Google's consent-screen requirements
are separate from this application's account approvals. Follow Google's
[web-server OAuth instructions](https://developers.google.com/identity/protocols/oauth2/web-server)
and OAuth2 Proxy's [Google provider documentation](https://oauth2-proxy.github.io/oauth2-proxy/configuration/providers/google/).

Configure the branding homepage as `https://economy.example.com/about` and the
privacy policy as `https://economy.example.com/privacy`, replacing the hostname.
Use the required fields shown by your console; do not assume these links can be
omitted in Testing. The pages must be publicly reachable over valid HTTPS. If
Google requests domain verification, the domain owner must complete the Search
Console verification. These links do not expose the operational application.

Start public pages first, with only the existing proxy network configured:

```bash
DOFUS_PROXY_NETWORK=your_proxy_network docker compose -f deploy/compose.public.yml up -d --wait
```

Before OAuth credentials exist, an NPM host can forward to `dofus-public-pages`
on HTTP port 8080 with a valid certificate and Force SSL. This service only serves
its information pages, stylesheet, and shared appearance script; operational paths return 404. After login
is ready, point the host at `dofus-google-login:4180` and install the exact public
location rules in `deploy/npm-advanced.conf`. Keep the static service running.

## Private server configuration

Clone the public source to `/opt/dofus-economy-analytics`. Keep all runtime
configuration outside that checkout. The following commands run as root on the
VPS, with secrets entered through hidden prompts:

```bash
install -d -m 700 /etc/dofus-touch-economy
install -d -m 700 /etc/dofus-touch-economy/secrets
install -d -m 700 -o 10001 -g 10001 /var/lib/dofus-touch-economy
cp deploy/.env.example /etc/dofus-touch-economy/app.env
chmod 600 /etc/dofus-touch-economy/app.env
```

Edit `app.env` with the selected hostname, actual market context, Google web
client ID, `DOFUS_OWNER_EMAIL`, NPM network name, and NPM container IPv4 address. Inspect the existing
network rather than assigning a new address or opening another firewall port:

```bash
docker inspect YOUR_NPM_CONTAINER --format '{{json .NetworkSettings.Networks}}'
```

The example proxy IP is only a placeholder. `DOFUS_TRUSTED_PROXY_IP` must name the
actual NPM container peer, not a public visitor IP or the VPS IP. Recheck this
setting if NPM is recreated with another address. The proxy's official
[configuration reference](https://oauth2-proxy.github.io/oauth2-proxy/configuration/overview/)
explains the forwarded-header trust boundary.

Create `google_client_secret` and `cookie_secret` under the private secrets
directory. Preserve existing valid secrets. The Google secret file contains only
the Web client's secret, without a trailing newline; the cookie secret contains
32 random bytes. Set both to mode 0600 and UID/GID 65532 for OAuth2 Proxy.

Create `invite_mail_config.json` in that same directory with the SMTP settings:

```json
{
  "host": "smtp.example.test",
  "port": 587,
  "username": "mailer@example.test",
  "password": "replace-with-private-smtp-password",
  "from_address": "mailer@example.test",
  "implicit_tls": false
}
```

Use STARTTLS on 587, or `implicit_tls: true` on 465. The app always verifies TLS
certificates. Gmail SMTP requires a Gmail app password; the Google sign-in OAuth
credential does not authorize sending email. Store this JSON as mode 0600 owned by
UID/GID 10001. It is mounted only into the app as a read-only secret. Do not put
real values in Git or shell history. A temporary `{}` file permits testing the
saved-request path, but actual delivery must be configured and verified before
claiming the invite-email workflow is complete.

The private owner email is set through `DOFUS_OWNER_EMAIL` in `app.env`. The app
bootstraps the reserved `owner` account and binds it to the first verified Google
subject matching that address. Existing economy rows migrate to this account.
Other accounts are identified by their stable Google subjects and start pending.
Approvals, denial, and failed-email retries are available at
`/admin/access-requests` only to the owner. Failed notifications remain saved and
retry at most once per ten minutes; a successful SMTP submission is not resent by
page refresh. An SMTP acceptance/crash boundary can cause a later retry, so delivery
is at-least-once rather than an exact-once mail guarantee.

OAuth2 Proxy uses `--email-domain=*` to authenticate access applicants. Admission
is enforced in the app, replacing the old gateway email allowlist. Keep
`--pass-user-headers=true`, `--prefer-email-to-user=false`, and
`--skip-auth-strip-headers=true`: the gateway strips caller-supplied identity and
sets `X-Forwarded-User` to the Google subject and `X-Forwarded-Email` to its verified
email. Never expose the app's port or attach it to the public proxy network.
Those identity headers are trusted only on the isolated app/authentication network;
a directly exposed app could be impersonated. Neither Google tokens nor the Google
client secret is passed to the app. Only the SMTP secret is mounted there.

## Preserve operational state and choose the authoritative database

The VPS database becomes authoritative after cutover. Stop the local web process
and Slack worker before the final transfer. Do not continue writing to both copies;
there is no cross-host SQLite synchronization. Local screenshot reconciliation and
the optional worker must use the authoritative database through an explicitly
chosen future workflow; this deployment does not move their credentials or enable
their automation.

Make a SQLite **online backup** into an ignored local path, verify its integrity,
and transfer that backup over SSH as
`/var/lib/dofus-touch-economy/dofus_touch.sqlite3`. Do not copy only the live `.sqlite3`
file while WAL writes are active. Transfer `data/app/item_icons/` separately to
`/var/lib/dofus-touch-economy/item_icons/`; icons are not stored in SQLite. Keep an
untouched pre-cutover backup and compare table contents and integrity after transfer.
Repeat online backup, migration, and verification for `dofus_tal_kasha.sqlite3`.
The icon directory contains both worlds’ UUID-addressed icons. Rehearse revision
`0012` on backup copies first and confirm that every legacy listing/capture owner
and price contributor is `owner`, with all preexisting values unchanged.
If sign-in was tested against disposable databases, stop the gateway and app before
cutover and preserve the central `user_accounts` registry from that Touch database.
Copy its verified owner binding, access decisions, and notification state into the
migrated production Touch backup before restarting. Check both disposable worlds
for operational writes and resolve any real records before replacing them; only
known synthetic verification rows may be discarded. The PC database must not gain
an independent account registry. Keep the pre-cutover copies for rollback.
Change transferred state ownership to UID/GID 10001 before starting the app:

```bash
chown -R 10001:10001 /var/lib/dofus-touch-economy
```

A fresh installation can instead migrate an empty database and use the existing
import/catalog commands. Private raw exports are never part of the image or Git.

## Start and connect HTTPS

From the checkout on the VPS:

```bash
docker compose --env-file /etc/dofus-touch-economy/app.env -f deploy/compose.yml -f deploy/compose.public.yml config --quiet
docker compose --env-file /etc/dofus-touch-economy/app.env -f deploy/compose.yml -f deploy/compose.public.yml build app
docker compose --env-file /etc/dofus-touch-economy/app.env -f deploy/compose.yml -f deploy/compose.public.yml run --rm app alembic upgrade head
docker compose --env-file /etc/dofus-touch-economy/app.env -f deploy/compose.yml -f deploy/compose.public.yml run --rm -e DOFUS_APP_DATABASE_PATH=data/app/dofus_tal_kasha.sqlite3 app alembic upgrade head
docker compose --env-file /etc/dofus-touch-economy/app.env -f deploy/compose.yml -f deploy/compose.public.yml up -d --wait
```

In NPM, create a Proxy Host for the selected hostname, forward using **HTTP** to
`dofus-google-login` on port **4180**, and request a certificate with **Force SSL**.
Paste [deploy/npm-advanced.conf](../deploy/npm-advanced.conf) into its Advanced
configuration. The NPM container must be on `DOFUS_PROXY_NETWORK`. Do not point NPM
at `app:8000`: that would bypass login. Neither service needs a published port.

If the DNS provider proxies requests, disable cache rules for this hostname and
use strict origin certificate verification. Ensure any upstream proxy also avoids
logging OAuth callback query strings. Do not add an authentication exemption for
static assets, icons, OpenAPI, HTML, or API routes. OAuth2 Proxy's own login and
health endpoints do not expose application data.

Only the signed-out root homepage and the four exact public paths above serve
public content. The `/_dofus_session` location is internal and returns 404 to direct
requests. Use the complete NPM configuration; broad bypasses such as `/static/`
or `/api/` are not part of this design.

The public appearance script is mounted read-only from the application's
`static/theme.js`, so public, pending-access, and approved pages use the same
Light/Dark/System preference. It stores only a browser theme choice and grants no
application access. Public CSP permits same-origin scripts and styles; inline and
external scripts remain blocked. Operational assets under `/static/` retain their
authentication and account-approval checks. Local application pages load the
same script through the existing local `/static/` mount.

Before cutover, verify:

- A signed-out visit to `/` returns the public homepage without redirecting to
  Google. Its sign-in button starts Google login; signing out clears the session
  and returns to that homepage. A valid session at `/` reaches the private Home
  checklist or pending-access screen, according to account approval.
- Other unauthenticated operational pages, icons, and OpenAPI redirect to Google;
  API routes return 401. Spoofed email/Authorization headers do not bypass authentication.
- The configured owner signs in and sees their own data. A second Google account
  sees the request screen, one email reaches the owner, approval unlocks an empty
  private economy with shared prices, and denial revokes access immediately.
- Two approved accounts cannot read/count/change each other’s listings or reports,
  even with known UUIDs or stale tabs. Administrators have no Sales bypass.
  The API, assets, icons, and OpenAPI remain blocked for pending/denied accounts.
- The original items, prices, recipes, and sales are intact. A deliberate test
  write persists through an app restart, and cross-origin/missing-origin writes
  are denied. Use synthetic state when testing mutations before cutover.
- HTTP redirects to HTTPS, the certificate validates, the login cookie has Secure,
  HttpOnly and SameSite=Lax, and Sign out removes the session.
- `docker compose ... ps` reports a healthy application with no published ports;
  existing VPS sites still work. Private data, email addresses, and tokens never
  appear in public logs or Git changes.

The app healthcheck checks HTTP availability; verify SQLite integrity and schema
separately. BigQuery Sync remains manual and owner-only; the existing Sales export contains
only the original owner’s rows, with anonymous common prices. Account records,
contributor keys, other users’ private notes, and other users’ Sales are excluded. The base deployment intentionally does
not mount Google Cloud credentials; configure least-privilege credentials outside
Git separately if that feature is required on the VPS.

## Updates, backups, and rollback

For an update, stop the app and authentication services, make an integrity-checked
SQLite backup outside the checkout, fast-forward the checkout to the reviewed
commit, build, migrate once, and restart with the commands above. Preserve the
private state directory and configuration. Run one application worker because the
BigQuery sync lock is process-local. Container restarts must not rerun imports.

Keep encrypted off-VPS backups of SQLite, icons, and private configuration and test
restoration. For rollback involving a migration, stop services and restore the
matching pre-upgrade database plus source/image; do not run older application code
against an incompatible new schema. Do not use `docker compose down -v` as a
deployment step. Rotating the cookie secret signs out all existing sessions.

## Public GitHub policy

Tracked files contain source, synthetic tests, and deployment examples only.
`.dockerignore` limits build input to application code, migrations, and locked
dependencies. `.gitignore` and the public-file check reject local configuration,
allowlists, secret files, credentials, private keys, operational data, and reports.
GitHub CI also runs Gitleaks across the complete checked-out history. Before a push,
run `./scripts/check.sh`, inspect the explicit staged paths, and run
`git diff --cached --check`. A secret scanner cannot guarantee that every private
value is detected; keep real configuration and data outside the checkout.
