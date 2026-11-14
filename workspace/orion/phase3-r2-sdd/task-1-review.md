# Task 1 review: prices.yaml, loader, combined config hash (4498513..7b75080)

Reviewer: task reviewer (spec + quality). Read via `git show 7b75080:` / `git diff`. Ran checks in a detached worktree
(`.worktrees/rev-t1` @ 7b75080, `npm ci`, now removed). I did not touch the main worktree.

### Spec Compliance

- ✅ **Spec compliant.** The brief plus rulings R2 and R9-R12 are all met.
  - **Every listed file has its hunk.** `share_price.underlying` went into `src/config/sources.ts:81` rather than
    `schema.ts`. That is where the share_price schema lives, so this is not a deviation.
  - **Risk 1, hash integrity: ✅.**
    - **Producer.** `loadAsset` (src/config/load.ts:72-78) is the only place the combined hash
      `sha256(canonicalJson({config, prices: entriesFor(...)}))` is made (load.ts:41-42). It passes `loadPrices(home)`.
    - **Stored/compared paths.** I grepped every `.hash`, `configHash` and `config_hash` use under src. Each one takes
      its hash from `loadAsset`:
      - ingest provenance: `ingest/run.ts:184,287,311,430,559`, then flow.ts:532, apiFlow.ts:204, periodic.ts:77, and
        `provenance/locator.ts:124`;
      - data set: `cli/commands/data.ts:105,120`;
      - observation-proposal approve: `app/proposals.ts:99,113`;
      - agent runs: `agent/run.ts:99,111,158` (configHash input, Ledger disclosed rows, mid-run change check), with
        `loaded`/`reload` from `cli/commands/agent.ts:88,94`;
      - registry: `registry/reconcile.ts:78` feeds `actions.ts:127` and `reconcile.ts:30-36`, and `nightlyReport.ts:52,122-124`
        compares those registry hashes for the report's "config changed" list.
    - **Valuation, tick and signals** read `config` only. They store or compare no hash.
    - **The two config-only callers neither store nor compare the hash.**
      - `agent/tools/write.ts:306`: `parseAssetObject(...)` is validation only and its return value is discarded.
        `filedAgainst` (write.ts:304) holds raw config values, not a hash.
      - Test helpers (`tests/app/tick.test.ts:18`, `tests/agent/context.test.ts:240`, the agentWorld and fetchHarness
        fixtures) build `LoadedAsset` from `parseAssetYaml` for test homes that have no prices.yaml. Those homes hash
        config-only in production too, so they are consistent.
    - **`approveConfig`** (`app/proposals.ts:185`) now validates with `loadPrices(configRoot)`. Its hash is discarded
      there too.
    - **Test.** `tests/config/combinedHash.test.ts:36-63` checks that a fetch and an approved observation store the same
      combined hash, and that it differs from the config-only hash.
  - **Risk 2, prices.yaml content: ✅, no mismatch.** I wrote a script that loads `prices.yaml` through `loadPrices` and
    compares every field against a transcription of the brief's table and task-1-values.md. AERO was compared against
    `assets/aero.yaml` `price_pool` / `price_check_pool` / `usdc_usd_feed`.
    - Fields compared: ref set (17/17, no extra), symbol, chain, `validFrom`, every primary and check
      address/index/quote_ref/usd_feed/feed/seconds/flavor/coin/market_id, tolerance, consecutive and label. Addresses
      were compared case-insensitively.
    - Result: `MISMATCHES: none`.
    - The `validFrom` values follow R2: every eip155 ref is 2025-10-13 except AERO at 2026-09-23; HYPE and LIT are
      2026-10-01; PUMP is 2026-10-12.
    - The R12 extras are present as ruled: cvxCRV/yCRV `i:1, j:0, dx:100/10`; sdCRV `tolerancePct:0, consecutive:1`;
      HYPE check `usd_feed`.
  - **Risk 3, validator strictness: ✅ for every case named in the brief.** I probed `parsePrices` with mutated copies of
    the committed file. Each of these is refused with `<ref>.<field>` named:
    - unknown key on an entry and on a check;
    - unknown kind;
    - a 21-byte or non-hex 0x address, an EVM address used as a Solana vault, a base58 string with `0`, a base58 string
      decoding to 3, 31 or 33 bytes, and a 31-byte v4 pool_id;
    - an unresolved quote_ref, a self-reference, the cycle VVV->DIEM->VVV, and a cycle through a check
      (CRV.check->cvxCRV->CRV);
    - a chain/ref contradiction (8453 ref on eip155:1; solana ref on eip155:1);
    - tolerance 0, consecutive 0, v3_twap seconds 1800, a missing check, and both quotes set.

    The committed file loads (17 entries). Gaps are listed under Minor.
  - **Risk 4, release packaging: ✅.**
    - `scripts/release/pack.sh:56,63` checks for `prices.yaml` and lists it like `schedule.yaml`.
    - `tests/release/pack.test.ts:40,94,157-162` covers the listing and the refusal.
    - In a release, `resolvePaths` sets `configRoot = releaseRoot` whenever `RELEASE` is present (`src/cli/paths.ts:83`),
      and `loadAsset(configRoot, …)` calls `loadPrices(home=configRoot)`. So prices come from the release dir, the
      same root as `assets/`, and never from `ORION_HOME`.
  - **Pins (Step 4).** I compared the pin files' changed lines (`git diff -- tests/assets tests/agent/disclosure.e2e.test.ts`).
    They contain only hash lines, the `parseAssetYaml` -> `loadAsset` switch, removed unused imports, and the re-pin
    comment. None of the 13 old hashes and neither provisional hash (4fcb90ae, 9fffd887) remains anywhere under tests
    or src. Every new pin equals what `loadAsset` gave in my run.
  - **Focused run** (`tests/prices/config.test.ts`, `tests/config/load.test.ts`, `tests/config/combinedHash.test.ts`,
    `tests/release/pack.test.ts`, `--maxWorkers=1`): 4 files, 51/51 passed, no warnings.
