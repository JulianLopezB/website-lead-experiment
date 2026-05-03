# infra/

Database schema, migrations, and shared types for the lead-gen pipeline +
engine.

## Layout

```
infra/
├── migrations/
│   └── 0001_init.sql   # leads + demos + enums + indexes + updated_at trigger
├── schema.sql          # canonical reference, regenerated from live DB
└── README.md
```

## Running migrations

Migrations apply DDL, so they need the **direct** Postgres connection
(port 5432), not the pooler. The pooler at port 6543 doesn't support all DDL
operations and shouldn't be used for migrations.

```bash
# from repo root, with .env loaded
psql "$DATABASE_URL_DIRECT" -f infra/migrations/0001_init.sql
```

Each migration is wrapped in `BEGIN; ... COMMIT;`, so a partial failure won't
leave the database half-built.

## Verifying

```bash
psql "$DATABASE_URL_DIRECT" -c '\d leads'
psql "$DATABASE_URL_DIRECT" -c '\d demos'
psql "$DATABASE_URL_DIRECT" -c "SELECT typname, enumlabel FROM pg_type t JOIN pg_enum e ON t.oid = e.enumtypid WHERE typname IN ('lead_status', 'deploy_status') ORDER BY typname, e.enumsortorder;"
```

## Regenerating `schema.sql`

After adding a new migration:

```bash
pg_dump --schema-only --no-owner --no-privileges "$DATABASE_URL_DIRECT" > infra/schema.sql
```

`schema.sql` is for code review and onboarding only — never apply it to a live
database directly. Use the numbered files in `migrations/`.

## Conventions

- Migrations are append-only and numbered `NNNN_description.sql`. Never edit a
  shipped migration; write a new one.
- Every mutable table has `created_at`, `updated_at`, and a
  `BEFORE UPDATE` trigger calling `set_updated_at()`.
- Use `jsonb` (not `json`) for any JSON column.
- Enum changes (adding values) go in their own migration; renaming/removing
  values requires a multi-step migration plan.

## Shared types

`infra/types/` will hold TypeScript (for the engine) and pydantic (for the
pipeline) representations of the schema. Empty until phase 2 (pydantic) and
phase 3 (TypeScript).
