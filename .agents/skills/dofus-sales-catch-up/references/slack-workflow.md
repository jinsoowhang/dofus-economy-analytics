# Today's Slack sales and repeated runs

## Select uploads by date and time

Resolve the current instant and today's calendar date in `America/Los_Angeles`.
Find `#dofus-touch` in the connected Duchess Nikki workspace and read its history;
the channel may be private, so a public search returning nothing is not evidence
that no uploads exist. Paginate until the start of today, selecting the owner's
image attachments whose message timestamps fall within today's local midnight
through the current instant. Inspect thread replies when they contain additional
owner images. Retain each image-bearing message's own timestamp and its parent
timestamp when different. Explicit dates or sources from the user take precedence.

Read all eligible messages, not only the newest two or messages later than the
last run. A later attachment on an earlier message or an unresolved earlier upload
must not disappear behind a timestamp cutoff. Process new message groups oldest
first, keeping attachment/screen order and inspecting visible overlap. The message
timestamp supplies `observed_at` unless an explicit reporting date changes the
interval; upload time is a reporting proxy, not a measured individual sale time.
If Slack access is unavailable, explain the missing access; do not silently switch
to Downloads and claim to have checked today's channel.

## Check reconciliation per attachment

Download into ignored private evidence storage and compute SHA-256. Compare each
attachment against all prior private manual audits and the existing SQLite
`sale_capture_files` joined to `sale_capture_batches` on `capture_batch_id`.
Retain workspace/channel, message timestamp, provider file ID, image hash, and
archived path. Use exact timestamp values, not rounded minutes or just the date.

- A successfully verified committed audit covering an attachment, or a committed
  capture covering it, establishes processing. Match file ID within its provider
  context or identical image hash. Reuploads with a different file ID but the same
  bytes are already processed. Timestamp orders reports; it is not the sole replay
  key, and equal item names/prices never establish replay.
- Legacy committed manual audits are valid checkpoints: read their `slack_source`,
  `evidence[].provider_file_id`, `evidence[].sha256`, and saved-state `verification`.
  Do not require a new audit schema before recognizing earlier work. If a known
  file ID now has different bytes, review the change rather than silently skipping
  or replaying it.
- Planned, rehearsed, failed, or uncertain audits/captures do not establish success.
  Inspect saved SQLite and recover an interrupted commit before considering a retry.
  Preserve blocked attachments for review; do not mark them processed or advance
  coverage past them merely because a later upload succeeded.
- Skip processed attachments individually, allowing a message with both old and
  new files to contribute only its new files. Compare new views with relevant
  archived screenshots to remove only visually established previously processed
  scroll overlap. Do not infer overlap from repeated sales alone.

If no unprocessed screenshots remain, report that today's uploads are already
reconciled (or that none were posted), with the last committed checkpoint. Make no
Sales changes and do not create a fictitious new reporting checkpoint.

## Same-day assignment and durable progress

Use the last actual reporting checkpoint to determine the interval. When the new
report's Pacific date equals the preceding report's date, assign new matched sales
to that same date at the new message's aware timestamp with source `manual`. Validate
that every assigned timestamp is at or after its listing start and no later than
the evidence/current instant. Preserve real prices and calculate historical costs
at that timestamp. Do not call `allocate_sales.py` for this case, fabricate a prior
date to satisfy it, allocate tomorrow, or refit weekday trends on partial-day checks.
For a later report date, use the existing next-day interval and allocation helper.
Keep distinct reporting checkpoints separate even when processed in one invocation.

Use a unique audit/evidence path such as
`data/reports/manual-screenshot-sales-YYYY-MM-DD-HHMMSSffffffZ.json`, with the suffix
from the run's UTC start time. Keep the new attachment identities, skipped attachment
reasons, evidence/report timestamps, rows, listing assignments, and verification
in that audit. Record successfully handled out-of-scope rows as reviewed exclusions
for the current approved scope, so unchanged resources do not retry on every run.
Only mark the selected attachments committed after the atomic Sales write and
saved-state verification, or a verified no-op containing only reviewed exclusions.
Recheck audit/capture processing state as well as evidence and listing state before
writing. Preserve earlier audits, and recover uncertain writes instead of replaying.
Manual reconciliation uses the existing private audits; do not manufacture worker
capture records or change its confirmation gates. Keep Slack originals available.
