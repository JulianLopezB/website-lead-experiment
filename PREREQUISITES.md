# Prerequisites

What you need to provision **before** each phase of the build can run.
Phases are sequential — don't worry about phase N+1 until phase N is working.

## Phase 1 — schema (current)

- [ ] Supabase project created
- [ ] `DATABASE_URL_DIRECT` (port 5432) — used **only** for running migrations
- [ ] `DATABASE_URL` (pooled, port 6543) — used by pipeline + engine at runtime
- [ ] Both URLs copied into local `.env` (see `.env.example`)

## Phase 2 — `pipeline/discover.py`

- [ ] Google Cloud project
- [ ] Places API (New) enabled on that project
- [ ] Billing enabled on that project (Places API requires it even for free-tier usage)
- [ ] API key with Places API restriction + IP/referrer restriction if possible
- [ ] `GOOGLE_PLACES_API_KEY` in `.env`

## Phase 3 — `engine/`

- [ ] Vercel account, repo linked
- [ ] No custom domain required yet — demos served from `*.vercel.app`
- [ ] `DATABASE_URL` (pooled) added to Vercel project env

## Phase 4 — `pipeline/generate.py`

- [ ] Anthropic API key with access to `claude-sonnet-4-5`
- [ ] `ANTHROPIC_API_KEY` in `.env`
- [ ] Vercel deploy hook URL (if we choose to trigger redeploys from the pipeline)

## Phase 5 — `pipeline/outreach.py`

- [ ] Custom domain purchased (required for verified Resend sending domain)
- [ ] Resend account
- [ ] Sending domain verified in Resend (DNS records added)
- [ ] `RESEND_API_KEY` in `.env`
- [ ] Reply-to inbox configured

## Future / TODO (not blocking any phase)

- 180-day retention cleanup job for `leads` where `status IN ('rejected','dead')` and `updated_at < now() - interval '180 days'`. Will likely live as a separate `pipeline/cleanup.py` cron.
- GitHub Actions cron wiring for `discover.py` / `generate.py` / `outreach.py`. Manual runs only until each phase is validated end-to-end.
- Opt-out keyword handler on inbound email replies (`baja`, `no contactar`, `unsubscribe` → set `leads.opt_out=true`).
