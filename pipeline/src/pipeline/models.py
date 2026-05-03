from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class LatLng(BaseModel):
    latitude: float
    longitude: float


class DisplayName(BaseModel):
    text: str
    language_code: Optional[str] = Field(default=None, alias="languageCode")

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class Review(BaseModel):
    publish_time: datetime = Field(alias="publishTime")
    rating: Optional[float] = None

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class PlaceNearby(BaseModel):
    id: str
    display_name: DisplayName = Field(alias="displayName")
    primary_type: Optional[str] = Field(default=None, alias="primaryType")
    types: list[str] = Field(default_factory=list)
    website_uri: Optional[str] = Field(default=None, alias="websiteUri")
    rating: Optional[float] = None
    user_rating_count: Optional[int] = Field(default=None, alias="userRatingCount")

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    @property
    def name(self) -> str:
        return self.display_name.text


class PlaceDetails(PlaceNearby):
    formatted_address: Optional[str] = Field(default=None, alias="formattedAddress")
    location: Optional[LatLng] = None
    international_phone_number: Optional[str] = Field(
        default=None, alias="internationalPhoneNumber"
    )
    reviews: list[Review] = Field(default_factory=list)

    model_config = ConfigDict(populate_by_name=True, extra="allow")


@dataclass
class LeadRow:
    place_id: str
    name: str
    vertical: str
    category: Optional[str]
    neighborhood: str
    address: Optional[str]
    lat: Optional[float]
    lng: Optional[float]
    phone: Optional[str]
    rating: Optional[float]
    user_rating_count: Optional[int]
    latest_review_at: Optional[datetime]
    status: str
    score: int
    qualification_reason: str
    raw: dict[str, Any]
