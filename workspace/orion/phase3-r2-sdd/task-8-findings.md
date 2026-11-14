# Task 8 findings (review of 13ece08) — binding rulings
1. IMPORTANT (fix): src/db/reprice.ts:358-360 + :410-417 — touches() counts only flow days whose value changes in THIS run, so after an interrupted --yes (or a zero-burn 0->0 day) derived rows over those days are never recomputed (reviewer reproduced usage_index staying 7.67 vs 77.98). Ruling R30: recompute every stored derived row in the asset's range whose inputs include a repriced-or-marked flow day, and write only when the value differs (a second --yes stays a no-op). Use the reviewer's probe as the regression test: t8-review-probe.test.ts in this dir (adapt it).
2. MINOR (fix, cheap): priceLevels.ts:79-84, :143-146 — derive the rung from venueOfMethod(...).rung instead of re-deriving it.
3. MINOR (fix, cheap): reprice.ts:227 — the first solana.token_supply reading must ignore rejected rows (status <> 'rejected'), matching the adapter.
4. MINOR (fix, cheap): tests/db/reprice.test.ts:202 tautological `yes ? 1 : 1`: assert the post-write state (unchanged on a third call).
5. MINOR (fix, cheap): `data reprice` exits non-zero (e.g. 3) when any row is refused, so an operator/script can't miss it; JSON keeps `refused`.
Accepted (Ruling R31): rebuild-price-levels refuses a row whose newest price is more than 6 h older than its observed_at - 1h (same staleness rule as the view).
Deferred (ledger): reprice.ts:259 a log_scan row with hourly_amounts but amount null is refused as 'no token amounts' (none known); CLI tests written after code.
