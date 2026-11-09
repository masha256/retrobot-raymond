import json, subprocess
ssh = ['ssh', '-i', '/home/hermes/.ssh/orion-prod_ed25519', '-o', 'IdentitiesOnly=yes', '-o', 'BatchMode=yes',
       '-o', 'ConnectTimeout=15', 'orion-prod@192.168.0.12']
r = subprocess.run(ssh + ['report', 'yield', 'aero'], capture_output=True, text=True, timeout=120)
d = json.loads(r.stdout); d = d.get('report', d)
i = d.get('incomeStatement') or {}
print('day', d.get('day'), 'price', d.get('price'), 'mcap', d.get('marketCap'), 'fdv', d.get('fdv'))
print('supply', json.dumps(i.get('perToken') or {})[:300])
print('dilution', json.dumps(i.get('dilution'))[:300])
print('yields', json.dumps(i.get('yields'))[:300])
print('revenue', (i.get('revenue') or {}).get('annualized'), 'holders', (i.get('holders') or {}).get('annualized'))
r = subprocess.run(ssh + ['data', 'show', 'aero'], capture_output=True, text=True, timeout=120)
print(r.stdout[:2500])
