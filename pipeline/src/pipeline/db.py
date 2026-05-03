from typing import Any

import psycopg
from psycopg.types.json import Jsonb

from .models import LeadRow

_UPSERT_LEAD = """
INSERT INTO leads (
    place_id, name, vertical, category, neighborhood, address,
    lat, lng, phone, rating, user_rating_count, latest_review_at,
    status, score, qualification_reason, raw, places_fetched_at
) VALUES (
    %(place_id)s, %(name)s, %(vertical)s, %(category)s, %(neighborhood)s, %(address)s,
    %(lat)s, %(lng)s, %(phone)s, %(rating)s, %(user_rating_count)s, %(latest_review_at)s,
    %(status)s, %(score)s, %(qualification_reason)s, %(raw)s, now()
)
ON CONFLICT (place_id) DO UPDATE SET
    name                 = EXCLUDED.name,
    rating               = EXCLUDED.rating,
    user_rating_count    = EXCLUDED.user_rating_count,
    latest_review_at     = EXCLUDED.latest_review_at,
    phone                = EXCLUDED.phone,
    address              = EXCLUDED.address,
    lat                  = EXCLUDED.lat,
    lng                  = EXCLUDED.lng,
    raw                  = EXCLUDED.raw,
    places_fetched_at    = now(),
    qualification_reason = EXCLUDED.qualification_reason,
    score                = EXCLUDED.score,
    status = CASE
        WHEN leads.status IN ('demo_ready','contacted','replied','customer','dead')
            THEN leads.status
        ELSE EXCLUDED.status::lead_status
    END
WHERE leads.opt_out = false
"""

_COUNT_QUALIFIED = "SELECT count(*) FROM leads WHERE status = 'qualified'"


def connect(database_url: str) -> psycopg.Connection[Any]:
    return psycopg.connect(database_url)


def upsert_lead(conn: psycopg.Connection[Any], row: LeadRow) -> None:
    params: dict[str, Any] = {
        "place_id": row.place_id,
        "name": row.name,
        "vertical": row.vertical,
        "category": row.category,
        "neighborhood": row.neighborhood,
        "address": row.address,
        "lat": row.lat,
        "lng": row.lng,
        "phone": row.phone,
        "rating": row.rating,
        "user_rating_count": row.user_rating_count,
        "latest_review_at": row.latest_review_at,
        "status": row.status,
        "score": row.score,
        "qualification_reason": row.qualification_reason,
        "raw": Jsonb(row.raw),
    }
    with conn.cursor() as cur:
        cur.execute(_UPSERT_LEAD, params)


def count_qualified(conn: psycopg.Connection[Any]) -> int:
    with conn.cursor() as cur:
        cur.execute(_COUNT_QUALIFIED)
        result = cur.fetchone()
    return int(result[0]) if result else 0
