"""Read-only prod queries via orion-remote sql-ro (prod: orion_prod_ro, READ ONLY tx, 30 s). Never writes."""
import json, shlex, subprocess, sys

SSH = ['ssh', '-i', '/home/hermes/.ssh/orion-prod_ed25519', '-o', 'IdentitiesOnly=yes', '-o', 'BatchMode=yes',
       'orion-prod@192.168.0.12']


def sql_ro(query: str):
    out = subprocess.run(SSH + ['sql-ro ' + shlex.quote(query)], capture_output=True, text=True, timeout=120)
    try:
        d = json.loads(out.stdout)
    except Exception:
        raise RuntimeError(f'sql-ro: unparseable output (exit {out.returncode}): {out.stdout[:300]} {out.stderr[:300]}')
    if isinstance(d, dict) and isinstance(d.get('error'), dict):
        raise RuntimeError(f"sql-ro error: {d['error']}")
    return d['rows']


if __name__ == '__main__':
    print(json.dumps(sql_ro(sys.argv[1]), indent=1)[:4000])