- ⚠️ **Cannot verify from the diff:**
  - **Step 2.** The `valid_from` measurement is a controller record (progress.md R2). I checked only that the file
    matches it.
  - **Release dir.** No test exercises an unpacked release dir loading prices.yaml from `configRoot`. Correctness
    follows from `paths.ts:83` plus `loadAsset`. The controller may want to check this on the next stage build.

### Strengths
- One hash producer, and the hash input is normalised (`consecutive` defaulted, entries sorted by ref,
  `config.ts:266`). Writing `consecutive: 1` explicitly or reordering the file does not move a hash.
- The "absent changes nothing" rule (load.ts:41) keeps MINI and every test home on its old hash. load.test.ts:229-245
  pins both sides of it.
- The test `crvUSD moves exactly crv, cvxcrv, sdcrv, ycrv; AERO only aero` (load.test.ts:248-258) edits a real copy
  of the repo's assets and prices. It is a behavioural test, not a mock.
- Refusal messages are precise and collected. Several issues are reported at once, and the cycle message prints the
  path.
- Base58 is validated by decoded length (`base58ByteLength`, config.ts:21-33), not only by regex.
- combinedHash.test.ts proves R10 through the real fetch and approve paths against the test DB.

### Issues

#### Critical (Must Fix)
None.

#### Important (Should Fix)
None.

#### Minor (Nice to Have)
1. **`src/prices/config.ts:176-179`: a check's kind is not checked against any chain.** A `meteora_dlmm` or
   `solana_vaults` check on an eip155 ref is accepted (I probed `CRV.check = meteora_dlmm`). The same goes for a
   `hyperliquid_candle` check on an EVM ref. The header says a check "is read on its ref's chain", but nothing enforces
   it, and Task 2/3's per-chain dispatch (R4) will meet such a check at runtime instead of at load. Fix: apply
   `primaryFits` to the check, using the ref's namespace chain (`eip155:N` / solana / hyperliquid). This is the
   check-side equivalent of "a primary not read on chain".
2. **`config.ts:146`: `chain: lighter` accepts any eip155 ref.** I probed with an eip155:56 ref. The only Lighter ref
   is on eip155:1, so restrict `lighter` to `eip155:1` unless a ruling says otherwise.
3. **`config.ts:96`: `valid_from` is checked by regex only.** `2025-13-45` loads. Add a `Date.parse` round-trip check.
   The writer will compute hours from this value.
4. **`config.ts:39`: the Solana ref key's mint is only checked as 32-44 base58 characters, not decoded to 32 bytes.**
   Vault and pair addresses are decoded. Use `base58ByteLength(mint) === 32` in `SOLANA_REF` matching for consistency.
5. **`config.ts:227-229`: `loadPrices` silently returns an empty map when the file is missing, even at a release root.**
   pack.sh refuses a tree without prices.yaml, so a packed release is safe. But an `ORION_CONFIG_ROOT` override, or a
   hand-assembled root, would silently fall back to config-only hashes, the exact R9 failure mode. Consider refusing
   when `readRelease(root) !== null` and the file is absent. Alternatively, add a prices.yaml row to
   `asset validate` / daemon start-up (the report's own carried concern).
6. **`config.ts:81-87,178`: `CheckSchema` is built with `as unknown as [...]` and destructured through a cast.** This
   loses static typing of check fields: a typo'd field name in this file would compile. It is acceptable for now. A
   typed helper (`withCheck(shape)`) per kind would keep the inference.
7. **No test pins that a release root, rather than `ORION_HOME`, supplies prices.yaml.** A `resolvePaths` and
   `loadAsset` test over a temp dir with `RELEASE` would cover it; `tests/cli/paths` likely has the fixture.

### Assessment

**Task quality:** Approved

**Reasoning:** I found no mismatch between prices.yaml and the binding table, task-1-values.md and R2. Every stored or
compared asset hash goes through `loadAsset`'s combined hash. The two config-only callers discard it. The validator
refuses every case the brief names, by field. The open items are validator gaps that no current entry triggers, plus
one defensive check on releases, all Minor.
