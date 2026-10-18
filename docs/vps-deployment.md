# VPS hosting with Google sign-in

This deployment keeps the source public and the operational website private. Only
verified Google accounts named in a private allowlist may use the website, icons,
or API. Every allowed account has full access to the same single-user database;
this is not a multi-tenant application.

```text
Browser -> HTTPS / Nginx Proxy Manager -> OAuth2 Proxy -> FastAPI -> SQLite
                                             |
                                         Google login
```

Nginx Proxy Manager (NPM) owns the certificate and HTTP-to-HTTPS redirect. OAuth2
Proxy owns Google authentication, account authorization, OAuth state, and secure
session cookies. Neither container publishes an application or authentication
port. The authentication container and public information service join the existing
NPM Docker network; FastAPI joins the application network. Keep NPM's admin UI private.

The exact `/about`, `/privacy`, and `/public.css` paths are intentionally public.
They are served by a separate static container with no application network,
database, or secret mounts. The public homepage explains the app and links to its
privacy policy so Google consent-screen branding can be configured before login
is ready. Every operational route and asset remains behind authentication.

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
are separate from this application's email allowlist. Follow Google's
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
its information pages and stylesheet; operational paths return 404. After login
is ready, point the host at `dofus-google-login:4180` and install the exact public
location rules in `deploy/npm-advanced.conf`. Keep the static service running.

## Private server configuration

Clone the public source to `/opt/dofus-touch-economy-analytics`. Keep all runtime
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
client ID, NPM network name, and NPM container IPv4 address. Inspect the existing
network rather than assigning a new address or opening another firewall port:

```bash
docker inspect YOUR_NPM_CONTAINER --format '{{json .NetworkSettings.Networks}}'
```

The example proxy IP is only a placeholder. `DOFUS_TRUSTED_PROXY_IP` must name the
actual NPM container peer, not a public visitor IP or the VPS IP. Recheck this
setting if NPM is recreated with another address. The proxy's official
[configuration reference](https://oauth2-proxy.github.io/oauth2-proxy/configuration/overview/)
explains the forwarded-header trust boundary.

Create the private allowlist and secrets:

```bash
python3 - <<'PY'
import getpass
import os
from pathlib import Path

directory = Path('/etc/dofus-touch-economy/secrets')
email = getpass.getpass('Allowed Google email: ').strip().lower()
secret = getpass.getpass('Google web client secret: ').strip()
if '@' not in email or '\n' in email or not secret:
    raise SystemExit('An email and client secret are required')
values = {
    'allowed_emails': (email + '\n').encode(),
    'google_client_secret': secret.encode(),
    'cookie_secret': os.urandom(32),
}
for name, value in values.items():
    path = directory / name
    if path.exists():
        if name == 'cookie_secret':
            if len(path.read_bytes()) != 32:
                raise SystemExit('Existing cookie secret must contain 32 bytes')
        elif path.read_bytes() != value:
            raise SystemExit(f'Existing {name} differs; rotate it explicitly')
    else:
        with path.open('xb') as handle:
            handle.write(value)
    path.chmod(0o600)
    os.chown(path, 65532, 65532)
PY
```

OAuth2 Proxy runs as UID 65532, which must be able to read the bind-mounted secret
files. Their parent directory stays root-only on the host. Compose mounts the
files read-only into that service; the application receives no OAuth secrets.
Compose secrets are local files, not an encrypted vault. Include their storage in
your server access and backup policy. Do not set `email_domains=*` or
`email_domains=gmail.com`; either would bypass the owner-only allowlist.

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
untouched pre-cutover backup and compare table counts and integrity after transfer.
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

The three explicit branding paths above are the sole public-content exceptions.
Use exact NPM locations; broad bypasses such as `/static/` or `/api/` are not part
of this design.

Before cutover, verify:

- Unauthenticated pages, icons, and OpenAPI redirect to Google; API routes return
  401. Spoofed email/Authorization headers do not bypass authentication.
- The allowlisted Gmail account signs in; a different Google account is denied.
- The original items, prices, recipes, and sales are intact. A deliberate test
  write persists through an app restart, and cross-origin/missing-origin writes
  are denied. Use synthetic state when testing mutations before cutover.
- HTTP redirects to HTTPS, the certificate validates, the login cookie has Secure,
  HttpOnly and SameSite=Lax, and Sign out removes the session.
- `docker compose ... ps` reports a healthy application with no published ports;
  existing VPS sites still work. Private data, email addresses, and tokens never
  appear in public logs or Git changes.

The app healthcheck checks HTTP availability; verify SQLite integrity and schema
separately. BigQuery Sync remains manual. The base deployment intentionally does
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
