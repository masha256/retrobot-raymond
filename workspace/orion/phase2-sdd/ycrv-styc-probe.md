# st-yCRV fee probe (controller, Task 2 Step 1, 2026-11-04; read-only, Alchemy mainnet RPC, 91 days to head)

Question (spec §8 yCRV row): is Yearn's st-yCRV performance fee (`flow_usd.yearn_styc_fee`, v1 ~0.10 $M/yr) taken out
of what YBS stakers are paid, or charged on yield outside the splitter?

Measured:
- st-yCRV vault `0x27b5739e22ad9033bcbf192059122d163b60349d` (yVault 0.4.3) has ONE strategy in its withdrawal queue:
  `0xe3974e44bc08f435da2c6db7d01e1758496da119`, name() = "StrategyYBSFarmer".
- That strategy holds 42,470,762 yCRV staked in YBS (`ybs.balanceOf`), of YBS totalSupply 63,273,579 = 67.1% of all
  staked yCRV. Vault totalAssets 42,470,877 yCRV (114 yCRV idle in the vault).
- Distributor `0xb226c52e…` paid 337,042 yvcrvUSD-2 shares over 91 days; 236,920 (70.3%) went to the StrategyYBSFarmer
  (13 claims). The strategy also received 273,952 crvUSD from the yvcrvUSD vault (redemptions) and yCRV from swaps/YBS.
- Fee: 91 transfers of st-yCRV shares from the vault to the Yearn treasury `0x044f9c86…`, 58,241.5 shares
  (pricePerShare 2.6537 yCRV/share now). No fee mints from 0x0.

Verdict: INSIDE. The st-yCRV vault's gains are the YBS crvUSD rewards it claims (70% of all YBS payouts), compounded
into yCRV; its 10% performance fee is carved out of payouts that `flow_usd.fees` (ybs_payout, measured at the
distributor) already counts. Adding it to revenue (v1's 2.31) double-counts.

Ruling (controller, for Task 2 and the followups note): yCRV v2 revenue = `yearn_gross` only (2.20 on 2026-10-27).
The st-yCRV fee is a fee of a wrapper product above YBS (charged only to st-yCRV depositors), not yCRV revenue and not
the protocol's take from YBS stakers: it is left OUT of the v2 statement (no revenue, holders or protocol line), so
yCRV holder flow (YBS staker yield) stays unchanged as the plan requires; `flow_usd.yearn_styc_fee` stays collected
(monitor_only) and in the legacy `income` lines until Task 11. The spec's alternative (holders −0.10, protocol +0.10)
would move yCRV holder flow by ~−6% and understate a direct YBS staker's yield; raised to Mike at G1 as a flip-able
ruling.
