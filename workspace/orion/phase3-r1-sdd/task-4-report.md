# Task 4 report: `schedule.unlocks_next_year` (disclosure rung)

Status: DONE. Commit 69caa3f `feat(ingest): schedule.unlocks_next_year, a cited unlock schedule (disclosure rung)` on
feat/phase3-third-party (parent e88130f). Step 1 (PUMP citation) skipped per ruling R5; fixtures use citations.md verbatim.

## What
- `src/ingest/adapters/schedule.ts` (new): adapter `schedule.unlocks_next_year`, `needsRpc: false`, reads nothing.
  Params are strict: `citation {url, quote}` and `schedules[{label, tokens, tranches|linear}]`. Unknown keys are refused at every level.
  The url must be http(s). The quote must be non-empty and at most 500 chars. tokens must be finite and > 0. Exactly one of tranches/linear.
  Dates must be real YYYY-MM-DD dates. Tranches take every_months 1..12 and count 1..120. linear.years must be > 0 and <= 50.
  Value = tokens due in (now, now+365d]. For tranches: tokens/count per tranche date, with dates from `addMonthsClamped`, as lit.ts does.
  For linear: (tokens/years) x overlap/365d, clamped to [start, start + years x 365d].
  The level it returns has `source 'api'`, detail `<label> <x>M, ...; cited <url>`, and `citation`. `run` re-validates and throws, so it never returns a silent 0. paramsDoc is set.
- `src/ingest/adapters/dates.ts` (new): `addMonthsClamped`, `isoDate`, `intIn` moved out of lit.ts unchanged. lit.ts now
  imports them, so `lit.unlocks_next_year` behaves the same (its tests pass unchanged).
- `src/ingest/types.ts`: the level `SourceValue` gains `citation?: { url; quote }`.
- `src/ingest/run.ts` (level path): computes the provenance once and passes `citationUrl`/`quotedText` only when the reading has a citation, so other rows get no new keys.
  A `disclosed`+`disclosure` reading with no citation url now fails the read ("a disclosure-rung reading needs its citation; nothing was written"). Before this, it threw `citation_required` out of insertObservation.
- `src/report/sourceTypes.ts`: `'schedule.unlocks_next_year': 'disclosure'`.
- `src/provenance/locator.ts` `methodOfSource`: an adapter on the `disclosure` rung returns `disclosed`. Every other adapter stays `measured`, and a test pins this for all registered adapters.
- `src/provenance/origin.ts` `originOf`: `disclosed` with a string `locator.adapter` now reads back `api` (this matches the reading's stamp, like a constant).
  Without it the origin guard would refuse the row (disclosed+disclosure read back `manual`). Hand-entered disclosures have no `adapter` in their locator (`disclosedProvenance`), so they stay `manual`.
- `src/ingest/adapters/registry.ts`: registers `scheduleAdapters`.
- `tools/sources-register/generate.ts`: `ADAPTER_ENDPOINTS['schedule.unlocks_next_year'] = [http(citation.url)]`, the closest existing Endpoint shape. A missing url gives '', which `sourceKey` refuses.
  No asset uses the adapter, so `docs/ops/sources-register.md` is unchanged and still current (the test passes).
- Levels job: needed no code change. `runLevels` runs fetchAsset as a dry run, and `latest_levels` has no rung CHECK. A test proves a watched disclosure-rung level lands there with `source_type 'disclosure'`, `source 'api'` and no block.

## Tests (TDD)
- RED: `npx vitest run tests/ingest/scheduleUnlocks.test.ts --maxWorkers=1` failed 22 of 22 (`unknown adapter: schedule.unlocks_next_year`; tsc: `citation` not on the level type).
- GREEN: same file 22/22. The focused set (scheduleUnlocks, tests/provenance/*, sourcesRegister, adapters.lit, originGuard,
  tests/levels/*, run) passed 184/184 over 10 files.
- Full suite at `--maxWorkers=2`: 143 files, 1735/1735 passed (baseline 1712 + 22 new + 1 register test). No failures, so nothing needed a rerun.
  `npm run typecheck` is clean.
- Covered: LIT 2026-11-12T00:46:15Z gives 500e6/36x10 (to 1e-6). PUMP 2026-11-12T00:46:41Z gives exactly 82.5e9. Tranche edges (on now is out, on now+365d is in).
  Linear ends inside the window, starts inside the window, before start = 0, wholly past = 0, month-end clamp. Every validateParams refusal is checked, plus a load-time refusal through parseAssetYaml.
  The written row has method disclosed, source_type disclosure, chain null, citation_url and quoted_text set, response_digest null, locator.adapter, and reads back `api`.
  A reading missing its citation fails the read and writes nothing. latest_levels gets the row via runLevels. The register lists the citation url.
- `tests/provenance/adapterOrigins.test.ts` gains a sample for the new adapter, and `mismatches` now uses the writer's real method (`methodOfSource`) instead of a hard-coded `measured`.
  This changes nothing for the existing adapters, which are all measured.
- No asset hash pin moved (no YAML touched; full suite green).

## Self-review / concerns
1. **Brief value "182 days' worth" does not match the brief's own rule.** The linear test uses start 2026-07-12, years 3, now 2029-01-12.
   With the interface's clamp of start + 3 x 365 d, the vest ends on 2029-07-11 (2028 is a leap year), which is 180 days after now.
   Calendar end 2029-07-12 would give 181. Neither gives 182. I implemented the stated rule and the test pins 180 days, with the derivation asserted inside the test.
   If 182 was intended, the rule needs to change, so the controller should decide.
2. **originOf changed for one new case:** a disclosed row with `locator.adapter` now reads back `api`. Rows that exist today are not affected, because no disclosure row carries an adapter in its locator.
   Still, this is a reader-side change the reviewer should look at.
3. **For Task 6:** once LIT and PUMP use the adapter, the register will list `x.com` and `blockworks.com` as sources, and each needs a TERMS entry (kind: x.com = Lighter's own post, first party; blockworks.com = third party, compiled by Blockworks).
   Generation fails until both are added. The locator stores the adapter params, citation included, which duplicates the citation columns. This is harmless.
4. The PUMP quote is 451 chars, under the 500 cap. A longer future quote will be refused at load.

## Files
Created: src/ingest/adapters/schedule.ts, src/ingest/adapters/dates.ts, tests/ingest/scheduleUnlocks.test.ts.
Modified: src/ingest/adapters/lit.ts, src/ingest/adapters/registry.ts, src/ingest/run.ts, src/ingest/types.ts,
src/provenance/locator.ts, src/provenance/origin.ts, src/report/sourceTypes.ts, tools/sources-register/generate.ts,
tests/provenance/adapterOrigins.test.ts, tests/tools/sourcesRegister.test.ts.
