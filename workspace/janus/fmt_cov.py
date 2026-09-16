import json,sys
d=json.load(open(sys.argv[1]))['data']['coverage']
for c in sorted(d,key=lambda x:(x['class'],x['symbol'])):
    print("{s:7s} {cl:6s} px={p:<10.6g} d%={dc:+6.2f} v20={a:+7.2f} v50={b:+7.2f} v200={e:>8} x={x}/{xa} px50={y}/{ya} fund={f:.5f} ref={fr:.5f} atr%={at:.1f}".format(
        s=c['symbol'], cl=c['class'][:6], p=c['close'], dc=c['daily_change_pct'], a=c['px_vs_sma20'], b=c['px_vs_sma50'],
        e=('%.2f'%c['px_vs_sma200']) if c['px_vs_sma200'] is not None else 'NA',
        x=c['cross_50_200'], xa=c['cross_50_200_age'], y=c['cross_px_50'], ya=c['cross_px_50_age'],
        f=c['funding_rate'] or 0, fr=c['funding_ref'] or 0, at=100*c['atr14']/c['close']))
