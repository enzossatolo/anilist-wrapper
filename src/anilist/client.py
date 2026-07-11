"""Main AniList API client."""

from __future__ import annotations

from typing import Any, Optional, TypeVar, overload

import httpx

from .exceptions import GraphQLError, RateLimitError
from .models.media import (
    AiringSchedule,
    Media,
    MediaConnection,
    MediaTrend,
    PageInfo,
)
from .models.character import (
    Character,
    CharacterConnection,
    Staff,
    StaffConnection,
    Studio,
    StudioConnection,
)
from .auth import AniListAuth
from .rate_limiter import RateLimiter
from .types import MediaType, MediaFormat, MediaListStatus, MediaSeason, MediaSort, MediaStatus

T = TypeVar("T")

ANILIST_ENDPOINT = "https://graphql.anilist.co"


class AniListClient:
    """Python client for the AniList GraphQL API.

    Usage:
        client = AniListClient()
        anime = client.get_media(1)
        results = client.search_media("Attack on Titan")
        seasonal = client.get_seasonal(2026, MediaSeason.SUMMER)
    """

    def __init__(
        self,
        rate_limit_rpm: float = 80,
        timeout: float = 30.0,
        auth: Optional[AniListAuth] = None,
    ) -> None:
        """
        Args:
            rate_limit_rpm: Max requests per minute (default 80, AniList cap ~90).
            timeout: HTTP request timeout in seconds.
            auth: Optional AniListAuth instance for authenticated requests.
        """
        self._auth = auth
        self._rate_limiter = RateLimiter(rate=rate_limit_rpm)
        self._client = httpx.Client(
            base_url=ANILIST_ENDPOINT,
            timeout=timeout,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self._client.close()

    def __enter__(self) -> "AniListClient":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    # ── Internal ──────────────────────────────────────────────

    def _execute(self, query: str, variables: Optional[dict] = None) -> dict:
        """Execute a GraphQL query with rate limiting and error handling."""
        self._rate_limiter.acquire()
        payload: dict[str, Any] = {"query": query}
        if variables:
            payload["variables"] = variables

        headers = {}
        if self._auth and self._auth.access_token:
            headers["Authorization"] = f"Bearer {self._auth.access_token}"

        response = self._client.post(ANILIST_ENDPOINT, json=payload, headers=headers)

        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 60))
            raise RateLimitError(retry_after)

        response.raise_for_status()
        data: dict = response.json()

        if "errors" in data:
            raise GraphQLError(data["errors"], query)

        return data.get("data", {})

    # ── Media ─────────────────────────────────────────────────

    def get_media(
        self,
        media_id: int,
        *,
        media_type: MediaType = "ANIME",
    ) -> Optional[Media]:
        """Get a single media entry by ID."""
        query = """
        query ($id: Int, $type: MediaType) {
            Media(id: $id, type: $type) {
                id idMal
                title { romaji english native userPreferred }
                type format status
                description(asHtml: false)
                startDate { year month day }
                endDate { year month day }
                season seasonYear seasonInt
                episodes duration chapters volumes
                countryOfOrigin isLicensed source
                hashtag
                trailer { id site thumbnail }
                coverImage { extraLarge large medium color }
                bannerImage
                genres synonyms
                averageScore meanScore popularity trending favourites
                tags { id name description category rank isGeneralSpoiler isMediaSpoiler isAdult }
                isAdult
                nextAiringEpisode { id airingAt timeUntilAiring episode mediaId }
                rankings { id rank type format year season allTime context }
                externalLinks { id url site type language color icon }
                streamingEpisodes { title thumbnail url site }
                siteUrl
            }
        }
        """
        data = self._execute(query, {"id": media_id, "type": media_type})
        media_data = data.get("Media")
        return Media(**media_data) if media_data else None

    def search_media(
        self,
        search: str,
        *,
        media_type: MediaType = "ANIME",
        page: int = 1,
        per_page: int = 10,
        sort: MediaSort = MediaSort.SEARCH_MATCH,
        format_in: Optional[list[MediaFormat]] = None,
        status: Optional[MediaStatus] = None,
        genre: Optional[str] = None,
        is_adult: bool = False,
    ) -> MediaConnection:
        """Search for media by title."""
        query = """
        query ($page: Int, $perPage: Int, $search: String, $type: MediaType,
               $sort: [MediaSort], $format: [MediaFormat], $status: MediaStatus,
               $genre: String, $isAdult: Boolean) {
            Page(page: $page, perPage: $perPage) {
                pageInfo { total perPage currentPage lastPage hasNextPage }
                media(search: $search, type: $type, sort: $sort,
                      format_in: $format, status: $status, genre: $genre,
                      isAdult: $isAdult) {
                    id idMal
                    title { romaji english native userPreferred }
                    format status episodes chapters volumes
                    averageScore meanScore popularity trending favourites
                    coverImage { extraLarge large medium color }
                    season seasonYear
                    genres
                    startDate { year month day }
                    nextAiringEpisode { airingAt episode }
                    isAdult
                    siteUrl
                }
            }
        }
        """
        data = self._execute(query, {
            "page": page,
            "perPage": per_page,
            "search": search,
            "type": media_type,
            "sort": [sort.value],
            "format": [f.value for f in format_in] if format_in else None,
            "status": status.value if status else None,
            "genre": genre,
            "isAdult": is_adult,
        })
        return MediaConnection(**data["Page"])

    def get_seasonal(
        self,
        year: int,
        season: MediaSeason,
        *,
        media_type: MediaType = "ANIME",
        page: int = 1,
        per_page: int = 20,
        sort: MediaSort = MediaSort.POPULARITY_DESC,
    ) -> MediaConnection:
        """Get media for a specific season."""
        query = """
        query ($page: Int, $perPage: Int, $season: MediaSeason, $year: Int,
               $type: MediaType, $sort: [MediaSort]) {
            Page(page: $page, perPage: $perPage) {
                pageInfo { total perPage currentPage lastPage hasNextPage }
                media(season: $season, seasonYear: $year, type: $type, sort: $sort) {
                    id idMal
                    title { romaji english native userPreferred }
                    format status episodes chapters volumes
                    averageScore meanScore popularity trending
                    coverImage { extraLarge large medium color }
                    genres
                    nextAiringEpisode { airingAt episode }
                    isAdult
                    siteUrl
                }
            }
        }
        """
        data = self._execute(query, {
            "page": page,
            "perPage": per_page,
            "season": season.value,
            "year": year,
            "type": media_type,
            "sort": [sort.value],
        })
        return MediaConnection(**data["Page"])

    def get_trending(
        self,
        *,
        media_type: MediaType = "ANIME",
        page: int = 1,
        per_page: int = 20,
    ) -> MediaConnection:
        """Get currently trending media."""
        query = """
        query ($page: Int, $perPage: Int, $type: MediaType) {
            Page(page: $page, perPage: $perPage) {
                pageInfo { total perPage currentPage lastPage hasNextPage }
                media(sort: TRENDING_DESC, type: $type) {
                    id idMal
                    title { romaji english native userPreferred }
                    format status episodes chapters volumes
                    averageScore meanScore popularity trending
                    coverImage { extraLarge large medium color }
                    genres
                    nextAiringEpisode { airingAt episode }
                    isAdult
                    siteUrl
                }
            }
        }
        """
        data = self._execute(query, {
            "page": page,
            "perPage": per_page,
            "type": media_type,
        })
        return MediaConnection(**data["Page"])

    def get_media_rankings(
        self,
        media_id: int,
    ) -> list[dict]:
        """Get rankings for a specific media."""
        query = """
        query ($id: Int) {
            Media(id: $id) {
                id
                rankings {
                    id rank type format year season allTime context
                }
            }
        }
        """
        data = self._execute(query, {"id": media_id})
        media = data.get("Media", {})
        return media.get("rankings", [])

    def get_media_recommendations(
        self,
        media_id: int,
        *,
        page: int = 1,
        per_page: int = 10,
    ) -> dict:
        """Get recommendations based on a media entry."""
        query = """
        query ($id: Int, $page: Int, $perPage: Int) {
            Media(id: $id) {
                id
                recommendations(page: $page, perPage: $perPage, sort: RATING_DESC) {
                    pageInfo { total perPage currentPage lastPage hasNextPage }
                    nodes {
                        id rating userRating
                        mediaRecommendation {
                            id title { romaji english }
                            format averageScore coverImage { medium }
                        }
                    }
                }
            }
        }
        """
        data = self._execute(query, {"id": media_id, "page": page, "perPage": per_page})
        return data.get("Media", {}).get("recommendations", {})

    def get_media_relations(
        self,
        media_id: int,
    ) -> dict:
        """Get related media (sequels, prequels, adaptations, etc.)."""
        query = """
        query ($id: Int) {
            Media(id: $id) {
                id
                relations {
                    edges {
                        id relationType(version: 2)
                        node { id title { romaji english } format type averageScore coverImage { medium } }
                    }
                }
            }
        }
        """
        data = self._execute(query, {"id": media_id})
        return data.get("Media", {}).get("relations", {})

    def get_media_trends(
        self,
        media_id: int,
        *,
        page: int = 1,
        per_page: int = 30,
    ) -> list[MediaTrend]:
        """Get daily trend data for a media entry."""
        query = """
        query ($id: Int, $page: Int, $perPage: Int) {
            Media(id: $id) {
                id
                trends(page: $page, perPage: $perPage, sort: ID_DESC) {
                    nodes {
                        mediaId date trending averageScore popularity inProgress releasing episode
                    }
                }
            }
        }
        """
        data = self._execute(query, {"id": media_id, "page": page, "perPage": per_page})
        trends = data.get("Media", {}).get("trends", {}).get("nodes", [])
        return [MediaTrend(**t) for t in trends]

    # ── Characters ────────────────────────────────────────────

    def get_character(
        self,
        character_id: int,
    ) -> Optional[Character]:
        """Get a single character by ID."""
        query = """
        query ($id: Int) {
            Character(id: $id) {
                id
                name { first middle last full native alternative alternativeSpoiler userPreferred }
                image { large medium }
                description(asHtml: false)
                gender
                dateOfBirth { year month day }
                age bloodType
                favourites
                siteUrl
            }
        }
        """
        data = self._execute(query, {"id": character_id})
        char_data = data.get("Character")
        return Character(**char_data) if char_data else None

    def search_characters(
        self,
        search: str,
        *,
        page: int = 1,
        per_page: int = 10,
    ) -> CharacterConnection:
        """Search for characters by name."""
        query = """
        query ($page: Int, $perPage: Int, $search: String) {
            Page(page: $page, perPage: $perPage) {
                pageInfo { total perPage currentPage lastPage hasNextPage }
                characters(search: $search, sort: SEARCH_MATCH) {
                    id
                    name { full native userPreferred }
                    image { large medium }
                    gender
                    favourites
                    siteUrl
                }
            }
        }
        """
        data = self._execute(query, {
            "page": page,
            "perPage": per_page,
            "search": search,
        })
        return CharacterConnection(**data["Page"])

    def get_media_characters(
        self,
        media_id: int,
        *,
        page: int = 1,
        per_page: int = 10,
        role: Optional[str] = None,  # "MAIN", "SUPPORTING", "BACKGROUND"
    ) -> CharacterConnection:
        """Get characters for a specific media entry."""
        query = """
        query ($id: Int, $page: Int, $perPage: Int, $role: CharacterRole) {
            Media(id: $id) {
                id
                characters(page: $page, perPage: $perPage, sort: ROLE, role: $role) {
                    pageInfo { total perPage currentPage lastPage hasNextPage }
                    nodes {
                        id
                        name { full native userPreferred }
                        image { large medium }
                        gender
                        favourites
                        siteUrl
                    }
                }
            }
        }
        """
        data = self._execute(query, {
            "id": media_id,
            "page": page,
            "perPage": per_page,
            "role": role,
        })
        return CharacterConnection(**data.get("Media", {}).get("characters", {}))

    # ── Staff ─────────────────────────────────────────────────

    def get_staff(
        self,
        staff_id: int,
    ) -> Optional[Staff]:
        """Get a single staff member by ID."""
        query = """
        query ($id: Int) {
            Staff(id: $id) {
                id
                name { first middle last full native alternative userPreferred }
                languageV2
                image { large medium }
                description(asHtml: false)
                primaryOccupations
                gender
                dateOfBirth { year month day }
                dateOfDeath { year month day }
                age
                yearsActive
                homeTown bloodType
                favourites
                siteUrl
            }
        }
        """
        data = self._execute(query, {"id": staff_id})
        staff_data = data.get("Staff")
        return Staff(**staff_data) if staff_data else None

    def get_media_staff(
        self,
        media_id: int,
        *,
        page: int = 1,
        per_page: int = 10,
    ) -> StaffConnection:
        """Get staff for a specific media entry."""
        query = """
        query ($id: Int, $page: Int, $perPage: Int) {
            Media(id: $id) {
                id
                staff(page: $page, perPage: $perPage, sort: RELEVANCE) {
                    pageInfo { total perPage currentPage lastPage hasNextPage }
                    nodes {
                        id
                        name { full native userPreferred }
                        languageV2
                        image { medium }
                        primaryOccupations
                        favourites
                        siteUrl
                    }
                }
            }
        }
        """
        data = self._execute(query, {
            "id": media_id,
            "page": page,
            "perPage": per_page,
        })
        return StaffConnection(**data.get("Media", {}).get("staff", {}))

    # ── Studios ───────────────────────────────────────────────

    def search_studios(
        self,
        search: str,
    ) -> Optional[Studio]:
        """Search for a studio by name."""
        query = """
        query ($search: String) {
            Studio(search: $search) {
                id
                name
                isAnimationStudio
                favourites
                siteUrl
            }
        }
        """
        data = self._execute(query, {"search": search})
        studio_data = data.get("Studio")
        return Studio(**studio_data) if studio_data else None

    def get_media_studios(
        self,
        media_id: int,
    ) -> StudioConnection:
        """Get studios for a specific media entry."""
        query = """
        query ($id: Int) {
            Media(id: $id) {
                id
                studios {
                    nodes {
                        id name isAnimationStudio favourites siteUrl
                    }
                }
            }
        }
        """
        data = self._execute(query, {"id": media_id})
        return StudioConnection(**data.get("Media", {}).get("studios", {}))

    # ── Airing Schedule ───────────────────────────────────────

    def get_airing_schedule(
        self,
        *,
        page: int = 1,
        per_page: int = 20,
        airing_at_greater: Optional[int] = None,
        airing_at_lesser: Optional[int] = None,
        not_yet_aired: bool = True,
        media_type: MediaType = "ANIME",
    ) -> dict:
        """Get upcoming airing schedules.

        Args:
            airing_at_greater: Unix timestamp — filter after this time.
            airing_at_lesser: Unix timestamp — filter before this time.
            not_yet_aired: Only include episodes that haven't aired yet.
        """
        query = """
        query ($page: Int, $perPage: Int, $airingAtGreater: Int,
               $airingAtLesser: Int, $notYetAired: Boolean, $type: MediaType) {
            Page(page: $page, perPage: $perPage) {
                pageInfo { total perPage currentPage lastPage hasNextPage }
                airingSchedules(
                    airingAt_greater: $airingAtGreater,
                    airingAt_lesser: $airingAtLesser,
                    notYetAired: $notYetAired,
                    sort: TIME
                ) {
                    id
                    airingAt
                    episode
                    mediaId
                    media {
                        id
                        title { romaji english }
                        format
                        status
                        coverImage { medium }
                    }
                }
            }
        }
        """
        data = self._execute(query, {
            "page": page,
            "perPage": per_page,
            "airingAtGreater": airing_at_greater,
            "airingAtLesser": airing_at_lesser,
            "notYetAired": not_yet_aired,
            "type": media_type,
        })
        return data["Page"]

    # ── Genre / Tag Collections ───────────────────────────────

    def get_genres(self) -> list[str]:
        """Get all possible media genres."""
        query = "query { GenreCollection }"
        data = self._execute(query)
        return data.get("GenreCollection", [])

    def get_media_tags(
        self,
        *,
        status: int = 1,  # 0=rejected, 1=pending, 2=accepted
    ) -> list[dict]:
        """Get all possible media tags."""
        query = """
        query ($status: Int) {
            MediaTagCollection(status: $status) {
                id name description category isAdult isGeneralSpoiler
            }
        }
        """
        data = self._execute(query, {"status": status})
        return data.get("MediaTagCollection", [])

    # ── Site Statistics ──────────────────────────────────────

    def get_site_statistics(self) -> dict:
        """Get AniList site-wide statistics."""
        query = """
        query {
            SiteStatistics {
                anime(first: 5, sort: COUNT_DESC) {
                    nodes { count }
                }
                manga(first: 5, sort: COUNT_DESC) {
                    nodes { count }
                }
                users(first: 5, sort: COUNT_DESC) {
                    nodes { count }
                }
            }
        }
        """
        data = self._execute(query)
        return data.get("SiteStatistics", {})
