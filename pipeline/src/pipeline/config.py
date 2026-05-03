import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

_REPO_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(_REPO_ROOT / ".env")


@dataclass(frozen=True)
class Settings:
    database_url: str
    google_places_api_key: str


def load_settings() -> Settings:
    db = os.environ.get("DATABASE_URL")
    if not db:
        raise RuntimeError(
            "DATABASE_URL not set; expected the pooled Supabase URL on port 6543"
        )
    key = os.environ.get("GOOGLE_PLACES_API_KEY")
    if not key:
        raise RuntimeError("GOOGLE_PLACES_API_KEY not set")
    return Settings(database_url=db, google_places_api_key=key)
