# LIT: Lighter's 50% of Robinhood-instance fees: where it goes, and a first-party revenue source

Scoped 2026-10-23 (read only). Tags: **[M]** = measured by me today from the source named; **[C]** = claimed (Q3 call
transcript, DefiLlama reference figures given in the brief, docs). k = $ thousands. Months are UTC calendar months; "Oct"
= Oct 1-22 for Lighter API series (the API's last complete day is 2026-10-22), Oct 1-23 for the DefiLlama figures.

## TL;DR
1. **The RH share is not bought back (as of 2026-10-23).** Lighter RH is a separate exchange (`api.rh.lighter.xyz`, on
   Robinhood Chain 4663). Its fee account (RH L2 account 0) has **never traded** and is accumulating USDG: collateral
   **$3.487M [M]** ≈ 100% of RH fees to date ($3.80M [M]) less one **$320,000 USDG** outflow on 2026-08-25 [M]. Lighter's
   own buyback series shows 0 on RH and ≈100% of **Core** revenue only. The 100% buyback claim [C] holds for Core; for RH
   the share is held, not bought back. Robinhood's 50% is not split out on L2 either (account 0 holds both halves).
2. **A first-party source exists:** `GET /api/v1/exchangeMetrics?period=all&kind={maker_fee|taker_fee|transfer_fee|withdraw_fee}`
   on **both** hosts (daily, USD, keyless). Lighter's own stats page (app.lighter.xyz/stats) computes "Revenue" as
   Core + **0.5 × RH**, with the 0.5 hard-coded in its frontend. DefiLlama's lighter adapters read these same endpoints.
   It reproduces the call: Q3 Core $7.54M + 0.5 × RH $2.23M = **$8.65M, 87.1% Core [M]** vs **$8.5M, 87% [C]**.

## (1) Where Lighter's 50% of RH fees goes

### The instance
- Lighter RH is a separate exchange with its own contracts, sequencer and accounts: docs.lighter.xyz/developers/robinhood-chain/overview,
  apidocs.lighter.xyz/docs/lighter-rh, docs.robinhood.com/chain/lighter-domains. API `https://api.rh.lighter.xyz/api/v1`.
  Lighter contract on Robinhood Chain: `0x94bAB9693Ba2f6358507eFfcbd372b0660AFfF9d`. Collateral: USDG
  `0x5fc5360D0400a0Fd4f2af552ADD042D716F1d168`, 6 decimals [C docs, M on chain]. The contract holds **106.37M USDG [M]**.
- RH markets [M `rh:/orderBookDetails`]: 63 perps (LIT is perp market 5) and 27 spot markets, all `*/USDG` stock tokens plus
  ETH/USDG. **There is no LIT spot market on RH**, so the RH treasury can't buy LIT on RH the way Core does (Core market 2049).

### RH fee account = RH L2 account 0 [M]
- `rh:/account?by=index&value=0` (2026-10-23): `collateral` **3,486,528.33 USDG**; small stock-token balances (spot fees
  collected in the base asset); **no positions**; `total_order_count` 0.
- `rh:/trades?account_index=0`: **empty: no buys, no sells, ever.**
- `rh:/pnl?by=index&value=0&resolution=1d` (cumulative fields; I took day-to-day differences):

  | month | trade_pnl Δ (= fees credited) | trade_spot_pnl Δ | outflow Δ |
  |---|---|---|---|
  | Jul | 9.2k | 0.0k | 0 |
  | Aug | 459.9k | 2.4k | **320.0k** (lands in the 2026-08-26 row) |
  | Sep | 1,633.5k | 49.1k | 0 |
  | Oct (to 10-23 partial) | 1,704.0k | 5.3k | 0 |

  Cumulative trade_pnl was $3.807M and trade_spot_pnl $0.057M on 2026-10-23. Less the $0.32M outflow, that is $3.54M,
  against $3.49M of collateral: **the account holds ~all RH fees (both halves), minus that one outflow.**
- The outflow on chain [M, Alchemy Robinhood RPC, `alchemy_getAssetTransfers` from the Lighter contract]: **320,000 USDG**
  Lighter contract → EOA `0xac71ec137c892d02d531e48ceb1d060f9c9ac357`, 2026-08-25 20:09 UTC, tx
  `0x99b52291852aec46568b861386103a409a403cab69b5130485f23ff1784f5ebe` (submitted by `0xe3d9…f1ac5` to `0xa918…088f`,
  selector `0xe3a49048`). The match is by exact amount and date, not by an account link (the account's tx list,
  `accountTxs`, returns 403 keyless). The recipient still holds **315,008.94 USDG [M]**. It has no Lighter RH account
  ("account not found"), Ethereum nonce 38, RH nonce 25,570, and has sent out only ~$5k. Its owner is **unknown**
  (Robinhood's half? an ops wallet?). For scale: RH fees through 2026-08-25 were $333.5k, half = $166.8k, so the $320k
  is neither exactly half nor exactly all of them.

### Lighter's own buyback series [M `exchangeMetrics?period=all&kind=buyback|buyback_usdc`]
These are what the app's Buybacks tab reads ("Robinhood buybacks" is not a separate tab; the page also reads
`explorer.elliot.ai/api/accounts/0/logs?pub_data_type=Trade`).

| month | Core revenue¹ | Core buyback_usdc | buyback / Core rev | Core LIT bought | RH buyback_usdc | RH gross fees² | Lighter's 50% of RH | DefiLlama RH [C ref] |
|---|---|---|---|---|---|---|---|---|
| Jul | 2,171.0k | 2,126.3k | 97.9% | 935.8k | 0.0 | 10.0k | 5.0k | 6k |
| Aug | 2,644.7k | 2,653.2k | 100.3% | 927.8k | 0.0 | 502.4k | 251.2k | 499k |
| Sep | 2,724.6k | 2,683.1k | 98.5% | 597.2k | 0.1k | 1,715.0k | 857.5k | 1,666k |
| Oct 1-22 | 2,149.9k | 2,142.1k | 99.6% | 622.3k | 0.0 | 1,571.1k | 785.6k | 1,566k (1-23) |
| **Q3** | **7,540.3k** | **7,462.6k** | **99.0%** | **2,460.8k** | ~0 | **2,227.4k** | **1,113.7k** | 2,171k |

¹ Core maker + taker + transfer + withdraw fees (exchangeMetrics, unfiltered = perp + spot). ² The same four kinds on the RH host.
- RH `buyback_usdc` (the same kind on the RH host) is ~$0 every day: a few cents, e.g. $0.04 on 2026-10-22.
- Orion's account-0 buys [M, orion.db read-only, `flow_usd.buyback`, rows stamped at day end]: Jul 2,097.8k, Aug 2,573.3k,
  Sep 2,764.7k, Oct 2,213.0k. Q3 $7.41M / 2.444M LIT (brief) vs Lighter's series $7.46M / 2.461M; the Q3 call says
  2.45M [C]; the stats page says "last quarter 2.46M LIT" [M]. **All of these match Core revenue alone.** If the RH share
  had been bought back on Core, Q3 buys would be ~$8.58M, not $7.46M.
- Core account 0 also moves its perp fees to spot daily (the pnl `outflow` ≈ `spot_inflow`, Jul 2,102k, Aug 2,522k,
  Sep 2,683k [M]). Its `inflow` is ~$0.37k a month, so **no RH money arrives at Core account 0**.

### Other hypotheses tested
| hypothesis | result |
|---|---|
| separate RH host/chain with its own treasury that buys LIT | RH host exists; its account 0 never trades; no LIT spot market on RH; buyback series 0 [M] |
| a different account or market on Core | Core buyback series = Core account 0 on 2049 and ≈ Core revenue only; Core account 0 inflow ~0 [M] |
| USDC/USDG bridged to L1 or held | **held**: $3.49M USDG in RH account 0 [M]; one $320k withdrawal on Robinhood Chain to an unlabelled EOA [M]; not traced into Ethereum (that EOA has no Ethereum USDG/USDC flows [M]) |
| LIT on Robinhood Chain | `0xeeca2E7Dc194a320d349122d88259bB9595a4cB0` is the **bridged** LIT: Arbitrum-standard token, `l1Address()` = the Ethereum LIT token, supply 455,571 LIT [M]. Not separate supply, and the Lighter RH contract holds none [M] |
| LIT reaching the L1 buyback wallet from elsewhere | `0x1a51…160d` LIT inflows over the last 120 days come only from the burn Safe: 15,638,702 on 2026-07-11 and 2,452,016 on 2026-10-09 [M]. Each matches an equal Safe inflow from `0x3b4d794a66…` (the L2 withdrawal path), alongside the reserve→Safe→dead burn. No RH-sourced LIT |
| sell side | RH account 0: no trades at all [M]. Core account 0: no sell flagged in any stored Orion fetch detail (the adapter reports sells; no `sold` in any `source_detail`) [M]. The stats page's "bought LIT back 18.73M" vs "burned 18.09M" [M] is a timing gap (post-10-01 buys), not a sale |

**Answer (1):** Lighter's 50% share of RH fees is **held as USDG in RH L2 account 0 and not bought back**: bought back =
**no** (measured through 2026-10-22). The call's "100% of trading revenue is used for buybacks" [C] matches Core only.
The account holds both halves, so the 50-50 split is not executed on L2; it is presumably settled off-platform or
pending. The only movement was the $320k on 2026-08-25, destination owner unknown. Unknown: whether Lighter intends a
catch-up buyback (e.g. a lump TWAP or a quarterly burn top-up). The 10-09 burn (2,452,017) equals Core buys only, so no
catch-up has happened yet.

## (2) First-party revenue source split by instance

**Found: Lighter's `exchangeMetrics` on both hosts.**
- Endpoints (keyless GET, daily points `{timestamp: UTC midnight, data: USD}`):
  - Core: `https://mainnet.zklighter.elliot.ai/api/v1/exchangeMetrics?period=all&kind=<k>`
  - RH: `https://api.rh.lighter.xyz/api/v1/exchangeMetrics?period=all&kind=<k>`
  - `<k>` ∈ `maker_fee`, `taker_fee`, `transfer_fee`, `withdraw_fee` (revenue); `liquidation_fee` (to the LLP, not revenue);
    also `buyback`, `buyback_usdc`, `volume`, `open_interest`, `attribution_maker_fee`/`attribution_taker_fee`
    (partner attribution, ~$0-16k a month, **not** the RH split). `&filter=byMarket&value=<symbol>` gives one market
    (DefiLlama uses it to scope perp vs spot).
- What it measures: gross fees charged per day per instance. Unfiltered = perp + spot.
- History: Core 644 days (from **2025-01-17**); RH 119 days (from **2026-06-26**, launch). Last point = the last completed UTC day.
- The 50% rule: the app's stats bundle (`app.lighter.xyz/assets/exchange-stats-*.js`) has
  `mt=new Set(['maker_fee','taker_fee','transfer_fee','withdraw_fee']); function vt(e){return mt.has(e)?.5:1}` and
  multiplies the RH series by it: "*ROBINHOOD CHAIN FEES COUNT AT LIGHTER'S 50% SHARE" [M]. **The API serves gross RH fees;
  the 0.5 is a client constant.** No endpoint serves the post-split figure.
- Check against the page total [M]: lifetime Core 66.30M + 0.5 × RH 3.80M = **68.20M** vs the page's "TOTAL REVENUE $68.21M".
- Check against the disclosure (Q3) [M vs C]: Core 7.540M + 0.5 × 2.227M = **8.654M**; Core share **87.1%**; Lighter's
  RH share **$1.114M** vs call **$8.5M / 87% / ">$1M attributed"** [C]. The total is +1.8% (the call likely rounded down);
  the share and the RH figure match.
- Check against DefiLlama [C ref]: Perps+Spot 2,199/2,680/2,795 vs my Core + RH spot ≈ 2,175/2,648/2,774 (−1.1/−1.2/−0.8%).
  Core alone is 2,171/2,645/2,725. RH perps 6/499/1,666/1,566 vs RH gross 10/502/1,715/1,571; the gap ≈ RH spot fees
  (0/2/49/5k). **DefiLlama counts 100% of RH fees, so it overstates Lighter's RH revenue 2×**, about +$1.1M in Q3.
- The DefiLlama sources read (github DefiLlama/dimension-adapters): `fees/lighterv2` (Core exchangeMetrics +
  `explorer.elliot.ai` account-0 trade logs for holders revenue), `fees/lighter-rh` (RH exchangeMetrics, perp markets
  only, all of it as revenue), `fees/lighterv2-spot` (spot on both hosts). So DefiLlama is a re-read of this API, not an
  independent source.
- Caveats: the 0.5 is contractual, not data, so Orion would carry it as a config constant with a citation (the call
  [02:24]-[02:28] "50-50 rev share"; the stats-page footnote). The API serves gross RH fees only and no post-split
  figure, so a change in the split would go unseen. `exchangeMetrics` daily values can be revised (unverified; diff
  before trusting). The 600-weight `trades` limit on RH doesn't apply here.

## Design options for Orion (config-level)
1. **Revenue streams core + robinhood × 0.5 (recommended for revenue).** Two `daily` streams under `reporting.revenue`, each
   an `http_json`-style exchangeMetrics sum (maker+taker+transfer+withdraw) per host. RH carries `share: 0.5` with a
   citation. Needs: a small adapter `lit.exchange_fees_daily {host, kinds, share}` (or a generic exchangeMetrics adapter)
   that returns a daily series. Backfill: Core from 2025-01-17, RH from 2026-06-26. DefiLlama stays a monthly cross-check,
   with RH at ×0.5 or with tolerance. Moves the config hash.
2. **Holder flow stays Core account 0 buys (no change)**, plus a **monitor-only level** `rh_fee_account_usdg` (RH account 0
   `collateral`), watched daily: a drop with no RH buyback means it was paid out or moved. It shows a catch-up buyback the
   day it happens. Needs: an http_json level metric on `rh:/account?by=index&value=0` → `accounts.0.collateral`,
   `monitor_only: true`. No valuation change.
3. **Second holder-flow member for RH, only if Lighter starts buying with it.** `lit.treasury_buys_daily` with
   `api: https://api.rh.lighter.xyz/api/v1, account: 0, market: <LIT spot id>`. No LIT spot market exists on RH today, so
   it can't be configured yet; or the RH funds may be bridged to Core and bought there, in which case the existing Core
   member already counts them. Don't build it now: it would read zero, or double count.
4. **Disclosed quarterly stream** (call figures: Q3 $8.5M total, 87% Core) as the `disclosed` stream, with options 1/2 as
   the measured cross-check. Needs: manual `data set` rows with citation/quote each quarter (the disclosure watcher files
   them). Weaker than option 1: quarterly, rounded, and late.
5. Valuation note (for Mike's decision, not config): the holder flow measures Core only, so the market is getting
   **~$0.86M a month (Sep-Oct run rate) of Lighter-owned RH revenue that is accruing, not returned**. Options: leave it out
   (cash held ≠ holder flow), or add a capture-probability-weighted RH term once Lighter states a policy. Ask Lighter/IR
   whether the RH share will be bought back.

## Reproduce (read-only)
- Fees: `curl '<host>/api/v1/exchangeMetrics?period=all&kind=maker_fee'` (and taker/transfer/withdraw/buyback_usdc).
- RH fee account: `<rh>/account?by=index&value=0`, `<rh>/pnl?by=index&value=0&resolution=1d&start_timestamp=1780000000&end_timestamp=<now>&count_back=400`, `<rh>/trades?account_index=0&sort_by=timestamp&limit=20`.
- Robinhood Chain: Alchemy `robinhood-mainnet.g.alchemy.com/v2/<ORION key>` works (chain id 0x1237). The robinhoodchain.blockscout.com API is behind Cloudflare.
- Scratch scripts (pruned in 24h): `~/.hermes/profiles/raymond/cache/scratch/{litp,pnl,attr,bb,rhc,rh2-5,l1,safe}.py`.
