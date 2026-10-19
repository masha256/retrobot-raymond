import json, sys, urllib.request, datetime, statistics
# usage: hl_funding2.py YYYY-MM-DD COIN...  (anchor 14:00 UTC on date)
# prints 30d daily-mean funding baseline (mean/sd of daily means) vs trailing 24h mean, with z-score
d = sys.argv[1]
anchor = int(datetime.datetime.strptime(d + " 14:00", "%Y-%m-%d %H:%M").replace(tzinfo=datetime.timezone.utc).timestamp() * 1000)
def post(body):
    req = urllib.request.Request("https://api.hyperliquid.xyz/info", data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=30))
for c in sys.argv[2:]:
    rows = []
    start = anchor - 31 * 86400 * 1000
    while True:
        r = post({"type": "fundingHistory", "coin": c, "startTime": start, "endTime": anchor})
        if not r: break
        rows += r
        last = r[-1]["time"]
        if len(r) < 500 or last >= anchor: break
        start = last + 1
    rows = [x for x in rows if x["time"] <= anchor]
    day = [float(x["fundingRate"]) for x in rows if x["time"] > anchor - 86400 * 1000]
    daily = {}
    for x in rows:
        if x["time"] > anchor - 30 * 86400 * 1000:
            k = (anchor - x["time"]) // (86400 * 1000)
            daily.setdefault(k, []).append(float(x["fundingRate"]))
    dm = [statistics.mean(v) for v in daily.values()]
    mu, sd = statistics.mean(dm), statistics.pstdev(dm)
    m24 = statistics.mean(day)
    print("%s 30d_daily_mean=%.6f%% sd=%.6f%% 24h_mean=%.6f%% z=%+.2f" % (c, mu * 100, sd * 100, m24 * 100, (m24 - mu) / sd if sd else 0))
