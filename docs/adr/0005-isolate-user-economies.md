# 0005: Isolate private user economies while sharing market observations

Date: 2026-10-18
Status: Accepted

## Context

The owner approved separate private economies for approved Google accounts, with
shared prices and common game data. Existing records belong to the original owner.
The two supported workspaces remain Touch / Blair and Dofus / Tal Kasha.

## Decision

Keep one SQLite operational database per game/server. Add opaque owner keys to
listings and screenshot records, backfilling the reserved `owner` key. Centralize
Google subjects, contact emails, approval state, and notification delivery state
in the default Touch database. An account has the same opaque key in both worlds;
private rows do not require a cross-file foreign key to the account registry.

Require an approved identity before serving any operational page, asset, or API.
Only the isolated OAuth2 Proxy may reach the application; it overwrites identity
headers with the Google subject and verified email. The app checks approval on
every request. Google authentication is open to access requests; it does not grant
access to economy data. The owner controls approval and denial, with no interface
for viewing another account's sales or impersonating another user.

Use an owner-scoped SQLAlchemy Session subclass to apply private-row criteria to
ORM reads, aggregates, relationship loads, and bulk mutations, and validate owners
at flush. Trusted CLI/worker sessions default to the original owner. Raw SQL/Core
connections are privileged maintenance interfaces, never request-selected. Tests
must prove isolation through scalar projections, joins, aliases, nested queries,
known UUIDs, and mutation paths. Keep the owner scope fixed for the session's life.

Share price observations and keep a private contributor key for corrections. Any
approved account may append prices; only the contributor or administrator may
invalidate them. Other contributors' free-text notes are not exposed. Browser
storage and stale-tab submissions are account-scoped. Existing warehouse exports
retain original-owner Sales only and anonymous shared prices, excluding all account
records, contributor keys, and other users' private notes/Sales.

Persist access requests before sending SMTP notifications to the configured owner.
Throttle retry attempts and expose saved/sent states honestly. Email links require
an authenticated administrator and never approve an account directly.

## Consequences

Existing catalog and price queries remain shared and existing reporting algorithms
remain reusable. New report code must use the scoped ORM session; raw SQL in request
services would require explicit review and owner predicates. SQLite serializes
short account admission transactions, suitable for the initial approved-account
scope. There is no cross-device browser preference sync or unapproved guest access.
Accounts, mail secrets, migration backups, and operational state remain private.
