"""Media (anime/manga) models."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from ..types import MediaFormat, MediaSeason, MediaSource, MediaStatus
from .base import FuzzyDate, MediaCoverImage, MediaTitle, MediaTrailer


class AiringSchedule(BaseModel):
    """The next airing schedule for a media entry."""

    id: int
    airing_at: int = Field(alias="airingAt")
    time_until_airing: int = Field(alias="timeUntilAiring")
    episode: int
    media_id: int = Field(alias="mediaId")


class MediaTag(BaseModel):
    """A tag describing elements and themes."""

    id: int
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    rank: int = 0
    is_general_spoiler: bool = Field(default=False, alias="isGeneralSpoiler")
    is_media_spoiler: bool = Field(default=False, alias="isMediaSpoiler")
    is_adult: bool = Field(default=False, alias="isAdult")


class MediaRanking(BaseModel):
    """Ranking of a media in a particular category and format."""

    id: int
    rank: int
    type: str
    format: str
    year: Optional[int] = None
    season: Optional[str] = None
    all_time: bool = Field(default=False, alias="allTime")
    context: str = ""


class MediaExternalLink(BaseModel):
    """External link to another site related to the media."""

    id: int
    url: str
    site: str
    type: Optional[str] = None
    language: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None


class MediaStreamingEpisode(BaseModel):
    """Data and links to legal streaming episodes."""

    title: Optional[str] = None
    thumbnail: Optional[str] = None
    url: Optional[str] = None
    site: Optional[str] = None


class ScoreDistribution(BaseModel):
    score: int
    amount: int


class StatusDistribution(BaseModel):
    status: str
    amount: int


class MediaStats(BaseModel):
    """Distribution of scores and statuses for a media."""

    score_distribution: list[ScoreDistribution] = Field(
        default_factory=list, alias="scoreDistribution"
    )
    status_distribution: list[StatusDistribution] = Field(
        default_factory=list, alias="statusDistribution"
    )


class PageInfo(BaseModel):
    """Pagination information."""

    total: int = 0
    per_page: int = Field(default=0, alias="perPage")
    current_page: int = Field(default=0, alias="currentPage")
    last_page: int = Field(default=0, alias="lastPage")
    has_next_page: bool = Field(default=False, alias="hasNextPage")


class MediaConnection(BaseModel):
    """A paginated list of media entries."""

    page_info: Optional[PageInfo] = Field(default=None, alias="pageInfo")
    nodes: list[Media] = Field(default_factory=list)


class Media(BaseModel):
    """An anime or manga entry."""

    id: int
    id_mal: Optional[int] = Field(default=None, alias="idMal")
    title: MediaTitle
    type: Optional[str] = None
    format: Optional[MediaFormat] = None
    status: Optional[MediaStatus] = None
    description: Optional[str] = None
    start_date: Optional[FuzzyDate] = Field(default=None, alias="startDate")
    end_date: Optional[FuzzyDate] = Field(default=None, alias="endDate")
    season: Optional[MediaSeason] = None
    season_year: Optional[int] = Field(default=None, alias="seasonYear")
    season_int: Optional[int] = Field(default=None, alias="seasonInt")
    episodes: Optional[int] = None
    duration: Optional[int] = None
    chapters: Optional[int] = None
    volumes: Optional[int] = None
    country_of_origin: Optional[str] = Field(default=None, alias="countryOfOrigin")
    is_licensed: Optional[bool] = Field(default=None, alias="isLicensed")
    source: Optional[MediaSource] = None
    hashtag: Optional[str] = None
    trailer: Optional[MediaTrailer] = None
    updated_at: Optional[int] = Field(default=None, alias="updatedAt")
    cover_image: Optional[MediaCoverImage] = Field(default=None, alias="coverImage")
    banner_image: Optional[str] = Field(default=None, alias="bannerImage")
    genres: list[str] = Field(default_factory=list)
    synonyms: list[str] = Field(default_factory=list)
    average_score: Optional[int] = Field(default=None, alias="averageScore")
    mean_score: Optional[int] = Field(default=None, alias="meanScore")
    popularity: Optional[int] = None
    is_locked: Optional[bool] = Field(default=None, alias="isLocked")
    trending: Optional[int] = None
    favourites: Optional[int] = None
    tags: list[MediaTag] = Field(default_factory=list)
    is_adult: Optional[bool] = Field(default=None, alias="isAdult")
    next_airing_episode: Optional[AiringSchedule] = Field(
        default=None, alias="nextAiringEpisode"
    )
    site_url: Optional[str] = Field(default=None, alias="siteUrl")

    # Relation fields (populated via connections — set to None by default)
    relations: Optional[MediaConnection] = None
    characters: Optional[object] = None
    staff: Optional[object] = None
    studios: Optional[object] = None
    recommendations: Optional[object] = None
    reviews: Optional[object] = None
    rankings: list[MediaRanking] = Field(default_factory=list)
    external_links: list[MediaExternalLink] = Field(default_factory=list, alias="externalLinks")
    streaming_episodes: list[MediaStreamingEpisode] = Field(
        default_factory=list, alias="streamingEpisodes"
    )

    model_config = {"populate_by_name": True}


class MediaTrend(BaseModel):
    """Daily trend stats for a media entry."""

    media_id: int = Field(alias="mediaId")
    date: int
    trending: int
    average_score: Optional[int] = Field(default=None, alias="averageScore")
    popularity: Optional[int] = None
    in_progress: Optional[int] = Field(default=None, alias="inProgress")
    releasing: bool = False
    episode: Optional[int] = None


MediaConnection.model_rebuild()
Media.model_rebuild()
