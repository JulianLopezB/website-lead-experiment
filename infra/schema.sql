-- schema.sql
-- Canonical reference for the current database schema.
-- Identical to the cumulative result of all migrations under infra/migrations/.
-- Regenerate after future migrations with:
--   pg_dump --schema-only --no-owner --no-privileges "$DATABASE_URL_DIRECT" > infra/schema.sql
--
-- Do NOT apply this file directly to a live database — use the numbered
-- migrations under infra/migrations/ instead. This file is for code review,
-- diffing, and onboarding.

CREATE EXTENSION IF NOT EXISTS pgcrypto;

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

CREATE OR REPLACE FUNCTION set_updated_at() RETURNS trigger AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

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
