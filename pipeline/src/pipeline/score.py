from datetime import datetime, timedelta
from typing import Optional

from .models import PlaceDetails, PlaceNearby, Review

RATING_FLOOR = 3.8
USER_RATING_COUNT_FLOOR = 15
RECENT_REVIEW_MAX_AGE_DAYS = 60


def cheap_reject(p: PlaceNearby) -> Optional[str]:
    """Return a rejection reason from Nearby fields, or None if it survives."""
    if p.website_uri:
        return f"has website ({p.website_uri})"
    if p.rating is None or p.rating < RATING_FLOOR:
        return f"rating {p.rating} below floor {RATING_FLOOR}"
    if p.user_rating_count is None or p.user_rating_count < USER_RATING_COUNT_FLOOR:
        return f"{p.user_rating_count} reviews below floor {USER_RATING_COUNT_FLOOR}"
    return None


def latest_review_at(d: PlaceDetails) -> Optional[datetime]:
    times = [r.publish_time for r in d.reviews if isinstance(r, Review)]
    return max(times) if times else None


def stale_review_reason(latest: Optional[datetime], *, now: datetime) -> Optional[str]:
    if latest is None:
        return f"no reviews returned (max age {RECENT_REVIEW_MAX_AGE_DAYS} days)"
    age_days = (now - latest).days
    if age_days > RECENT_REVIEW_MAX_AGE_DAYS:
        return f"latest review {age_days} days ago, floor {RECENT_REVIEW_MAX_AGE_DAYS}"
    return None


def compute_score(d: PlaceDetails, latest: Optional[datetime], *, now: datetime) -> int:
    rating_score = round((float(d.rating or 0.0) - 3.5) * 100)
    review_score = min(d.user_rating_count or 0, 200)
    if latest is None:
        recency = 0
    else:
        age_days = (now - latest).days
        if age_days <= 14:
            recency = 50
        elif age_days <= 30:
            recency = 25
        else:
            recency = 0
    return rating_score + review_score + recency


def qualified_reason(d: PlaceDetails, latest: Optional[datetime], *, now: datetime) -> str:
    parts = [f"rating {d.rating}", f"{d.user_rating_count} reviews"]
    if latest is not None:
        parts.append(f"last review {(now - latest).days} days ago")
    return "qualified: " + ", ".join(parts)
