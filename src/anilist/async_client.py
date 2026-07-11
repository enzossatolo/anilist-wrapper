"""Async AniList API client."""

from __future__ import annotations

from typing import Any, Optional

import httpx

from .client import ANILIST_ENDPOINT
from .exceptions import GraphQLError, RateLimitError
from .models.media import (
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
from .models.user import User
from .auth import AniListAuth
from .rate_limiter import AsyncRateLimiter
from .types import MediaType, MediaFormat, MediaSeason, MediaSort, MediaStatus


class AsyncAniListClient:
    """Async Python client for the AniList GraphQL API.

    Usage:
        async with AsyncAniListClient() as client:
            anime = await client.get_media(1)
    """

    def __init__(
        self,
        rate_limit_rpm: int = 40,
        timeout: float = 30.0,
        auth: Optional[AniListAuth] = None,
    ) -> None:
        self._auth = auth
        self._rate_limiter = AsyncRateLimiter(rate=rate_limit_rpm)
        self._client = httpx.AsyncClient(
            base_url=ANILIST_ENDPOINT,
            timeout=timeout,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> "AsyncAniListClient":
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

    async def _execute(self, query: str, variables: Optional[dict] = None) -> dict:
        await self._rate_limiter.acquire()
        payload: dict[str, Any] = {"query": query}
        if variables:
            payload["variables"] = variables

        headers = {}
        if self._auth and self._auth.access_token:
            headers["Authorization"] = f"Bearer {self._auth.access_token}"

        response = await self._client.post(ANILIST_ENDPOINT, json=payload, headers=headers)
        if response.status_code == 429:
            raise RateLimitError(int(response.headers.get("Retry-After", 60)))

        # Treat 404 as "not found" — return empty data so callers handle None gracefully
        if response.status_code == 404:
            return {}

        # Treat 500 as transient server error with a hint to retry
        if response.status_code >= 500:
            raise GraphQLError(
                [{"message": f"AniList server error (HTTP {response.status_code}). Try again later."}],
                query,
            )

        if response.status_code >= 400:
            try:
                body = response.json()
                errors = body.get("errors", [{"message": response.text}])
            except Exception:
                errors = [{"message": f"HTTP {response.status_code}: {response.text[:500]}"}]
            raise GraphQLError(errors, query)

        data: dict = response.json()
        if "errors" in data:
            raise GraphQLError(data["errors"], query)
        return data.get("data", {})

    # ── Media ──

    async def get_media(self, media_id: int, *, media_type: MediaType = "ANIME") -> Optional[Media]:
        q = """query($id:Int,$type:MediaType){Media(id:$id,type:$type){id idMal title{romaji english native userPreferred}type format status description(asHtml:false)startDate{year month day}endDate{year month day}season seasonYear seasonInt episodes duration chapters volumes countryOfOrigin isLicensed source hashtag trailer{id site thumbnail}coverImage{extraLarge large medium color}bannerImage genres synonyms averageScore meanScore popularity trending favourites tags{id name description category rank isGeneralSpoiler isMediaSpoiler isAdult}isAdult nextAiringEpisode{id airingAt timeUntilAiring episode mediaId}rankings{id rank type format year season allTime context}externalLinks{id url site type language color icon}streamingEpisodes{title thumbnail url site}siteUrl}}"""
        d = await self._execute(q, {"id": media_id, "type": media_type})
        return Media(**d["Media"]) if d.get("Media") else None

    async def search_media(self, query: str, *, media_type: MediaType = "ANIME", page: int = 1, per_page: int = 10, sort: MediaSort = MediaSort.SEARCH_MATCH, format_in: Optional[list[MediaFormat]] = None, status: Optional[MediaStatus] = None, genre: Optional[str] = None, is_adult: bool = False) -> MediaConnection:
        q = """query($p:Int,$pp:Int,$s:String,$t:MediaType,$so:[MediaSort],$f:[MediaFormat],$st:MediaStatus,$g:String,$ad:Boolean){Page(page:$p,perPage:$pp){pageInfo{total perPage currentPage lastPage hasNextPage}media(search:$s,type:$t,sort:$so,format_in:$f,status:$st,genre:$g,isAdult:$ad){id idMal title{romaji english native userPreferred}format status episodes chapters volumes averageScore meanScore popularity trending favourites coverImage{extraLarge large medium color}season seasonYear genres startDate{year month day}nextAiringEpisode{airingAt episode}isAdult siteUrl}}}"""
        d = await self._execute(q, {"p": page, "pp": per_page, "s": query, "t": media_type, "so": [sort.value], "f": [f.value for f in format_in] if format_in else None, "st": status.value if status else None, "g": genre, "ad": is_adult})
        return MediaConnection(**d["Page"])

    async def get_seasonal(self, year: int, season: MediaSeason, *, media_type: MediaType = "ANIME", page: int = 1, per_page: int = 20, sort: MediaSort = MediaSort.POPULARITY_DESC) -> MediaConnection:
        q = """query($p:Int,$pp:Int,$s:MediaSeason,$y:Int,$t:MediaType,$so:[MediaSort]){Page(page:$p,perPage:$pp){pageInfo{total perPage currentPage lastPage hasNextPage}media(season:$s,seasonYear:$y,type:$t,sort:$so){id idMal title{romaji english native userPreferred}format status episodes chapters volumes averageScore meanScore popularity trending coverImage{extraLarge large medium color}genres nextAiringEpisode{airingAt episode}isAdult siteUrl}}}"""
        d = await self._execute(q, {"p": page, "pp": per_page, "s": season.value, "y": year, "t": media_type, "so": [sort.value]})
        return MediaConnection(**d["Page"])

    async def get_trending(self, *, media_type: MediaType = "ANIME", page: int = 1, per_page: int = 20) -> MediaConnection:
        q = """query($p:Int,$pp:Int,$t:MediaType){Page(page:$p,perPage:$pp){pageInfo{total perPage currentPage lastPage hasNextPage}media(sort:TRENDING_DESC,type:$t){id idMal title{romaji english native userPreferred}format status episodes chapters volumes averageScore meanScore popularity trending coverImage{extraLarge large medium color}genres nextAiringEpisode{airingAt episode}isAdult siteUrl}}}"""
        d = await self._execute(q, {"p": page, "pp": per_page, "t": media_type})
        return MediaConnection(**d["Page"])

    # ── Characters ──

    async def get_character(self, character_id: int) -> Optional[Character]:
        q = """query($id:Int){Character(id:$id){id name{first middle last full native alternative alternativeSpoiler userPreferred}image{large medium}description(asHtml:false)gender dateOfBirth{year month day}age bloodType favourites siteUrl}}"""
        d = await self._execute(q, {"id": character_id})
        return Character(**d["Character"]) if d.get("Character") else None

    async def search_characters(self, query: str, *, page: int = 1, per_page: int = 10) -> CharacterConnection:
        q = """query($p:Int,$pp:Int,$s:String){Page(page:$p,perPage:$pp){pageInfo{total perPage currentPage lastPage hasNextPage}characters(search:$s,sort:SEARCH_MATCH){id name{full native userPreferred}image{large medium}gender favourites siteUrl}}}"""
        d = await self._execute(q, {"p": page, "pp": per_page, "s": query})
        return CharacterConnection(**d["Page"])

    async def get_media_characters(self, media_id: int, *, page: int = 1, per_page: int = 10, role: Optional[str] = None) -> CharacterConnection:
        q = """query($id:Int,$p:Int,$pp:Int,$r:CharacterRole){Media(id:$id){id characters(page:$p,perPage:$pp,sort:ROLE,role:$r){pageInfo{total perPage currentPage lastPage hasNextPage}nodes{id name{full native userPreferred}image{large medium}gender favourites siteUrl}}}}"""
        d = await self._execute(q, {"id": media_id, "p": page, "pp": per_page, "r": role})
        return CharacterConnection(**d.get("Media", {}).get("characters", {}))

    # ── Staff ──

    async def get_staff(self, staff_id: int) -> Optional[Staff]:
        q = """query($id:Int){Staff(id:$id){id name{first middle last full native alternative userPreferred}languageV2 image{large medium}description(asHtml:false)primaryOccupations gender dateOfBirth{year month day}dateOfDeath{year month day}age yearsActive homeTown bloodType favourites siteUrl}}"""
        d = await self._execute(q, {"id": staff_id})
        return Staff(**d["Staff"]) if d.get("Staff") else None

    async def get_media_staff(self, media_id: int, *, page: int = 1, per_page: int = 10) -> StaffConnection:
        q = """query($id:Int,$p:Int,$pp:Int){Media(id:$id){id staff(page:$p,perPage:$pp,sort:RELEVANCE){pageInfo{total perPage currentPage lastPage hasNextPage}nodes{id name{full native userPreferred}languageV2 image{medium}primaryOccupations favourites siteUrl}}}}"""
        d = await self._execute(q, {"id": media_id, "p": page, "pp": per_page})
        return StaffConnection(**d.get("Media", {}).get("staff", {}))

    # ── Studios ──

    async def search_studios(self, query: str) -> Optional[Studio]:
        q = """query($s:String){Studio(search:$s){id name isAnimationStudio favourites siteUrl}}"""
        d = await self._execute(q, {"s": query})
        return Studio(**d["Studio"]) if d.get("Studio") else None

    async def get_media_studios(self, media_id: int) -> StudioConnection:
        q = """query($id:Int){Media(id:$id){id studios{nodes{id name isAnimationStudio favourites siteUrl}}}}"""
        d = await self._execute(q, {"id": media_id})
        return StudioConnection(**d.get("Media", {}).get("studios", {}))

    # ── Airing / Trends / Recs ──

    async def get_airing_schedule(self, *, page: int = 1, per_page: int = 20, airing_at_greater: Optional[int] = None, airing_at_lesser: Optional[int] = None, not_yet_aired: bool = True) -> dict:
        schedule_args = ["notYetAired: $nya", "sort: TIME"]
        var_defs = ["$p: Int", "$pp: Int", "$nya: Boolean"]
        variables: dict = {"p": page, "pp": per_page, "nya": not_yet_aired}
        if airing_at_greater is not None:
            var_defs.append("$ag: Int")
            schedule_args.insert(0, "airingAt_greater: $ag")
            variables["ag"] = airing_at_greater
        if airing_at_lesser is not None:
            var_defs.append("$al: Int")
            schedule_args.insert(0, "airingAt_lesser: $al")
            variables["al"] = airing_at_lesser
        q = f"query({','.join(var_defs)}){{Page(page:$p,perPage:$pp){{pageInfo{{total perPage currentPage lastPage hasNextPage}}airingSchedules({','.join(schedule_args)}){{id airingAt episode mediaId media{{id title{{romaji english}}format status coverImage{{medium}}}}}}}}}}"
        return (await self._execute(q, variables))["Page"]

    async def get_media_recommendations(self, media_id: int, *, page: int = 1, per_page: int = 10) -> dict:
        q = """query($id:Int,$p:Int,$pp:Int){Media(id:$id){id recommendations(page:$p,perPage:$pp,sort:RATING_DESC){pageInfo{total perPage currentPage lastPage hasNextPage}nodes{id rating userRating mediaRecommendation{id title{romaji english}format averageScore coverImage{medium}}}}}}"""
        return (await self._execute(q, {"id": media_id, "p": page, "pp": per_page})).get("Media", {}).get("recommendations", {})

    async def get_media_trends(self, media_id: int, *, page: int = 1, per_page: int = 30) -> list[MediaTrend]:
        q = """query($id:Int,$p:Int,$pp:Int){Media(id:$id){id trends(page:$p,perPage:$pp,sort:ID_DESC){nodes{mediaId date trending averageScore popularity inProgress releasing episode}}}}"""
        d = await self._execute(q, {"id": media_id, "p": page, "pp": per_page})
        return [MediaTrend(**t) for t in d.get("Media", {}).get("trends", {}).get("nodes", [])]

    async def get_media_relations(self, media_id: int) -> dict:
        q = """query($id:Int){Media(id:$id){id relations{edges{id relationType(version:2)node{id title{romaji english}format type averageScore coverImage{medium}}}}}}"""
        return (await self._execute(q, {"id": media_id})).get("Media", {}).get("relations", {})

    # ── Misc ──

    async def get_genres(self) -> list[str]:
        return (await self._execute("query{GenreCollection}")).get("GenreCollection", [])

    async def get_media_tags(self, *, status: int = 1) -> list[dict]:
        return (await self._execute("query($s:Int){MediaTagCollection(status:$s){id name description category isAdult isGeneralSpoiler}}", {"s": status})).get("MediaTagCollection", [])

    # ── Rankings ──────────────────────────────────────────────

    async def get_media_rankings(self, media_id: int) -> list[dict]:
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
        data = await self._execute(query, {"id": media_id})
        media = data.get("Media", {})
        return media.get("rankings", [])

    # ── Site Statistics ───────────────────────────────────────

    async def get_site_statistics(self) -> dict:
        """Get AniList site-wide statistics."""
        query = """
        query {
            SiteStatistics {
                anime { nodes { count } }
                manga { nodes { count } }
            }
        }
        """
        data = await self._execute(query)
        return data.get("SiteStatistics", {})

    # ── User ──────────────────────────────────────────────────

    async def get_user(
        self,
        *,
        name: Optional[str] = None,
        user_id: Optional[int] = None,
    ) -> Optional[User]:
        """Get an AniList user by name or ID.

        Args:
            name: Username to search (case-insensitive match).
            user_id: Exact user ID (takes precedence over name).

        Returns:
            User object if found, None otherwise.
        """
        if not name and not user_id:
            raise ValueError("Either 'name' or 'user_id' must be provided")

        query = """
        query ($id: Int, $name: String) {
            User(id: $id, name: $name) {
                id name about avatar { large medium }
                bannerImage
                isFollowing isFollower isBlocked
                donatorTier donatorBadge
                moderatorRoles
                options { titleLanguage displayAdultContent profileColor }
                mediaListOptions { scoreFormat rowOrder }
                favourites { anime { nodes { id title { romaji english } } } }
                statistics {
                    anime { count meanScore standardDeviation episodesWatched minutesWatched }
                    manga { count meanScore standardDeviation chaptersRead volumesRead }
                }
                unreadNotificationCount
                siteUrl
                createdAt updatedAt
            }
        }
        """
        data = await self._execute(query, {"id": user_id, "name": name})
        user_data = data.get("User")
        if user_data is None:
            return None
        return User(**user_data)
