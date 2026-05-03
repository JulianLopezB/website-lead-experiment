# pipeline/

Python scripts that drive the lead-gen funnel.

## Setup

Requires Python 3.11+ and [`uv`](https://docs.astral.sh/uv/).

```bash
cd pipeline
uv sync
```

`.env` lives at the repo root (one level up). See `.env.example` for required
variables. `pipeline/config.py` loads it automatically.

## Phase 2 — `discover`

Pulls food-service businesses near Chamberí from Google Places, qualifies or
rejects each one against the rules below, and writes the full funnel to the
`leads` table. Idempotent: re-running updates existing rows by `place_id`,
and never downgrades rows that have moved past `qualified` in the funnel.

Run from the `pipeline/` directory:

```bash
uv run python -m pipeline.discover
```

Output goes to stderr — one line per place, plus a final funnel summary.

### Constants (hardcoded for now)

- Center: `40.4378, -3.7090` (Chamberí), 800 m radius
- Primary types: `restaurant`, `cafe`, `bar`, `bakery`
- Stored under vertical = `food_service`, neighborhood = `chamberi`
- Target: ≥ 10 rows with `status = 'qualified'`

### Qualification rules

A place is **qualified** iff:

- `websiteUri` is absent (any URL — including Facebook/Instagram — disqualifies)
- `rating >= 3.8`
- `userRatingCount >= 15`
- newest review's `publishTime` is within the last 60 days

Anything that fails is written with `status='rejected'` and a human-readable
`qualification_reason`. Rejected rows are visible in the funnel — they are
never silently dropped.

### Cost-optimized API call shape

- One **Nearby Search** (Pro tier field mask) per primary type, returning up to
  20 places each. Field mask covers all fields needed for the cheap-rejection
  filter — businesses with a `websiteUri` or sub-floor rating/review-count are
  rejected without a Place Details call.
- One **Place Details** (Preferred tier — includes `reviews`) per survivor.

### Verifying the run

```bash
psql "$DATABASE_URL_DIRECT" -c "
  SELECT status, count(*) FROM leads GROUP BY status ORDER BY 2 DESC;
"

psql "$DATABASE_URL_DIRECT" -c "
  SELECT name, rating, user_rating_count, score, qualification_reason
  FROM leads
  WHERE status = 'qualified'
  ORDER BY score DESC
  LIMIT 10;
"
```

### When `discover` underdelivers (< 10 qualified)

Plan B (not yet built): split Chamberí into 4 overlapping sub-circles and
re-sweep. Will add only if the simple search proves insufficient.
