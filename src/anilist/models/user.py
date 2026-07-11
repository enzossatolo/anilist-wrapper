"""User and media list models."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field, field_validator

from ..types import MediaListStatus
from .base import FuzzyDate
from .media import Media, MediaTitle


class UserOptions(BaseModel):
    """User display preferences."""

    title_language: Optional[str] = Field(default=None, alias="titleLanguage")
    display_adult_content: Optional[bool] = Field(
        default=None, alias="displayAdultContent"
    )
    airing_notifications: Optional[bool] = Field(
        default=None, alias="airingNotifications"
    )
    profile_color: Optional[str] = Field(default=None, alias="profileColor")
    staff_name_language: Optional[str] = Field(default=None, alias="staffNameLanguage")
    notification_options: list["NotificationOption"] = Field(
        default_factory=list, alias="notificationOptions"
    )

    model_config = {"populate_by_name": True}


class NotificationOption(BaseModel):
    """A notification setting."""

    type: Optional[str] = None
    enabled: Optional[bool] = None


class MediaListOptions(BaseModel):
    """User media list preferences."""

    score_format: Optional[str] = Field(default=None, alias="scoreFormat")
    row_order: Optional[str] = Field(default=None, alias="rowOrder")
    anime_list: Optional["MediaListTypeOptions"] = Field(
        default=None, alias="animeList"
    )
    manga_list: Optional["MediaListTypeOptions"] = Field(
        default=None, alias="mangaList"
    )

    model_config = {"populate_by_name": True}


class MediaListTypeOptions(BaseModel):
    """Per-type list display options."""

    section_order: list[str] = Field(default_factory=list, alias="sectionOrder")
    split_completed_section_by_format: bool = Field(
        default=False, alias="splitCompletedSectionByFormat"
    )
    custom_lists: list[str] = Field(default_factory=list, alias="customLists")
    advanced_scoring: list[str] = Field(default_factory=list, alias="advancedScoring")
    advanced_scoring_enabled: bool = Field(
        default=False, alias="advancedScoringEnabled"
    )

    model_config = {"populate_by_name": True}


class UserAvatar(BaseModel):
    """User avatar image."""

    large: str = ""
    medium: str = ""


class UserBanner(BaseModel):
    """User banner image."""

    large: str = ""


class User(BaseModel):
    """An AniList user."""

    id: int
    name: str
    about: Optional[str] = None
    avatar: Optional[UserAvatar] = None
    banner_image: Optional[str] = Field(default=None, alias="bannerImage")
    is_following: Optional[bool] = Field(default=None, alias="isFollowing")
    is_follower: Optional[bool] = Field(default=None, alias="isFollower")
    is_blocked: Optional[bool] = Field(default=None, alias="isBlocked")
    bans: Optional[dict] = None
    options: Optional[UserOptions] = None
    media_list_options: Optional[MediaListOptions] = Field(
        default=None, alias="mediaListOptions"
    )
    favourites: Optional[dict] = None
    statistics: Optional["UserStatistics"] = None
    unread_notification_count: Optional[int] = Field(
        default=None, alias="unreadNotificationCount"
    )
    site_url: Optional[str] = Field(default=None, alias="siteUrl")
    donator_tier: Optional[int] = Field(default=None, alias="donatorTier")
    donator_badge: Optional[str] = Field(default=None, alias="donatorBadge")
    moderator_roles: list[str] = Field(default_factory=list, alias="moderatorRoles")

    @field_validator("moderator_roles", mode="before")
    @classmethod
    def _null_to_empty_list(cls, v):
        return v or []

    created_at: Optional[int] = Field(default=None, alias="createdAt")
    updated_at: Optional[int] = Field(default=None, alias="updatedAt")

    model_config = {"populate_by_name": True}


class UserStatistics(BaseModel):
    """User anime/manga statistics."""

    anime: Optional["UserFormatStatistics"] = None
    manga: Optional["UserFormatStatistics"] = None


class UserFormatStatistics(BaseModel):
    """Statistics broken down by format."""

    count: int = 0
    mean_score: float = Field(default=0.0, alias="meanScore")
    standard_deviation: float = Field(default=0.0, alias="standardDeviation")
    minutes_watched: int = Field(default=0, alias="minutesWatched")
    episodes_watched: int = Field(default=0, alias="episodesWatched")
    chapters_read: int = Field(default=0, alias="chaptersRead")
    volumes_read: int = Field(default=0, alias="volumesRead")
    formats: list["UserFormatStatistic"] = Field(default_factory=list)

    model_config = {"populate_by_name": True}


class UserFormatStatistic(BaseModel):
    """Statistics for a specific format."""

    format: Optional[str] = None
    count: int = 0
    mean_score: float = Field(default=0.0, alias="meanScore")
    minutes_watched: int = Field(default=0, alias="minutesWatched")
    chapters_read: int = Field(default=0, alias="chaptersRead")
    media_ids: list[int] = Field(default_factory=list, alias="mediaIds")

    model_config = {"populate_by_name": True}


class MediaList(BaseModel):
    """A user's list entry for a specific media."""

    id: int
    user_id: int = Field(alias="userId")
    media_id: int = Field(alias="mediaId")
    status: Optional[MediaListStatus] = None
    score: Optional[float] = None
    progress: Optional[int] = None
    progress_volumes: Optional[int] = Field(default=None, alias="progressVolumes")
    repeat: Optional[int] = None
    priority: Optional[int] = None
    private: Optional[bool] = None
    notes: Optional[str] = None
    hidden_from_status_lists: Optional[bool] = Field(
        default=None, alias="hiddenFromStatusLists"
    )
    custom_lists: Optional[dict] = Field(default=None, alias="customLists")
    advanced_scores: Optional[dict] = Field(default=None, alias="advancedScores")
    started_at: Optional[FuzzyDate] = Field(default=None, alias="startedAt")
    completed_at: Optional[FuzzyDate] = Field(default=None, alias="completedAt")
    updated_at: Optional[int] = Field(default=None, alias="updatedAt")
    created_at: Optional[int] = Field(default=None, alias="createdAt")
    media: Optional[Media] = None

    model_config = {"populate_by_name": True}


class MediaListCollection(BaseModel):
    """A user's media list grouped by status."""

    user: Optional[User] = None
    has_next_chunk: Optional[bool] = Field(default=None, alias="hasNextChunk")
    lists: list["MediaListGroup"] = Field(default_factory=list)

    model_config = {"populate_by_name": True}


class MediaListGroup(BaseModel):
    """A group of media list entries with the same status."""

    name: Optional[str] = None
    is_custom_list: Optional[bool] = Field(default=None, alias="isCustomList")
    is_split_completed_list: Optional[bool] = Field(
        default=None, alias="isSplitCompletedList"
    )
    status: Optional[MediaListStatus] = None
    entries: list[MediaList] = Field(default_factory=list)
