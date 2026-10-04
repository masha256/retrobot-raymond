import json, urllib.request, urllib.parse, sys, datetime
# usage: python3 regime_fetch2.py YYYY-MM-DD SYM...  (last 5m bar <=14:00 UTC vs prior daily close)
D=sys.argv[1]
anchor=datetime.datetime.strptime(D,"%Y-%m-%d").replace(hour=14,tzinfo=datetime.timezone.utc).timestamp()
H={"User-Agent":"Mozilla/5.0"}
def get(u):
    return json.load(urllib.request.urlopen(urllib.request.Request(u,headers=H),timeout=20))["chart"]["result"][0]
for s in sys.argv[2:]:
    q=urllib.parse.quote(s)
    try:
        r=get("https://query1.finance.yahoo.com/v8/finance/chart/%s?interval=5m&range=5d&includePrePost=true"%q)
        bars=[(t,c) for t,c in zip(r["timestamp"],r["indicators"]["quote"][0]["close"]) if c is not None and t<=anchor]
        t,px=bars[-1]
        r2=get("https://query1.finance.yahoo.com/v8/finance/chart/%s?interval=1d&range=1mo"%q)
        dl=[(datetime.datetime.utcfromtimestamp(tt).strftime("%Y-%m-%d"),c) for tt,c in zip(r2["timestamp"],r2["indicators"]["quote"][0]["close"]) if c is not None]
        pd,pc=[x for x in dl if x[0]<D][-1]
        print("%s px=%.4f at %s prev_close(%s)=%.4f chg=%+.2f%%"%(s,px,datetime.datetime.utcfromtimestamp(t).strftime("%m-%d %H:%M"),pd,pc,(px/pc-1)*100))
    except Exception as e:
        print(s,"ERR",e)
