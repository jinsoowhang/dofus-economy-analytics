# Session Notes 2026-10-11

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
