-- 0001_init.sql
-- Initial schema: leads + demos, supporting enums, indexes, updated_at trigger.
-- Run against the DIRECT connection (port 5432), not the pooler:
--   psql "$DATABASE_URL_DIRECT" -f infra/migrations/0001_init.sql

BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ---------------------------------------------------------------------------
-- Enums
-- ---------------------------------------------------------------------------

CREATE TYPE lead_status AS ENUM (
  'discovered',
  'qualified',
  'rejected',
  'demo_ready',
  'contacted',
  'replied',
  'customer',
  'dead'
);

CREATE TYPE deploy_status AS ENUM (
  'pending',
  'live',
  'failed'
);

-- ---------------------------------------------------------------------------
-- Shared trigger function
-- ---------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION set_updated_at() RETURNS trigger AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ---------------------------------------------------------------------------
-- leads
-- ---------------------------------------------------------------------------

CREATE TABLE leads (
  id                   uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  place_id             text NOT NULL UNIQUE,
  name                 text NOT NULL,
  vertical             text NOT NULL,
  category             text,
  neighborhood         text NOT NULL,
  address              text,
  lat                  double precision,
  lng                  double precision,
  phone                text,
  rating               numeric(2,1),
  user_rating_count    integer,
  latest_review_at     timestamptz,
  status               lead_status NOT NULL DEFAULT 'discovered',
  score                integer NOT NULL DEFAULT 0,
  qualification_reason text,
  opt_out              boolean NOT NULL DEFAULT false,
  last_contacted_at    timestamptz,
  places_fetched_at    timestamptz NOT NULL DEFAULT now(),
  raw                  jsonb NOT NULL,
  created_at           timestamptz NOT NULL DEFAULT now(),
  updated_at           timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX leads_status_score_idx  ON leads (status, score DESC);
CREATE INDEX leads_neighborhood_idx  ON leads (neighborhood);
CREATE INDEX leads_vertical_idx      ON leads (vertical);

CREATE TRIGGER leads_set_updated_at
  BEFORE UPDATE ON leads
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- ---------------------------------------------------------------------------
-- demos
-- ---------------------------------------------------------------------------

CREATE TABLE demos (
  id                    uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  lead_id               uuid NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
  slug                  text NOT NULL UNIQUE,
  theme                 text NOT NULL,
  content               jsonb,
  content_generated_at  timestamptz,
  deploy_status         deploy_status NOT NULL DEFAULT 'pending',
  deployed_at           timestamptz,
  view_count            integer NOT NULL DEFAULT 0,
  created_at            timestamptz NOT NULL DEFAULT now(),
  updated_at            timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX demos_lead_id_idx ON demos (lead_id);

CREATE TRIGGER demos_set_updated_at
  BEFORE UPDATE ON demos
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

COMMIT;
