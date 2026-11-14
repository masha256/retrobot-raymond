# Task 8 re-review, fix round 1 (c5e6172..3aca04e)

### Finding Verdicts

1. **IMPORTANT, R30: derived rows stale after an interrupted --yes / a 0 -> 0 day.** ADDRESSED.
   src/db/reprice.ts:297-305 now seeds `repricedDays` from every active flow row in `all` that already carries
   `locator.repriced`. reprice.ts:354 calls `markDay` for every row this run prices before the unchanged check, so
   unchanged and 0 -> 0 days count. Refused and skipped rows `continue` earlier and are never marked. `touches()`
   (reprice.ts:421-428) reads `repricedDays`. The derived write is still guarded by `v === d.value` → unchanged
   (reprice.ts:444-447), so a further --yes stays a no-op.
   Check run: I copied the reviewer's t8-review-probe.test.ts into a scratch worktree at 3aca04e and added assertions
   that the first run throws `boom` and that the third --yes changes nothing (`exportFile` null, `days` 0,
   `recomputed` 0, `repriced` 0, full observations snapshot equal). Result: 2/2 pass.
   - Rerun recomputes usage_index: recomputed 2, unchanged 1.
   - Stored values now equal burnMomentum on the final flows: [118.7128, 77.9762, 80.5186]. The 2026-10-05 day-end
     row is 77.976. Before the fix it stayed at 7.67 against an expected 77.98.
   - Third run: export null, usage_index recomputed 0 / unchanged 3.
   The in-repo regression test `R30: a day that failed mid-apply...` (tests/db/reprice.test.ts:378-418) covers the same
   case and also checks burn_rate.
2. **MINOR: rung from venueOfMethod(...).rung.** ADDRESSED. src/db/priceLevels.ts:145-149 has `sourceType: venue.rung`
   and `firstParty = venue.rung === 'first_party_api'`. `kindOfSource` (:79-84) stays only to map the label to a
   method kind, which venueOfMethod needs.
3. **MINOR: first solana.token_supply reading ignores rejected rows.** ADDRESSED. reprice.ts:229 adds
   `AND status <> 'rejected'`. Test `PUMP: a rejected supply reading does not move the history/chain split` is at
   tests/db/reprice.test.ts:421-436.
4. **MINOR: tautological `yes ? 1 : 1`.** ADDRESSED. tests/db/reprice.test.ts:202 is now `toBe(1)`. :204-206 adds a
   third call that asserts `repriced 0, unchanged 1` with the gap row still refused.
5. **MINOR: non-zero exit on refused rows.** ADDRESSED. src/cli/commands/data.ts:41 defines `REPRICE_REFUSED_EXIT = 3`.
   :307 sets it after `output(...)`, for both the dry run and --yes; errors still exit 1 through `guarded`. The JSON
   output is unchanged. CLI help and docs/ops/deploy.md:460-461 document it. tests/cli/reprice.cli.test.ts:78/90/92-94
   cover dry run, --yes and --json exiting 3, and `--from 2026-10-05` exiting 0.

R31 (6 h staleness refusal) was accepted; no change was expected and none was made.

### New Breakage in the Fix Diff

None.
- Minor, non-blocking: priceLevels.ts:145-147 now takes the rung from the venue for an unknown `first_party:<x>`
  label. Such a label now falls through to `contract_state` with no `api` origin key; before, `startsWith` made it
  first_party. No such label exists today (only hyperliquid and lighter), and this is the consistency R-item 2 asked for.

### Checks run

Scratch worktree `git worktree add --detach .worktrees/rev-t8b 3aca04e` + `npm ci`, since removed:
- Adapted probe `tests/db/reprice-rrprobe.test.ts`: 2 passed.
- `npx vitest run tests/db/reprice* tests/db/priceLevels* tests/cli/reprice* --maxWorkers=1`: 4 files (probe included),
  20 tests passed.

### Out-of-Scope Observations

None.

### Verdict

**Fix round:** All findings addressed, no new Critical/Important breakage.
