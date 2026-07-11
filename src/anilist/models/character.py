"""Character, Staff, Studio, and related models."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from .base import FuzzyDate
from .media import Media, MediaConnection, MediaTitle, PageInfo


class CharacterName(BaseModel):
    """Character name in different scripts."""

    first: Optional[str] = None
    middle: Optional[str] = None
    last: Optional[str] = None
    full: Optional[str] = None
    native: Optional[str] = None
    alternative: list[str] = Field(default_factory=list)
    alternative_spoiler: list[str] = Field(default_factory=list, alias="alternativeSpoiler")
    user_preferred: Optional[str] = Field(default=None, alias="userPreferred")  # noqa


class CharacterImage(BaseModel):
    """Character images."""

    large: str = ""
    medium: str = ""


class CharacterConnection(BaseModel):
    """A paginated list of characters."""

    page_info: Optional[PageInfo] = Field(default=None, alias="pageInfo")
    nodes: list[Character] = Field(default_factory=list)


class Character(BaseModel):
    """An anime/manga character."""

    id: int
    name: CharacterName
    image: Optional[CharacterImage] = None
    description: Optional[str] = None
    gender: Optional[str] = None
    date_of_birth: Optional[FuzzyDate] = Field(default=None, alias="dateOfBirth")
    age: Optional[str] = None
    blood_type: Optional[str] = Field(default=None, alias="bloodType")
    is_favourite: Optional[bool] = Field(default=None, alias="isFavourite")
    favourites: Optional[int] = None
    site_url: Optional[str] = Field(default=None, alias="siteUrl")
    media: Optional[MediaConnection] = None

    model_config = {"populate_by_name": True}


class StaffName(BaseModel):
    """Staff name in different scripts."""

    first: Optional[str] = None
    middle: Optional[str] = None
    last: Optional[str] = None
    full: Optional[str] = None
    native: Optional[str] = None
    alternative: list[str] = Field(default_factory=list)
    user_preferred: Optional[str] = Field(default=None, alias="userPreferred")  # noqa


class StaffImage(BaseModel):
    """Staff images."""

    large: str = ""
    medium: str = ""


class StaffConnection(BaseModel):
    """A paginated list of staff."""

    page_info: Optional[PageInfo] = Field(default=None, alias="pageInfo")
    nodes: list[Staff] = Field(default_factory=list)


class Staff(BaseModel):
    """A voice actor, director, animator, etc."""

    id: int
    name: StaffName
    language_v2: Optional[str] = Field(default=None, alias="languageV2")
    image: Optional[StaffImage] = None
    description: Optional[str] = None
    primary_occupations: list[str] = Field(
        default_factory=list, alias="primaryOccupations"
    )
    gender: Optional[str] = None
    date_of_birth: Optional[FuzzyDate] = Field(default=None, alias="dateOfBirth")
    date_of_death: Optional[FuzzyDate] = Field(default=None, alias="dateOfDeath")
    age: Optional[int] = None
    years_active: list[int] = Field(default_factory=list, alias="yearsActive")
    home_town: Optional[str] = Field(default=None, alias="homeTown")
    blood_type: Optional[str] = Field(default=None, alias="bloodType")
    is_favourite: Optional[bool] = Field(default=None, alias="isFavourite")
    favourites: Optional[int] = None
    site_url: Optional[str] = Field(default=None, alias="siteUrl")
    staff_media: Optional[MediaConnection] = Field(default=None, alias="staffMedia")
    characters: Optional[CharacterConnection] = None

    model_config = {"populate_by_name": True}


class StudioConnection(BaseModel):
    """A paginated list of studios."""

    page_info: Optional[PageInfo] = Field(default=None, alias="pageInfo")
    nodes: list[Studio] = Field(default_factory=list)


class Studio(BaseModel):
    """A production studio."""

    id: int
    name: str
    is_animation_studio: bool = Field(alias="isAnimationStudio")
    favourites: Optional[int] = None
    media: Optional[MediaConnection] = None
    site_url: Optional[str] = Field(default=None, alias="siteUrl")

    model_config = {"populate_by_name": True}


class RecommendationConnection(BaseModel):
    """A paginated list of recommendations."""

    page_info: Optional[PageInfo] = Field(default=None, alias="pageInfo")
    nodes: list[Recommendation] = Field(default_factory=list)


class Recommendation(BaseModel):
    """A user recommendation linking two media entries."""

    id: int
    rating: Optional[int] = None
    user_rating: Optional[str] = Field(default=None, alias="userRating")
    media: Optional[Media] = None
    media_recommendation: Optional[Media] = Field(
        default=None, alias="mediaRecommendation"
    )
    user: Optional[object] = None  # User is in a different module

    model_config = {"populate_by_name": True}


class ReviewConnection(BaseModel):
    """A paginated list of reviews."""

    page_info: Optional[PageInfo] = Field(default=None, alias="pageInfo")
    nodes: list[Review] = Field(default_factory=list)


class Review(BaseModel):
    """A user review of a media entry."""

    id: int
    user_id: int = Field(alias="userId")
    media_id: int = Field(alias="mediaId")
    media_type: Optional[str] = Field(default=None, alias="mediaType")
    summary: Optional[str] = None
    body: Optional[str] = None
    rating: Optional[int] = None
    rating_amount: Optional[int] = Field(default=None, alias="ratingAmount")
    score: Optional[int] = None
    private: Optional[bool] = None
    site_url: Optional[str] = Field(default=None, alias="siteUrl")
    created_at: int = Field(alias="createdAt")
    updated_at: int = Field(alias="updatedAt")

    model_config = {"populate_by_name": True}


# Rebuild models that reference types defined later in this same file
CharacterConnection.model_rebuild()
StaffConnection.model_rebuild()
StudioConnection.model_rebuild()
RecommendationConnection.model_rebuild()
ReviewConnection.model_rebuild()
