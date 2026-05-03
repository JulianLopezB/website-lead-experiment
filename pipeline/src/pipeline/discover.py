import sys
from datetime import datetime, timezone
from typing import Any

from . import db
from .config import load_settings
from .models import LeadRow, PlaceDetails, PlaceNearby
from .places import PlacesClient
from .score import (
    cheap_reject,
    compute_score,
    latest_review_at,
    qualified_reason,
    stale_review_reason,
)

NEIGHBORHOOD = "chamberi"
VERTICAL = "food_service"
CENTER_LAT = 40.4378
CENTER_LNG = -3.7090
RADIUS_M = 800.0
PRIMARY_TYPES = ["restaurant", "cafe", "bar", "bakery"]
TARGET_QUALIFIED = 10


def log(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


def main() -> int:
    settings = load_settings()
    now = datetime.now(timezone.utc)

    funnel = {
        "discovered": 0,
        "rejected_website": 0,
        "rejected_rating": 0,
        "rejected_review_count": 0,
        "rejected_stale_reviews": 0,
        "qualified": 0,
        "errors": 0,
    }

    nearby_by_id: dict[str, PlaceNearby] = {}
    nearby_raw: dict[str, dict[str, Any]] = {}
    nearby_type: dict[str, str] = {}

    with PlacesClient(settings.google_places_api_key) as places, db.connect(
        settings.database_url
    ) as conn:
        for ptype in PRIMARY_TYPES:
            log(f"[nearby] type={ptype} center=({CENTER_LAT},{CENTER_LNG}) r={RADIUS_M}m")
            parsed, raw_list = places.search_nearby(
                latitude=CENTER_LAT,
                longitude=CENTER_LNG,
                radius_m=RADIUS_M,
                included_primary_types=[ptype],
            )
            log(f"[nearby] type={ptype} returned {len(parsed)} places")
            for place, raw_place in zip(parsed, raw_list):
                if place.id in nearby_by_id:
                    continue
                nearby_by_id[place.id] = place
                nearby_raw[place.id] = {"nearby": raw_place}
                nearby_type[place.id] = ptype

        funnel["discovered"] = len(nearby_by_id)
        log(f"[nearby] {len(nearby_by_id)} unique places after dedup")

        survivors: list[str] = []
        for place_id, place in nearby_by_id.items():
            reason = cheap_reject(place)
            if reason is None:
                survivors.append(place_id)
                continue
            if "website" in reason:
                funnel["rejected_website"] += 1
            elif "rating" in reason:
                funnel["rejected_rating"] += 1
            else:
                funnel["rejected_review_count"] += 1
            row = LeadRow(
                place_id=place.id,
                name=place.name,
                vertical=VERTICAL,
                category=nearby_type[place_id],
                neighborhood=NEIGHBORHOOD,
                address=None,
                lat=None,
                lng=None,
                phone=None,
                rating=place.rating,
                user_rating_count=place.user_rating_count,
                latest_review_at=None,
                status="rejected",
                score=0,
                qualification_reason=f"rejected: {reason}",
                raw=nearby_raw[place_id],
            )
            try:
                db.upsert_lead(conn, row)
                conn.commit()
                log(f"[reject] {place.name}: {reason}")
            except Exception as e:
                conn.rollback()
                funnel["errors"] += 1
                log(f"[upsert][error] {place.name}: {e}")

        log(f"[filter] {len(survivors)} survivors after cheap reject")

        for place_id in survivors:
            place = nearby_by_id[place_id]
            try:
                details, raw_details = places.place_details(place_id)
            except Exception as e:
                funnel["errors"] += 1
                log(f"[details][error] {place.name}: {e}")
                continue

            latest = latest_review_at(details)
            stale = stale_review_reason(latest, now=now)
            raw = {**nearby_raw[place_id], "details": raw_details}

            if stale:
                funnel["rejected_stale_reviews"] += 1
                row = _row_from_details(
                    details=details,
                    fallback_category=nearby_type[place_id],
                    status="rejected",
                    qualification_reason=f"rejected: {stale}",
                    score_value=0,
                    latest=latest,
                    raw=raw,
                )
                log(f"[reject-stale] {details.name}: {stale}")
            else:
                funnel["qualified"] += 1
                s = compute_score(details, latest, now=now)
                row = _row_from_details(
                    details=details,
                    fallback_category=nearby_type[place_id],
                    status="qualified",
                    qualification_reason=qualified_reason(details, latest, now=now),
                    score_value=s,
                    latest=latest,
                    raw=raw,
                )
                log(f"[qualify] {details.name}: score={s}, {row.qualification_reason}")

            try:
                db.upsert_lead(conn, row)
                conn.commit()
            except Exception as e:
                conn.rollback()
                funnel["errors"] += 1
                log(f"[upsert][error] {details.name}: {e}")

        in_db_qualified = db.count_qualified(conn)

    log("---")
    log("FUNNEL:")
    for k, v in funnel.items():
        log(f"  {k}: {v}")
    log(f"qualified rows in DB: {in_db_qualified}")

    if in_db_qualified >= TARGET_QUALIFIED:
        log(f"OK: hit target of {TARGET_QUALIFIED} qualified")
    else:
        log(f"WARN: under target {TARGET_QUALIFIED} qualified — consider widening search")
    return 0


def _row_from_details(
    *,
    details: PlaceDetails,
    fallback_category: str,
    status: str,
    qualification_reason: str,
    score_value: int,
    latest: datetime | None,
    raw: dict[str, Any],
) -> LeadRow:
    return LeadRow(
        place_id=details.id,
        name=details.name,
        vertical=VERTICAL,
        category=details.primary_type or fallback_category,
        neighborhood=NEIGHBORHOOD,
        address=details.formatted_address,
        lat=details.location.latitude if details.location else None,
        lng=details.location.longitude if details.location else None,
        phone=details.international_phone_number,
        rating=details.rating,
        user_rating_count=details.user_rating_count,
        latest_review_at=latest,
        status=status,
        score=score_value,
        qualification_reason=qualification_reason,
        raw=raw,
    )


if __name__ == "__main__":
    sys.exit(main())
