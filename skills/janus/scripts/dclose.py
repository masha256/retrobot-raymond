import sys, json, urllib.request, urllib.parse, datetime
# Usage: python3 dclose.py SYM... -> last 4 daily closes with d/d % (Yahoo 1d/10d). For weekend anchors.
H={"User-Agent":"Mozilla/5.0"}
for s in sys.argv[1:]:
    u="https://query1.finance.yahoo.com/v8/finance/chart/%s?interval=1d&range=10d"%urllib.parse.quote(s)
    try:
        r=json.load(urllib.request.urlopen(urllib.request.Request(u,headers=H),timeout=20))["chart"]["result"][0]
        ts=r["timestamp"]; c=r["indicators"]["quote"][0]["close"]
        rows=[(datetime.datetime.utcfromtimestamp(t).strftime("%Y-%m-%d"),x) for t,x in zip(ts,c) if x is not None][-4:]
        out=[]
        for i,(d,x) in enumerate(rows):
            ch="" if i==0 else " (%+.2f%%)"%((x/rows[i-1][1]-1)*100)
            out.append("%s %.2f%s"%(d,x,ch))
        print(s, " | ".join(out))
    except Exception as e:
        print(s,"ERR",e)
