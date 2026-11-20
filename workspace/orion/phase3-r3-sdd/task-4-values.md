# Task 4 values (controller, verified on chain / first-party 2026-11-20 ~19:00Z; binding)

Mike's picks (2026-11-20 "all recommendations"): N1d PUMP option B, N1e CAKE option B, the rest as recommended.
Terms per asset are the scoping files' "Proposed method" YAML blocks, with these exact contracts (no elided ids):

- CAKE (cake-vvv-aero.md): add `cake_pool: 0x45c54210128a065de780C4B0Df3d16664f7f859e`, `vecake: 0x5692DB8177a81A6c6afc8084C2976C9933EC1bAB`;
  terms totalSupply - dead - burner - masterchef_v2 - cake_pool - vecake. Live: 315,730,969.
- CRV (crv-wrappers.md): add `circ_contract: 0x14139EB676342b6bC8E41E0d419969f23A49881e`, `community_fund: 0xe3997288987E6297Ad550A69B31439504F513267`,
  `vest_prelp: 0x575CCD8e2D300e2377B43478339E364000318E2c`, `minter: 0xd061D61a4d941c39E5453435B6345Dc261C2fcE0`; terms totalSupply -
  balanceOf(ve, community_fund, vest_prelp, token, minter, curve_treasury). Live: 1,582,336,065. Check (N5): Curve circ_contract
  `circulating_supply()` 1,588,069,374 (gap = the treasury, 0.36%; WATCH outside ±1%).
- cvxCRV: add `convex_treasury` (exists: 0x1389388d01708118b497f59521f6943be2541bb7); totalSupply - wrapper.balanceOf(convex_treasury) (4,862,034.53).
- sdCRV: add `sd_governance: 0xF930EBBd05eF8b25B1797b9b2109DDC9B0d43063`; totalSupply - gauge.balanceOf(sd_governance) (1,608,571.94).
- yCRV: add `yearn_treasury_vault: 0x93A62dA5a14C80f265DAbC077fCEE437B1a0Efde`; terms totalSupply - st_ycrv.balanceOf(yearn_treasury_vault) x pps -
  st_ycrv.balanceOf(yearn_treasury) x pps (`times: {contract: st_ycrv, function: pricePerShare, decimals: 18}`); pps 2.681874; 1,674,049 + 741,365.
- HYPE: add `hyper_foundation: 0xd57ecca444a9acb7208d286be439de12dd09de5d`, `community_grants: 0xa20fcfa0507fe762011962cc581b95bbbc3bbdba`;
  `hype.circulating_supply` subtract both. Live: 301,557,370 - 60,642,286 - 2,979,878.
