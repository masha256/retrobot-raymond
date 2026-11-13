# Phase 3 R2 scoping: HYPE, LIT, PUMP prices without CoinGecko / DefiLlama / Jupiter

Read-only scoping, 2026-11-13 (measurements 14:39 to 14:50 UTC). Code read in `/home/hermes/git/orion/.worktrees/phase3`.
Spec: `docs/superpowers/specs/2026-11-09-orion-phase3-third-party-removal-design.md` §3.1, §4, D2, D3, D9.
Tags: **MEASURED (time)** means I read it myself at that time. **CLAIMED (source)** means it is taken from a source and not
re-measured. **DEV-ONLY REF** marks CoinGecko or GeckoTerminal figures, used only to sanity-check, never as a method.
About 450 requests in total: Hyperliquid ~6, Lighter ~25, Ethereum RPC ~130, Solana RPC ~230, CoinGecko 7, GeckoTerminal 2.
No RPC URL or key is written here.

## 0. Who needs an hourly history (from the code)

| asset | flows stored in tokens and priced in USD? | evidence | needs hourly `prices` history? |
|---|---|---|---|
| HYPE | **no** | `flow_usd.af_buys_direct` takes px x sz from the fills (`hype.ts:156/183/203`, token `usd`). `af_buyback`/`revenue_proxy` are DefiLlama USD (deleted in R5). `reserve_yield` is in USDC. No `flow_tokens.*`. | **No** for today's flows. Only `price_usd` (level) moves. |
| LIT | **no** | `flow_usd.buyback` takes trade price x size (`lit.ts:83`, `USD_TOKEN`). `flow_tokens.buyback/burn/routed_to_prime` are `unit: tokens`, so nothing prices them. Fees come in USD from `exchangeMetrics`. | **No** for today's flows. Only `price_usd` (level) moves. |
| PUMP | **yes** | `flow_usd.buyback` = `solana.supply_burn_daily`: the burned tokens x **the day's mean CoinGecko hourly price**, fetched inline from `/coins/pump-fun/market_chart` (`solana.ts:108-124`), not through the `prices` table. That explains why prod has no PUMP `prices` rows. Days before the first on-chain supply reading come from DefiLlama USD (`params.history`), which R6 deletes. | **Yes**, but only from the first stored `total_supply` reading. The YAML and the onboarding note put that at 2026-10-16 (**CLAIMED**, to be checked in prod `observations`). That is about 29 days (~700 hours) today, not 183 days. A daily mean is enough, so hourly is an implementation choice. |

The report reads `price_usd` only as the level on the report day (`report/load.ts:224` `level(STD_METRICS.price)`). No 91-day mean price is computed.

Consequence for D3 (the 52.7k-call estimate assumed 12 refs x 24 h x 183 d): **HYPE and LIT can skip the history rebuild.**
It is still cheap for both, so writing it anyway costs almost nothing and keeps the table uniform: HYPE takes 1 request, LIT 9.
For PUMP the rebuild is about 700 hours now. It grows to 183 days only if R6 rebuilds burns or fees from the chain further back.

## 1. HYPE (Hyperliquid)

**Needs history:** no (see §0). Level only, plus an optional uniform history because it is nearly free.

**Instruments (MEASURED 2026-11-13 14:39Z, `POST api.hyperliquid.xyz/info`):**
- Spot: `@107` = tokens [150 HYPE, 0 USDC], `isCanonical: false`. midPx 73.8505, markPx 73.854, day notional volume $70.8M.
  The other HYPE spot pairs are thin: `@207` $65k/day, `@255` $35k/day, `@232` with no volume. `@107` is the pair the
  YAML's `af_buys_direct` already uses.
- Perp `HYPE`: midPx 73.8055, markPx 73.7666, oraclePx 73.8235, day volume $553M, OI 21.66M HYPE.
- `allMids`: `@107` 73.8355, `HYPE` 73.795.

**Right "price":** the spot `@107` mid (HYPE/USDC), x Chainlink USDC/USD (Ethereum feed: 0.99978, **MEASURED** 14:42Z) to
match the D2 "x stable feed" rule. Spot is the asset itself. The perp is a derivative with funding and premium.

**History, MEASURED:** `candleSnapshot {coin:"@107", interval:"1h"}` serves only the newest ~5,000 candles. A request
from 2026-03-01 returned 5,003 candles starting **2026-04-19 04:00Z**, and requests for 2025-01 and 2025-12 returned 0.
This matches the docs' "only the most recent 5000 candles" (**CLAIMED**, Hyperliquid docs, info endpoint).
From 2026-05-13: 4,431 hourly candles, **0 missing hours, 0 hours with fewer than 10 trades**. One request covers the
whole 183 days. The window is rolling (~208 days), so a rebuild has to run before 2026-05-13 drops out (~25 days of
slack today), or persist as it goes.

