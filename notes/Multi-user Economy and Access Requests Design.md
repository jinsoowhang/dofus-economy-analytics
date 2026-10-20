# Multi-user economy and access requests

Approved October 18, 2026. This supersedes the earlier single-owner/shared-database
hosting boundary. Preserve the current two game/server databases and their common
catalog, recipes, icons, and price observations. Do not copy catalogs per user.

## Identity and admission

Google authenticates everyone through the existing isolated OAuth2 Proxy. The
application receives the gateway's overwritten Google subject/email headers and
checks account approval on every request. Use Google subject as the stable identity;
email is a contact/display field. Bootstrap one configured owner/admin account,
binding its first verified Google subject to the existing owner key. No owner email
or credential belongs in tracked source or public fixtures.

Persist accounts and invitation delivery state in the default Touch database only,
including when the user selects PC. Other world databases use the same schema but
are not independent account registries. Accounts start pending; the owner sees
pending requests and can approve or deny them through same-origin POST forms.
Pending/denied users cannot access catalog, assets, APIs, or economy data. Do not
provide administrator impersonation or other users' Sales/report pages.

First authenticated sign-in creates one durable request and queues an email to the
configured owner. A saved request and an email delivered to the mail server are
different states: only show “Invite request has been sent” after SMTP acceptance.
When mail is unavailable, say the request was saved and notification is pending.
Keep a durable retry state, throttle attempts, and provide an owner retry action.
Email links open the authenticated approvals page; no email link directly approves
an account. SMTP settings and credentials remain private runtime configuration.

## Ownership and shared prices

Add an opaque owner key to Sales and local screenshot capture records. Backfill
existing rows to the reserved owner key without changing IDs, amounts, timestamps,
observations, or cost snapshots. All new request sessions carry an immutable owner
scope. Enforce ownership for ORM selects (including aggregates, aliases, joins,
subqueries, and relationship loads), updates/deletes, and ORM flushes. Query scoping
belongs at the session boundary so existing dashboards and recipe projections
cannot accidentally count everyone. Protect this choice with cross-account tests.
Trusted local CLI/worker sessions remain explicitly scoped to the original owner;
there is no unscoped web session or administrator Sales bypass.

Price observations are common to the selected game/server. Record an internal
contributor key for correction/audit purposes without exposing account identity.
Only a contributor or administrator can invalidate that contributor's observations;
any approved user can append a newer market observation. Free-text price notes and
invalidation reasons are private to their contributor/admin. Listing/relisting and
screenshot price corrections continue publishing anonymous price observations;
completed sales also contribute their actual price while preserving listing starts
and existing linked observations. Preserve exact whole-kama lot totals.

Calculator carts, selections, checklist progress, and remembered world selection
are isolated by account in the browser. Pin requests to their originating account
so an old tab cannot submit its private state under a different signed-in account.
Accounts do not share browser-local state. Cross-device state sync is out of scope.

## Analytics and deployment

Keep user identities, approvals, email state, and contributor keys out of analytical
snapshots. Existing manually published Sales analytics remain restricted to the
original owner; do not silently export other users' private sales. Only the owner
can use the web BigQuery controls. Shared prices remain anonymous in snapshots.

Rehearse migrations against fresh integrity-checked backups of both databases and
verify all preexisting fields unchanged. Run focused ownership, admission, SMTP,
workspace, Sales/reporting tests and the complete repository check. Deploy first
against disposable state; validate proxy identity headers, approval gates, assets,
origin controls, and accounts before transferring live state. Stop local writers
before final online backups. After cutover the VPS is the sole writer, including
manual screenshot reconciliation. Email delivery and actual Google sign-in must
be verified before calling the full workflow complete.

## Success criteria

- Existing 827 Touch sales and all other legacy rows belong only to the owner.
- Two approved users cannot read, count, edit, delete, or reopen each other's rows,
  even using known UUIDs; administrators receive the same private-data restriction.
- Both users see shared latest prices in their own world and never another world's
  data; contributors' identity/free-text personal notes stay private.
- A new Google account sees a truthful pending screen and generates one request;
  repeated refreshes do not resend accepted mail or bypass approval.
- Owner can approve/deny requests, retry notification delivery, and continue using
  their own economy. Other accounts cannot access approval/export controls.
- Both world migrations preserve legacy data, authentication fails closed, browser
  account switches do not leak private state, and full verification passes.