- LINK: the 33 wallets Chainlink lists (from `https://supply.chain.link/supply` `balances[]`, its own list), names `nc_01`..`nc_33` in this order,
  every one a `-token.balanceOf(nc_NN)` term (zero balances kept: Chainlink's definition):
  - `0x98C63b7B319dFBDF3d811530F2ab9DfE4983Af9D` (27.00 LINK on 2026-11-20)
  - `0x75398564ce69B7498dA10a11ab06Fd8fF549001c` (0.78 LINK on 2026-11-20)
  - `0x5560d001f977df5e49ead7ab0bdd437c4ee3a99e` (0.00 LINK on 2026-11-20)
  - `0xbe6977e08d4479c0a6777539ae0e8fa27be4e9d6` (0.00 LINK on 2026-11-20)
  - `0xdAD22a85ef8310eF582b70e4051E543F3153e11F` (0.00 LINK on 2026-11-20)
  - `0xe0362f7445e3203a496f6f8b3d51cbb413b69be2` (1.70 LINK on 2026-11-20)
  - `0x5A8e77bC30948cc9A51aE4E042d96e145648BB4C` (30,000,000.00 LINK on 2026-11-20)
  - `0xe0b66bFc7344a80152BfeC954942E2926A6FcA80` (29,400,000.00 LINK on 2026-11-20)
  - `0xa42D0A18B834F52e41bEDdEaA2940165db3DA9a3` (0.00 LINK on 2026-11-20)
  - `0x276F695b3B2C7f24E7CF5b9d24e416a7f357aDb7` (0.00 LINK on 2026-11-20)
  - `0x5Eab1966D5F61E52C22D0279F06f175e36A7181E` (3,000,000.00 LINK on 2026-11-20)
  - `0x959815462EeC5fFf387A2e8a6871d94323D371de` (0.08 LINK on 2026-11-20)
  - `0xb9b012cad0A7C1b10CbE33a1B3F623b06fAD1c7C` (0.00 LINK on 2026-11-20)
  - `0xfB682b0dE4e0093835EA21cfABb5449cA9ac9e5e` (0.00 LINK on 2026-11-20)
  - `0x3264225f2Fd3bb8D5DC50587EA7506aA8638B966` (0.00 LINK on 2026-11-20)
  - `0x8d34d66bDb2d1d6ACd788A2d73d68e62282332e7` (0.00 LINK on 2026-11-20)
  - `0x4a87ecE3eFffCb012fbE491AA028032e07B6F6cF` (0.00 LINK on 2026-11-20)
  - `0x57Ec4745258e5A4C73d1A82636dc0FE291e3eE9F` (0.00 LINK on 2026-11-20)
  - `0x37398A324d35c942574650B9eD2987BC640BAD76` (0.00 LINK on 2026-11-20)
  - `0xD321948212663366503E8dCCDE39cc8e71C267c0` (0.00 LINK on 2026-11-20)
  - `0x55b0ba1994d68C2AB0C01C3332eC9473de296137` (0.00 LINK on 2026-11-20)
  - `0xD48133C96C5FE8d41D0cbD598F65bf4548941e27` (0.00 LINK on 2026-11-20)
  - `0x9c17f630DBde24eECe8fd248fAA2E51f690FF79B` (0.00 LINK on 2026-11-20)
  - `0x35a5dc3FD1210Fe7173aDD3C01144Cf1693B5E45` (0.00 LINK on 2026-11-20)
  - `0x0DFfD343C2D3460a7EAD2797a687304Beb394ce0` (28,750,000.00 LINK on 2026-11-20)
  - `0x76287e0F7b107d1C9f8f01D5aFac314Ea8461a04` (30,000,000.00 LINK on 2026-11-20)
  - `0x9BBb46637A1Df7CADec2AFcA19C2920CdDCc8Db8` (30,000,000.00 LINK on 2026-11-20)
  - `0x7594Eb0ca0a7f313bEFD59AfE9e95c2201a443e4` (30,000,000.00 LINK on 2026-11-20)
  - `0x8652Fb672253607c0061677bDCaFb77a324DE081` (30,000,000.00 LINK on 2026-11-20)
  - `0x157235A3cc6011d9C26A010875c2550246aAbcCA` (22,000,000.00 LINK on 2026-11-20)
  - `0xa71bbBd288a4e288CfDC08bb2E70DCd74Da4486D` (0.00 LINK on 2026-11-20)
  - `0xEc640A90e9A30072158115B7C0253f2689ee6547` (0.00 LINK on 2026-11-20)
  - `0x2a6AB3B0C96377bd20AE47E50ae426A8546A4Ae9` (0.00 LINK on 2026-11-20)
  Live sum 233,150,029.58; circ 766,849,970.42 = the API's circulatingSupply exactly. Check (N5): http_json `https://supply.chain.link/supply`
  path `circulatingSupply` decimals 18 as a monitor-only level + WATCH outside ±0.5% of the gap.
- LIT: terms totalSupply - dead - ecosystem_reserve - buyback_wallet, `locked_schedule: {amount: 500000000, first_tranche: 2027-01-29, tranches: 36,
  every_months: 1, citation: "https://x.com/Lighter_xyz/status/2005862687331303804"}` (quote in sky-lit.md). Live: 245,112,910.
- PUMP (option B): add `token_custodian: Cfq1ts1iFr1eUWWBm8eFxUzm5R3YA3UvMZznwiShbgZt` and the five dormant custodian-funded vaults (owners):
  `dormant_a: 8UhbNoBXmGoxJr2TeWW8wmSMoWmjS2rTT2tVJxzuTogC` (80.0B), `dormant_b: 9pkFKCR1mdS31JxjKdtmWg2awZUg6vJUYVY722DAcXzv` (35.0B),
  `dormant_c: BBvQteuawKB2UtExfevL8HYLjWWsgmWXsp922vFbvCfT` (25.0B), `dormant_d: GTeSSwovPiVirpvWJpThUWiLDSLsuApmJw621Yom3MhB` (25.0B),
  `dormant_e: AvqFxKNrYZNvxsj2oWhLW8det68HzCXBqswshoD2TdT6` (24.0B); `solana.supply_less_owners` subtract all six. Live ~403.51B.
- SKY: add `mkr_sky: 0xA1Ea1bA18E88C381C724a75F23a130420C403f9a`; terms totalSupply - balanceOf(pause_proxy) - mkr_sky.take() (39,985,420).
- UNI: add `uf_grants: 0x5069A64BC6616dEC1584eE0500B7813A9B680F7E`, `aera_incentives: 0x7c8406384f7a5c147a6ADd16407803BE146147E4`;
  terms totalSupply - dead - timelock - uf_grants - aera_incentives.
- VVV: add `venice_safe_b: 0x4665883F3Adb708F301BA75764D39AD0cD2a4D84`, `venice_safe_c: 0xb3c89592D84ae6Adb6A1aa41515ac14eC822B175`,
  `sablier_linear: 0x4CB16D4153123A74Bc724d161050959754f378D8`; terms totalSupply - burn_sink - treasury - venice_safe_b - venice_safe_c -
  sablier_linear (= vvv_stats exactly). Keep the existing Venice cross-check at 2% (N1j).