**Check:** the perp `HYPE` candle close. It is a separate order book and a separate trader set, and its mark is anchored
to the validators' oracle (a weighted median of CEX spot, **CLAIMED**, Hyperliquid docs). It is not fully independent,
because the venue is the same. A HyperEVM pool (WHYPE/USDT0) would be off-venue, but I did not measure one and do not
know whether the public HyperEVM RPC serves archive state. That is an open question.

**Gaps, MEASURED (2026-05-13 to 2026-11-13 14:00Z, 4,431 hours), spot close vs perp close:**
median 0.033%, p95 0.094%, p99 0.141%, max 0.377% (2026-10-30 01:00Z: 89.035 vs 89.372), signed mean +0.007%.
The daily-mean gap has a median of 0.027% and a max of 0.098%. A 2% tolerance has a large margin. 0.5% would also hold.
- DEV-ONLY REF, CoinGecko `hyperliquid` (89-day hourly, 2,136 hours): spot open vs CG median abs 0.026%, p95 0.089%,
  max 0.686%. Perp: 0.033% / 0.122% / 0.663%. CG simple price 74.10 at 14:45Z, against `@107` mid ~73.84 at 14:39Z, a
  few minutes apart.

**Terms:** the Hyperliquid Terms of Use (https://app.hyperliquid.xyz/terms, last updated 2026-06-15) cover the
**Interface** (app.hyperliquid.xyz) of Hyperliquid Corp. They exclude US and Ontario persons (§1.6) and prohibit
automated use beyond reasonable limits (§3.1.8). They say nothing about the info API, data licensing or redistribution.
The Hyper Foundation ToS (https://hyperfoundation.org/termsOfService, revised 2024-10-10, **CLAIMED** from the
foundation's llms-full.txt because the page returned 404 to my fetcher) says "the Hyperliquid L1 is not part of the
Services" and also lists the US as a prohibited jurisdiction. The data is the L1's public state. **No clause grants or
forbids commercial display.** The US-person restriction applies to the interface and foundation services, and its
application to keyless API reads is a judgement call for Mike/legal. Orion already reads this API in prod.

**Recommendation:** primary = `@107` hourly candle **close** (or the open of the next hour) for history and `allMids["@107"]`
for the live level, x Chainlink USDC/USD. Check = perp `HYPE` (candles for history, `allMids` live) at 2% tolerance (0.5%
is feasible). Write the 183-day history now (1 request) even though no flow needs it, before the 5,000-candle window
passes 2026-05-13.

## 2. LIT (Lighter)

**Needs history:** no (see §0). Level only, plus an optional uniform history (9 requests).

**Markets (MEASURED 14:40Z, `GET mainnet.zklighter.elliot.ai/api/v1/orderBooks`):** spot `LIT/USDC` market 2049 (created
2025-12-29); perp `LIT` market 120 (created 2026-01-02, OI $72.4M). Ignore `LITE` (178): it is a different market.

**History, MEASURED:** `GET /api/v1/candles?market_id=&resolution=1h&start_timestamp=&end_timestamp=&count_back=`
returns at most 500 candles per call (docs: https://docs.lighter.xyz/api/candlesticks/candles.md). The old path
`/candlesticks` returns **403**. Hourly data reaches back to each market's start: daily candles begin 2025-12-30 (2049) and
2026-01-02 (120), and hourly candles exist on 2026-01-10. From 2026-05-13: 4,431 hours for each market in **9 calls**
each, with no missing hour and no zero-volume hour on spot. Spot hourly quote volume: median $157k, p5 $23k, min $3.1k.
Perp median $546k. (This is longer than the ~150 days of `trades` the buyback adapter has.)

**On-chain pools (Ethereum; MEASURED by reading state over our RPC, reserves CLAIMED by GeckoTerminal, DEV-ONLY REF for discovery):**
| pool | TVL (GT, claimed) | 24h vol (GT) | state read |
|---|---|---|---|
| Uniswap v4 LIT/USDC 0.3%, id `0x8366b1dd…cc00f1` | $579k | $392k | StateView `0x7fFE…7227` `getSlot0` |
| Uniswap v4 LIT/ETH 0.3%, id `0x0112df46…f428` | $505k | $228k | same, x Chainlink ETH/USD |
| Uniswap v3 LIT/WETH 1% `0xcd4abaf3…c22a` | $330k (137 WETH + 18.3k LIT measured) | $138k | `slot0`; **observationCardinality 1, so no TWAP** |
| Metric LIT/USDC `0xfc71…c321` | $182k | $119k | not read |
| v3 LIT/USDC 1% `0x25d4…bdd` | $1.5k | n/a | dust |

There is no deep on-chain pool. Total is about $1.6M across all pools, against Lighter spot's ~$4.7M/day and the perp's $72M OI.
So the spec's "or a pool if LIT has a deep on-chain one" does not apply: **Lighter stays primary** and the v4 LIT/USDC
pool is the **independent check** (another venue on another chain). Uniswap v4 has no built-in oracle, so the check reads
spot `sqrtPriceX96` at the hour's block, and it must skip hours with zero in-range liquidity. On 2026-05-14 12:00Z the v4
USDC pool had liquidity 0 and a stale price of 1.772 against Lighter's 0.89 (+99%). That shows why the guard is needed.

**Gaps:**
- Now (MEASURED 14:41Z): Lighter spot last 3.354, book 3.3547 / 3.3577 (mid 3.3562). v4 LIT/USDC 3.3573 (x USDC feed),
  v4 LIT/ETH 3.3594, v3 LIT/WETH 3.3542. All are within 0.1% of the Lighter mid.
- Lighter spot 2049 vs perp 120 closes, 4,431 hours (MEASURED): median 0.101%, p95 0.296%, p99 0.418%, max 1.406%
  (2026-08-07 14:00Z, 2.4119 vs 2.4463). Signed mean −0.087%: spot runs slightly under the perp. Daily-mean gap: median
  0.092%, max 0.324%.
- Lighter spot (hour open) vs on-chain pools at that hour's block, 12 sample hours from 2026-05-14 to 2026-11-06
  (MEASURED, archive `eth_call`): v4 LIT/USDC within ±0.77% on every sample except the 05-14 zero-liquidity one.
  v4 LIT/ETH within 2.4% (worst 05-30, −2.36%). v3 LIT/WETH 1% within 1.21%. The pools are thin, so a check tolerance of
  2% hourly would trip now and then. A daily-mean check or 3% hourly is safer.
- DEV-ONLY REF, CoinGecko `lighter` (2,136 hours): Lighter spot open vs CG median abs 0.091%, p95 0.252%, max 0.813%.
  CG simple price 3.36 at 14:45Z. Venue view (DEV-ONLY, CG tickers): OKX $12.0M, Bybit $8.4M, Coinbase $6.7M, Lighter
  spot $4.7M per day. Lighter is not the deepest LIT spot venue, but it is the issuer's own venue and in line with the CEXs.

**Terms:** Lighter Terms of Service (https://lighter.xyz/terms, last updated 2025-12-29, Elliot Technologies, Inc.)
explicitly cover the **API** ("as well as a related API"; §5 API usage: no damage or impairment, no unlawful use; the
company may limit or terminate the API). There is **no data-licence or redistribution clause, and nothing on commercial
display**. However, the Services, which include the API, are stated as **"not available to persons … in the United States
of America, Canada, the United Kingdom, …"**, and §4 lists "unauthorized access to the API" as grounds for suspension.
Orion already reads this API (buybacks, fees). Whether a US operator may rely on it for a published site is a legal
question for Mike and should go on the sources-register row.

**Recommendation:** primary = Lighter spot 2049 hourly candle close (history) and the order-book mid or `last_trade_price`
(live), x Chainlink USDC/USD. Checks: (1) the Lighter perp 120, which is same-venue but measured as tight, at 2%; and
(2) the independent check required by the spec: Uniswap v4 LIT/USDC 0.3% `getSlot0` over our Ethereum RPC, with a
non-zero `getLiquidity` guard, at about 3% hourly or 2% on the daily mean. A history rebuild for the v4 check would cost
~4,400 archive blocks x ~3 calls. Run the check on a daily sample for history (~550 calls) and hourly live.

## 3. PUMP (Solana)

**Needs history:** **yes**, for the burn flow (`flow_usd.buyback`) from the first on-chain supply reading (~2026-10-16,
CLAIMED), about 700 hours now. A daily mean is enough for the adapter, but it should read the `prices` table (spec §3.1).
Full 183-day depth is needed only if R6 rebuilds burns or fee accounts on chain before 2026-10-16. **Flag for R6:**
PumpSwap and bonding-curve fee accounts accrue SOL/USDC, so R6's `balance_delta` revenue lines will need a **SOL/USD**
history too.

**Pools (discovery via GeckoTerminal, DEV-ONLY REF; state MEASURED over our Solana RPC 14:43Z):**
| pool | program | quote | depth | price now |
|---|---|---|---|---|
| **PumpSwap PUMP/USDC `2uF4Xh61…iSd`** | `pAMMBay6…EA` | USDC | **3.0147B PUMP + 10.53M USDC (~$21M), MEASURED** | 0.0034927 to 0.0034946 |
| Orca whirlpool PUMP/SOL `BofA2ViU…5BKW` | whirLb… | SOL | $2.2M (GT) | 0.0034993 (x Pyth SOL 81.36), +0.13% |
| Meteora DLMM PUMP/USDC bin 20 `9SMp4yLK…KoZj` | LBUZ… | USDC | $1.39M (GT); reserves 343.3M PUMP + 189.8k USDC measured | 0.0034953, +0.02% |
| Raydium CLMM PUMP/SOL `45ssPkUQ…XuWC5` | CAMM… | SOL | $0.54M (GT) | 0.0034972 (x Pyth), +0.07% |
| Meteora DLMM PUMP/USDC bin 80 `88LoXa6p…fPy` | LBUZ… | USDC | $0.21M (GT) | 0.0034916, −0.09% |

There is **only one deep PumpSwap PUMP pool**. The other PumpSwap PUMP pools are memecoin/PUMP pairs, which are not
usable. PumpSwap pool account layout (MEASURED and parsed): disc 8, bump 1, index 2, creator 32, base_mint, quote_mint,
lp_mint, pool_base_token_account `8TqK4PL3…9bhC`, pool_quote_token_account `68Vdm7mQ…dr8t`, lp_supply. The price is
quote vault / base vault, read with `getTokenAccountBalance` on the two vaults, or with one `getMultipleAccounts`.

**Live check (D9):** the deepest second pool is Orca PUMP/SOL, but it needs a SOL/USD leg (Pyth push feed
`7UVimffx…LiE`, owner `rec5EKMG…`, parsed MEASURED 81.306 to 81.36; it has no history on chain). **Recommend the Meteora
DLMM PUMP/USDC (bin step 20) instead.** It is USDC-quoted, so no SOL leg or Pyth is needed. Price =
(1+bin_step/1e4)^active_id, from the `lb_pair` account (active_id @76, bin_step @80). The 0.2% bin granularity is fine at
2%. Raydium CLMM x Pyth is the fallback. D9 says "PumpSwap/Raydium". Meteora meets the intent (a second, independent
pool), and that should be stated in the plan.

**Past hours: how (MEASURED):** standard Solana RPC has no account state at past slots. Options:
- **(a) Swap-tx parsing, which works.** 1) Find the slot at the hour: binary search with `getBlockTime`. The measured
  slot time is **0.215 s** (1M slots), not 0.4 s, and a 0.4 s estimate lands hours off. 2) Take one signature from
  `getBlock(slot, transactionDetails:"signatures")` as a seek key. 3) `getSignaturesForAddress(pool, {before: seekSig,
  limit: 50})`: a `before` signature that does not involve the pool works as a time cursor (MEASURED, the first
  signature lands 1 to 294 s before the hour). 4) `getTransaction` of the first non-failed signature with
  **`maxSupportedTransactionVersion: 1`**. Version-1 transactions now exist, and `0` fails with −32015. 5) The pool
  vaults' `postTokenBalances` give the reserves after the swap, so price = quote/base. The pool has ~5,300 signatures an
  hour, 86% of them failed bot transactions (MEASURED over 1,000 signatures / 674 s). History reaches at least 2026-05-15
  (MEASURED, a sample at 182 days back worked). Cost: ~11 calls an hour as measured with a naive search, ~5 to 6 with a
  cached slot/time interpolation. That is ~4k to 8k calls for the ~700 hours needed, or 25k to 45k calls for 183 days.
