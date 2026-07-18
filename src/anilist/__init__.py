"""
AniList API Wrapper — A complete, type-safe Python client for the AniList GraphQL API.

Usage:
    from anilist import AniListClient

    client = AniListClient()
    anime = client.get_media(1)
    print(anime.title.romaji)

    results = client.search_media("Attack on Titan")
    for m in results.nodes:
        print(m.title.english, m.average_score)

    seasonal = client.get_seasonal(2026, MediaSeason.SUMMER)
"""

from .async_client import AsyncAniListClient
from .client import AniListClient
from .exceptions import (
    AniListError,
    AuthenticationError,
    GraphQLError,
    NotFoundError,
    RateLimitError,
    ValidationError,
)
from .models.user import User
from .rate_limiter import AsyncRateLimiter, RateLimiter
from .types import (
    CharacterSort,
    MediaFormat,
    MediaListStatus,
    MediaSeason,
    MediaSort,
    MediaSource,
    MediaStatus,
    ScoreFormat,
    StaffSort,
    UserTitleLanguage,
)

__all__ = [
    "AniListClient",
    "AsyncAniListClient",
    "AsyncRateLimiter",
    "AniListError",
    "AuthenticationError",
    "CharacterSort",
    "GraphQLError",
    "MediaFormat",
    "MediaListStatus",
    "MediaSeason",
    "MediaSort",
    "MediaSource",
    "MediaStatus",
    "NotFoundError",
    "RateLimiter",
    "RateLimitError",
    "ScoreFormat",
    "StaffSort",
    "User",
    "UserTitleLanguage",
    "ValidationError",
]

__version__ = "1.1.1"
