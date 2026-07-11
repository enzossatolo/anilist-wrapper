"""Base/shared models used across the models package."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class FuzzyDate(BaseModel):
    """A date that may have unknown day/month."""

    year: Optional[int] = None
    month: Optional[int] = None
    day: Optional[int] = None


class MediaTitle(BaseModel):
    """The official titles of a media entry in various languages."""

    romaji: Optional[str] = None
    english: Optional[str] = None
    native: Optional[str] = None
    user_preferred: Optional[str] = Field(default=None, alias="userPreferred")


class MediaCoverImage(BaseModel):
    """Cover images for a media entry."""

    extra_large: str = Field(default="", alias="extraLarge")
    large: str = ""
    medium: str = ""
    color: Optional[str] = None


class MediaTrailer(BaseModel):
    """A media trailer or advertisement."""

    id: Optional[str] = None
    site: Optional[str] = None
    thumbnail: Optional[str] = None
