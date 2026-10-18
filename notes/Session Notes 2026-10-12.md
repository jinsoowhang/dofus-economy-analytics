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
