"""Custom exceptions for the AniList API wrapper."""

from __future__ import annotations


class AniListError(Exception):
    """Base exception for all AniList API errors."""


class GraphQLError(AniListError):
    """Raised when the GraphQL API returns errors."""

    def __init__(self, errors: list[dict], query: str = "") -> None:
        self.errors = errors
        self.query = query
        messages = [e.get("message", str(e)) for e in errors]
        super().__init__("\n".join(messages))


class RateLimitError(AniListError):
    """Raised when the rate limit is exceeded (HTTP 429)."""

    def __init__(self, retry_after: int = 60) -> None:
        self.retry_after = retry_after
        super().__init__(
            f"Rate limit exceeded. Retry after {retry_after} seconds."
        )


class AuthenticationError(AniListError):
    """Raised when authentication fails."""


class NotFoundError(AniListError):
    """Raised when a requested resource is not found."""


class ValidationError(AniListError):
    """Raised when input validation fails."""
