### Task 10 (gate G3, own `-- breaking` release): contract migration

**Files:** `src/db/pg/migrations/0006_provenance_not_null.sql` (first line `-- breaking`): `SET NOT NULL` on `method`,
`source_type`, `locator`, `code_version`, `config_hash`, then `DROP COLUMN source` and the reader changes. **Do not
build until** one release has run with 0004-0005 on staging, `db backfill-provenance` left 0 null rows there, and Mike
says go. Prod runs it only after the cutover, with `--breaking`.

