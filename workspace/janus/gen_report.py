import json, subprocess, os
os.environ['JANUS_DB']='/home/hermes/.hermes/profiles/raymond/workspace/janus/janus.db'
D='2026-09-17'
def j(cmd):
    out=subprocess.run(cmd,shell=True,capture_output=True,text=True).stdout
    return json.loads(out)

macro=j(f'janus macro reads --date {D}')['data']
cl=j(f'janus cluster reads --date {D}')['data']['reads']
scores=j(f'janus score list --date {D}')['data']
rows=scores.get('scores') or scores.get('items')
heat=j('janus heat')['data']

mreg=macro['metrics']['regime']
cmap={1:"Crypto Assets",2:"AI / Semiconductors",3:"AI / Software"}
amap={"AAPL":None,"GOOGL":None,"AAVE":1,"AERO":1,"ARB":1,"BTC":1,"ETH":1,"HYPE":1,"LINK":1,"LIT":1,
"NEAR":1,"ONDO":1,"POL":1,"SOL":1,"UNI":1,"VVV":1,"ZEC":1,"AMD":2,"INTC":2,"MU":2,"NVDA":2,"SNDK":2,"PLTR":3}

def esc(s): return s.replace('|','\\|').replace('\n',' ')

L=[]
L.append(f"# Score report — {D}\n")
from collections import Counter
c=Counter(r['directive'] for r in rows)
dstr=", ".join(f"{v} {k}" for k,v in c.most_common())
L.append(f"Queue: {len(rows)} assets ({len(rows)} flagged, 0 open trades). Directives: {dstr}.\n")

L.append("## Regime\n")
L.append(f"**Macro: {mreg:+.1f}** — {esc(macro['read']['summary'])}\n")
L.append("| Cluster | Regime | Δ vs macro | Summary |")
L.append("| --- | --- | --- | --- |")
for r in sorted(cl,key=lambda x:-x['metrics']['regime']):
    reg=r['metrics']['regime']
    L.append(f"| {r['cluster_name']} | {reg:+.1f} | {reg-mreg:+.1f} | {esc(r['summary'])} |")
L.append("")

L.append("## Portfolio heat\n")
b=heat['book']
L.append("| Guardrail | Detail | Status |")
L.append("| --- | --- | --- |")
L.append(f"| Book heat | ${b['heat']:,.0f} of ${b['limit']:,.0f} ({b['used_pct']:.0f}%) — no open positions | ✅ |")
L.append("")

L.append("## Actions for today\n")
act=[r for r in rows if r['directive'] not in ('HOLD','STAND_ASIDE')]
if not act:
    L.append("No actions today.\n")

L.append("## Scores\n")
L.append("| Asset | Cluster | Position | Directive | Direction | Conviction | Why not | Rationale |")
L.append("| --- | --- | --- | --- | --- | --- | --- | --- |")
srt=sorted(rows,key=lambda s:(-(s['conviction'] or 0),-abs(s['direction'])))
for s in srt:
    cn=cmap.get(amap[s['symbol']],"—")
    L.append(f"| {s['symbol']} | {cn} | {s['position_state']} | {s['directive']} | {s['direction']:+.2f} | {s['conviction']} | {esc(s['results'].get('directive_reason') or '—')} | {esc(s['rationale'])} |")
L.append("")

L.append("## Data gaps\n")
L.append("- MU — only 137 bars of history: no 200-day MA and no 50/200 cross, treated as neutral; `funding_ref` 5.5e-6 is effectively zero on a thin equity perp, so crowding falls back to neutral on mark premium alone.")
L.append("- SNDK — `funding_ref` is 0 on the equity perp; crowding leans on mark premium and OI alone.")
L.append("- AAPL — `funding_ref` is 0 and mark sits fractionally under index; crowding leans on premium alone at reduced confidence.")
L.append("- PLTR — `funding_ref` is 0 on the equity perp; crowding leans on premium alone.")
L.append("- LIT — only 259 bars of history, so `secular` is declared neutral rather than estimated.")
L.append("- Macro read (carried, not re-reasoned): no broad-dollar update past DTWEXBGS Sep 11 and no percent-above-200-day breadth source; both treated as neutral.")

open(f'/home/hermes/.hermes/profiles/raymond/workspace/janus/reports/{D}.md','w').write("\n".join(L)+"\n")
print("written", len("\n".join(L)))
