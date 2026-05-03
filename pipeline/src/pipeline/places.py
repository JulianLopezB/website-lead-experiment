from typing import Any

import httpx

from .models import PlaceDetails, PlaceNearby

_BASE_URL = "https://places.googleapis.com/v1"

NEARBY_FIELD_MASK = ",".join(
    [
        "places.id",
        "places.displayName",
        "places.primaryType",
        "places.types",
        "places.websiteUri",
        "places.rating",
        "places.userRatingCount",
    ]
)

DETAILS_FIELD_MASK = ",".join(
    [
        "id",
        "displayName",
        "primaryType",
        "types",
        "websiteUri",
        "rating",
        "userRatingCount",
        "formattedAddress",
        "location",
        "internationalPhoneNumber",
        "reviews",
    ]
)


class PlacesClient:
    def __init__(self, api_key: str, *, timeout: float = 15.0) -> None:
        self._client = httpx.Client(
            base_url=_BASE_URL,
            timeout=timeout,
            headers={
                "X-Goog-Api-Key": api_key,
                "Content-Type": "application/json",
            },
        )

    def __enter__(self) -> "PlacesClient":
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()

    def close(self) -> None:
        self._client.close()

    def search_nearby(
        self,
        *,
        latitude: float,
        longitude: float,
        radius_m: float,
        included_primary_types: list[str],
        max_results: int = 20,
    ) -> tuple[list[PlaceNearby], list[dict[str, Any]]]:
        body = {
            "includedPrimaryTypes": included_primary_types,
            "maxResultCount": max_results,
            "locationRestriction": {
                "circle": {
                    "center": {"latitude": latitude, "longitude": longitude},
                    "radius": radius_m,
                }
            },
        }
        resp = self._client.post(
            "/places:searchNearby",
            json=body,
            headers={"X-Goog-FieldMask": NEARBY_FIELD_MASK},
        )
        resp.raise_for_status()
        payload = resp.json()
        raw_places: list[dict[str, Any]] = payload.get("places", []) or []
        parsed = [PlaceNearby.model_validate(p) for p in raw_places]
        return parsed, raw_places

    def place_details(self, place_id: str) -> tuple[PlaceDetails, dict[str, Any]]:
        resp = self._client.get(
            f"/places/{place_id}",
            headers={"X-Goog-FieldMask": DETAILS_FIELD_MASK},
        )
        resp.raise_for_status()
        payload: dict[str, Any] = resp.json()
        return PlaceDetails.model_validate(payload), payload
