"""Controller: one-time read-only copy of prod (venus) into a local orion_dev schema p2proof_<stamp>, via orion-remote
sql-ro (READ ONLY tx as orion_prod_ro). Never writes to prod. Usage: python3 prod_copy.py <P> <old release dir> <new config worktree>
Writes <P>/schema, <P>/{old,new}/.env (2 lines), <P>/copy.json (per-table counts prod vs local)."""
import json, os, subprocess, sys, time
sys.path.insert(0, os.path.dirname(__file__))
from prod_ro import sql_ro

P, REL, NEWCFG = sys.argv[1], sys.argv[2], sys.argv[3]  # NEWCFG = worktree whose assets/personas/skills the new home uses
URL = 'postgresql://orion_dev@/orion_dev?host=/var/run/postgresql'
os.makedirs(P, exist_ok=False)
S = 'p2proof_' + time.strftime('%Y%m%dt%H%M%Sz', time.gmtime()).lower()
open(f'{P}/schema', 'w').write(S + '\n')
for side in ('old', 'new'):
    os.makedirs(f'{P}/{side}')
    fd = os.open(f'{P}/{side}/.env', os.O_WRONLY | os.O_CREAT, 0o600)
    os.write(fd, f'ORION_DATABASE_URL={URL}\nORION_DB_SCHEMA={S}\n'.encode()); os.close(fd)
    for d in ('assets', 'personas', 'skills'):
        subprocess.run(['cp', '-R', f'{REL if side == "old" else NEWCFG}/{d}', f'{P}/{side}/{d}'], check=True)

def psql(sql, quiet=True):
    r = subprocess.run(['psql', '-U', 'orion_dev', '-d', 'orion_dev', '-v', 'ON_ERROR_STOP=1', '-Atq'], input=sql,
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr[-2000:])
    return r.stdout

def ins(t, rows, off):
    rows = json.loads(rows) if isinstance(rows, str) else rows
    payload = json.dumps(rows)
    tag = '$pj' + str(off) + '$'
    assert tag not in payload
    psql(f'set search_path to "{S}"; begin; set constraints all deferred; '
         f'insert into "{t}" overriding system value select * from json_populate_recordset(null::"{t}", {tag}{payload}{tag}); commit;')

# 1. local schema at prod's migration level, migrated by the prod release itself
env = {**{k: v for k, v in os.environ.items() if not k.startswith('ORION_')}, 'ORION_HOME': f'{P}/old', 'ORION_ENV_FILE': f'{P}/old/.env'}
r = subprocess.run(['node', f'{REL}/dist/cli/index.js', 'db', 'migrate', '--json'], cwd=f'{P}/old', env=env, capture_output=True, text=True)
open(f'{P}/migrate-old.json', 'w').write(r.stdout + r.stderr)
if r.returncode != 0:
    raise SystemExit('migrate failed: ' + r.stderr[-500:])
prod_mig = sql_ro('select max(id) as m from schema_migrations')[0]['m']
local_mig = psql(f'select max(id) from "{S}".schema_migrations').strip()
if str(prod_mig) != local_mig:
    raise SystemExit(f'migration mismatch prod {prod_mig} local {local_mig}')

tables = [r['t'] for r in sql_ro("select c.relname as t from pg_class c join pg_namespace n on n.oid = c.relnamespace "
                                 "where n.nspname = current_schema() and c.relkind = 'r' order by 1")]
counts = {}
PAGE = 1500
psql(f'set search_path to "{S}"; ' + ' '.join(f'truncate "{t}" cascade;' for t in tables if t != 'schema_migrations'))
for t in tables:
    if t == 'schema_migrations':
        continue
    cols = [r['c'] for r in sql_ro(f"select column_name as c from information_schema.columns where table_schema = current_schema() "
                                   f"and table_name = '{t}' order by ordinal_position")]
    if 'id' in cols:
        top = sql_ro(f'select coalesce(max(id), 0)::bigint as m from "{t}"')[0]['m']
        n = sql_ro(f'select count(*)::int as n from "{t}" where id <= {top}')[0]['n']
        last, got, page, buf = -1, 0, 400, []
        while True:
            try:
                rows = sql_ro(f'select coalesce(json_agg(x order by x.id), \'[]\'::json) as j from (select * from "{t}" '
                              f'where id > {last} and id <= {top} order by id limit {page}) x')[0]['j']
            except RuntimeError as e:
                if 'unparseable' in str(e) and page > 1:
                    page = max(1, page // 2); continue   # orion-remote caps output at 1 MB
                raise
            rows = json.loads(rows) if isinstance(rows, str) else rows
            if not rows:
                break
            buf.extend(rows)
            got += len(rows); last = rows[-1]['id']
        if buf:
            ins(t, buf, 0)
    else:
        rows = sql_ro(f'select coalesce(json_agg(x), \'[]\'::json) as j from "{t}" x')[0]['j']
        rows = json.loads(rows) if isinstance(rows, str) else rows
        n = len(rows); got = 0
        if rows:
            ins(t, rows, 0); got = len(rows)
    local = int(psql(f'select count(*) from "{S}"."{t}"').strip())
    counts[t] = {'prod': n, 'copied': got, 'local': local}
    if local != n:
        raise SystemExit(f'{t}: prod {n} local {local}')
# sequences
seqs = psql(f"select format('%I.%I', schemaname, sequencename) || '|' || (select attname from pg_attribute a join pg_depend d on d.refobjid = a.attrelid and d.refobjsubid = a.attnum where d.objid = (quote_ident(schemaname)||'.'||quote_ident(sequencename))::regclass limit 1) || '|' || (select (quote_ident(n.nspname)||'.'||quote_ident(c.relname)) from pg_depend d join pg_class c on c.oid = d.refobjid join pg_namespace n on n.oid = c.relnamespace where d.objid = (quote_ident(schemaname)||'.'||quote_ident(sequencename))::regclass and d.deptype in ('a','i') limit 1) from pg_sequences where schemaname = '{S}'")
for line in seqs.strip().splitlines():
    seq, col, tbl = line.split('|')
    if col and tbl:
        psql(f"select setval('{seq}', greatest(coalesce((select max(\"{col}\") from {tbl}), 0), 1), (select count(*) > 0 from {tbl}))")
json.dump({'schema': S, 'prod_migration': prod_mig, 'tables': counts}, open(f'{P}/copy.json', 'w'), indent=1)
print('copied', S, sum(v['local'] for v in counts.values()), 'rows in', len(counts), 'tables')