- **(b) pump.fun's own APIs:** there is no documented public price or candle API (none found). The frontend endpoints
  fall under Terms §21(h) (https://pump.fun/docs/terms-and-conditions, last updated 2026-11-04): no "web crawlers, bots,
  spiders or other automatic devices … to access, obtain, copy or monitor any part of the Pump Platform and/or Pump
  Services", except automated access "we expressly permit" (§6.1). **Do not use them.**
- **(c) Does R2 need it at all:** yes, but only from about 2026-10-16 (see above), unless R6 extends it.

**Sample hours, MEASURED (PumpSwap reserves from the first swap before the hour; check = Meteora DLMM bin-20 execution price from the vault deltas of its first swap before the hour, fee included):**
| hour (UTC) | PumpSwap | lag s | DLMM exec | swap $ | gap | CG (DEV-ONLY) |
|---|---|---|---|---|---|---|
| 2026-11-13T02 | 0.0034580 | 7 | none in 6 tx tried | | | 0.0034618 |
| 2026-11-10T14 | 0.0035042 | 33 | 0.0035093 | 317 | +0.14% | 0.0035034 |
| 2026-11-06T14 | 0.0040085 | 17 | 0.0040200 | 99 | +0.29% | 0.0040121 |
| 2026-10-30T14 | 0.0040237 | 2 | 0.0040361 | 405 | +0.31% | 0.0040218 |
| 2026-10-23T14 | 0.0046288 | 3 | 0.0046420 | 505 | +0.29% | 0.0046403 |
| 2026-10-16T14 | 0.0044120 | 1 | none | | | 0.0044124 |
| 2026-09-14T14 | 0.0036337 | 19 | 0.0036378 | 420 | +0.11% | 0.0036313 |
| 2026-07-16T14 | 0.0016306 | 293 | 0.0016261 | 1,380 | −0.28% | (outside CG 89 d) |
| 2026-05-15T14 | 0.0017885 | 41 | none | | | (outside CG 89 d) |
The check gaps are 0.1% to 0.3%, consistent with the DLMM fee and bin. PumpSwap vs CG (DEV-ONLY), 7 hours: median abs
0.065%, max 0.25%. Live now (14:43Z): PumpSwap 0.0034946 vs DLMM +0.02%, Raydium x Pyth +0.07%, Orca x Pyth +0.13%;
CG simple 0.00349003 (DEV-ONLY).
A historical check for each hour costs about 2 to 6 more calls and finds no qualifying DLMM swap in about 1 of 3 hours.
Use a daily check for history.

**Terms:** pump.fun Terms of Use (URL above) grant only a personal-use licence of Pump IP (§17). §21(h) bans automated
access to the Platform/Services, and §21(c) bans commercially exploiting access. Reading the PumpSwap program's accounts
and transactions through our own Solana RPC (Alchemy) does not touch the Pump Platform. It is public chain data, the same
basis as the existing `solana.*` adapters, but whether PumpSwap on-chain state counts as a "Pump Service" is a judgement
call: say so in the sources register. The Pyth SOL/USD push feed is needed only if Orca/Raydium is the check. I did not
read Pyth's data terms, because the recommendation avoids the feed.

**Recommendation:** primary = PumpSwap PUMP/USDC vault reserves (live: `getMultipleAccounts` on the two vaults at the
hour; history: the swap-tx `postTokenBalances` method), x Chainlink USDC/USD. Check = Meteora DLMM PUMP/USDC bin-20
active bin (live), at 2%. Rebuild hourly PUMP prices from the first supply reading (~700 hours, ~4k to 8k calls).
`solana.supply_burn_daily` then takes the daily mean from `prices` (source `chain`) and drops `market_chart`.

## 4. Open questions

1. PUMP: the exact first on-chain `total_supply` reading in prod. That sets the start of the PUMP history. Does R6 rebuild burns or fees before it (183-day PUMP and SOL/USD history), or does it stay "absent"?
2. HYPE/LIT: write the optional 183-day hourly history anyway (≈10 requests total), or drop them from the D3 rebuild and the "12 refs" cost line? If written, the HYPE rebuild must run before ~2026-12-08 (the 5,000-candle window).
3. US-person clauses: Lighter ToS ("Services … API" not for US persons) and Hyperliquid interface/foundation terms. Neither has a data licence. Mike/legal to decide for the published site's sources register.
4. HYPE off-venue check: is there a HyperEVM WHYPE/USDT0 pool with archive-readable state (public RPC or a provider)? Not measured.
5. LIT check tolerance: v4 pools are thin ($0.5M). Use 3% hourly or 2% on the daily mean, guard on zero in-range liquidity, or use the Lighter perp as the routine check and v4 as a weekly independent check?
6. D9 wording: the second pool recommended is Meteora DLMM (USDC-quoted), not Raydium (which needs SOL x Pyth). OK to amend?
7. Past `price_usd` level rows (CoinGecko-sourced): keep, relabel, or replace from candles and the tx method? D3 speaks of flows. Levels are not addressed.

## 5. Scratch data (not repo files)
`$TMPDIR` (`~/.hermes/profiles/raymond/cache/scratch/`): `hype_candles.json`, `lit_candles.json`, `lit_samples.json`,
`pump_samples.json`, `cg_devref.json` (DEV-ONLY). These are pruned after 24 h idle.
