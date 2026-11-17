"""Seed the Linear 'orion' project with phases (parents) and steps (sub-issues). Idempotent by title."""
import json, os, lmcp

OUT = os.path.join(os.path.dirname(__file__), 'issues.json')
done = json.load(open(OUT)) if os.path.exists(OUT) else {}
SPEC3 = 'docs/superpowers/specs/2026-11-09-orion-phase3-third-party-removal-design.md'
ROAD = 'docs/superpowers/specs/2026-10-28-orion-coinrevs-core-roadmap.md'
B = ['Blocked']

# (key, title, state, labels, description, parent_key)
T = [
 ('P1', 'Phase 1: remove the valuation layer', 'Done', [], f'Price targets, drivers, signals and assumption sets removed; no reported number changed. Spec: `docs/superpowers/specs/2026-10-28-orion-phase1-remove-valuation-design.md`. Roadmap: `{ROAD}`.', None),
 ('P15', 'Phase 1.5: platform (LAN server, Postgres, daemon)', 'Done', [], 'venus server, Postgres 18, one `orion daemon` per env with asset registry, tagged releases + SSH deploy, snapshot publisher. Staging live 2026-11-04; prod cut over 2026-11-07 (`orion-2026.11.05.1`).', None),
 ('P2', 'Phase 2: data strategy + income statement v2', 'Done', [], 'Source ladder, provenance on every observation, income statement v2, v1 retired. Closed: prod `orion-2026.11.11.1` = main 1de531d (2026-11-12). Record: `docs/superpowers/notes/2026-11-04-orion-phase2-followups.md`, "Phase 2 closed".', None),
 ('PF', 'Platform follow-ups (Phase 1.5 carry-overs)', 'Todo', [], 'Leftovers from the platform/cutover work tracked in `workspace/orion/phase1.5-mike-steps.md`.', None),
 ('PF1', 'Backup restore drill (spec 10.3)', 'Todo', B, 'Prove a pgBackRest restore of prod end to end. Needs Mike on venus (sudo). Backups themselves verified healthy 2026-11-11.', 'PF'),
 ('PF2', 'Retire the paused legacy Hermes orion-<asset> cron jobs + uranus fallback checkout', 'Todo', B, 'The 13 `orion-<asset>` jobs and `orion-disclosure-watch` are paused as the week-1 cutover fallback; `/home/hermes/git/orion` is pinned on 33efeea for it. Remove them and update the local checkout. Needs Mike\'s go.', 'PF'),
 ('P3', 'Phase 3: remove DefiLlama and CoinGecko from live code', 'In Progress', [], f'One plan per release, each written just before its build from fresh measurements; every release goes stage -> one soak nightly -> prod on Mike\'s go, proven byte-identical for untouched assets on a read-only prod copy. Spec (D1-D11 approved): `{SPEC3}` §5. After R3 nothing CoinGecko-derived is stored; after R7 no third-party figure is published.', None),
 ('R0', 'R0: CAKE pending-burn supply fix', 'Done', [], 'Shipped `orion-2026.11.10.1` (prod 2026-11-11). CAKE total supply nets dead + burner + masterchef_v2.', 'P3'),
 ('R1', 'R0b + R1: remote backfill/purge verbs; drop DefiLlama cross-checks and display series', 'Done', [], 'Shipped `orion-2026.11.12.1` = main 8f50ac6 (migration 7) on stage and prod; orphan series purged on both; reports byte-identical.', 'P3'),
 ('R2', 'R2: price swap (CoinGecko -> on-chain/first-party hourly prices)', 'In Progress', [], 'Built, proven (Mike signed the table 2026-11-15), tagged `orion-2026.11.15.1` = main 02f39e3. orion-host.sh SELF-CHECK 57/0 and RPC prereq done (2026-11-17). Rollout per deploy.md "R2" block. Plan: `docs/superpowers/plans/2026-11-13-orion-phase3-r2-price-swap.md`; ledger `workspace/orion/phase3-r2-sdd/`.', 'P3'),
 ('R2a', 'R2 rollout: deploy orion-2026.11.15.1 to staging', 'Todo', B, 'After stage\'s nightly window (from 04:45Z). Needs Mike\'s "deploy stage". Then release block steps (backfill-prices ~3 h, reprice, rebuild-price-levels, purges) on stage.', 'R2'),
 ('R2b', 'R2 rollout: staging soak (one scheduled nightly) + soak report', 'Todo', [], 'Resume soak cron with the new known-queue line; check stage vs prod diffs against `tools/phase3-proof/r2-allowlist.json`.', 'R2'),
 ('R2c', 'R2 rollout: prod deploy + prod --yes steps', 'Todo', B, '`deploy.sh prod orion-2026.11.15.1` through the soak gate, then reprice / rebuild-price-levels / purges with `--yes` - each on Mike\'s go after the dry runs. Any refused row is his decision.', 'R2'),
 ('R2d', 'Decide: price-check gaps (HYPE same-venue check, sdCRV no independent check)', 'Todo', B, 'HYPE primary = Hyperliquid spot candle, check = Hyperliquid perp (a venue-wide fault moves both): second venue needed? sdCRV check is a 0.3-1.0 CRV sanity band only (second pool ~$430 deep). Mike\'s call. Source: R2 followups note, "Open items for Mike".', 'R2'),
 ('R3', 'R3: circulating supply on chain', 'Todo', [], f'§3.2 per asset (total minus staked/reserve balances via `chain.view_sum`). Moves market cap and every yield on market cap; per-asset before/after. After R3 nothing CoinGecko-derived is stored. Steps: plan -> Mike approval -> build -> proof -> stage -> prod.', 'P3'),
 ('R4', 'R4: AERO revenue on chain (pool_scan pilot)', 'Todo', [], 'Replace DefiLlama `flow_usd.fees` with `pool_scan` over `factory.allPools()` on 7 chains (PoolTape/CLPoolTape accumulators + VotingRewardsManager incentives). History from the merger (2026-10-21/22); 272 DefiLlama rows deleted; 91-day window fills ~2027-01-21. Scoping: `workspace/orion/aero-scoping/`.', 'P3'),
 ('R5', 'R5: HYPE revenue on chain/first-party', 'Todo', [], 'Revenue = Assistance Fund buys / 0.99 from Hyperliquid `userFills` + reserve yield; two-path check vs the fund\'s HYPE balance change. 289 + 400 DefiLlama rows deleted. Fills API look-back to be measured.', 'P3'),
 ('R6', 'R6: PUMP revenue from Solana fee accounts', 'Todo', [], 'Bonding-curve and PumpSwap fee accounts as `balance_delta` reads; creator/LP fees as cost lines where measurable. Burn side drops its DefiLlama history param; unlocks as a cited schedule. 502 DefiLlama rows deleted.', 'P3'),
 ('R7', 'R7: CRV vote incentives (event_sum)', 'Todo', [], 'Replace llama.box `vote_incentive_run_rate_usd` with `event_sum` over curated incentive markets (Votemarket v1/v2, others from scoping), coverage stated. Largest single value at stake (7.48 of 12.65 $M/yr holder flow). After R7 no third-party figure is published.', 'P3'),
 ('R8', 'R8: retire third-party sources', 'Todo', [], 'Delete the DefiLlama/CoinGecko source types, add a hosts grep test, finalize `docs/ops/sources-register.md`. LIT/PUMP third_party unlock rows go here (Mike\'s R27 pick).', 'P3'),
 ('P5', 'Phase 5: snapshot export for the coinrevs site', 'Todo', [], f'Versioned export pushed to a git repo the site pulls: per-token figures for the site\'s live-price layer, income statement, holder flow by bucket, net holder yield after dilution, supply, provenance and change log. May ship before R8 only for assets whose exported fields carry no third_party data. Roadmap: `{ROAD}`.', None),
 ('P5a', 'Phase 5: write the export spec', 'Todo', [], 'Snapshot format/versioning, field list, provenance shape, publish cadence. Include Phase 2 review item M6 (`levels` body sourceType/locator keys).', 'P5'),
 ('P5b', 'Phase 5: Mike\'s decisions on the export spec', 'Todo', B, 'Decision list in the spec; recorded in its Status line.', 'P5'),
 ('P5c', 'Phase 5: write the implementation plan', 'Todo', [], 'From the approved spec.', 'P5'),
 ('P5d', 'Phase 5: build + proof', 'Todo', [], 'Subagent-driven execution; proof on a read-only prod copy.', 'P5'),
 ('P5e', 'Phase 5: release (stage -> soak -> prod)', 'Todo', B, 'Prod deploy on Mike\'s go.', 'P5'),
 ('P4', 'Phase 4: internal comparison tool', 'Todo', [], 'Separate repo, internal only: reads Orion read-only, pulls other platforms, reports divergences with causes. Its third-party figures are never republished on the site without a licence. Runs after Phases 3 and 5.', None),
 ('P4a', 'Phase 4: write the comparison-tool spec', 'Todo', [], 'Sources to compare, divergence rules, where it runs, how it reads Orion read-only.', 'P4'),
 ('P4b', 'Phase 4: Mike\'s decisions on the spec', 'Todo', B, 'Decision list in the spec.', 'P4'),
 ('P4c', 'Phase 4: plan + build', 'Todo', [], 'New repo; plan from the approved spec, then build.', 'P4'),
 ('P4d', 'Phase 4: first comparison run + review', 'Todo', B, 'Run against prod read-only; Mike reviews the divergence report.', 'P4'),
]

lmcp.init()
for key, title, state, labels, desc, parent in T:
    if key in done:
        continue
    args = dict(title=title, team='RET', project='orion', state=state, description=desc)
    if labels:
        args['labels'] = labels
    if parent:
        args['parentId'] = done[parent]['identifier']
    r = lmcp.call('save_issue', **args)
    done[key] = {'identifier': r.get('id'), 'uuid': r.get('uuid'), 'url': r.get('url'), 'title': title, 'state': state, 'labels': labels}
    json.dump(done, open(OUT, 'w'), indent=1)
    print(key, r.get('id'), state, labels)
print(len(done), 'of', len(T))
