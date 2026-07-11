# AniList API Wrapper

Complete, type-safe Python wrapper for the [AniList GraphQL API](https://docs.anilist.co/).

## Features

- **Zero-config** — no API key needed for public data
- **Type-safe** — Pydantic models for all GraphQL types
- **Rate-limited** — built-in token bucket (~80 req/min, stays under the 90 cap)
- **Rich data** — media, characters, staff, studios, airing schedules, trends, user lists
- **OAuth2 support** — full auth flow for authenticated operations
- **CLI tool** — query from the terminal
- **Well-documented** — docstrings on every public method

## Installation

```bash
pip install anilist-wrapper
```

Or from source:

```bash
git clone https://github.com/enzossatolo/anilist-wrapper.git
cd anilist-wrapper
pip install -e .
```

## Quick Start

```python
from anilist import AniListClient, MediaSeason

client = AniListClient()

# Get an anime by ID
anime = client.get_media(1)
print(anime.title.romaji)        # "Cowboy Bebop"
print(anime.average_score)       # 86
print(anime.genres)              # ["Action", "Adventure", "Drama", "Sci-Fi"]

# Search
results = client.search_media("Attack on Titan")
for m in results.nodes:
    print(f"{m.title.english}: {m.average_score}%")

# Seasonal
summer = client.get_seasonal(2026, MediaSeason.SUMMER)
for m in summer.nodes:
    print(f"{m.title.romaji} — {m.average_score}%")

# Characters
chars = client.search_characters("Lelouch")
for c in chars.nodes:
    print(c.name.full)

# Close when done (or use as context manager)
client.close()
```

### Context manager

```python
with AniListClient() as client:
    anime = client.get_media(1)
    print(anime.title.romaji)
```

## CLI Usage

```bash
# Search
anilist search "Attack on Titan"
anilist search "One Piece" --type MANGA
anilist search "isekai" --format TV --sort POPULARITY_DESC

# Get by ID
anilist get 1
anilist get 1 --json | jq .title.romaji

# Seasonal
anilist seasonal --year 2026 --season SUMMER
anilist seasonal --year 2026 --season WINTER --per-page 5

# Trending
anilist trending
anilist trending --type MANGA

# Characters
anilist character "Spike Spiegel"
anilist character "Mikasa" --json

# Studios
anilist studio "Wit Studio"

# Genres
anilist genres

# Airing schedule
anilist schedule

# User info (requires auth)
anilist user --name "someuser" --token YOUR_OAUTH_TOKEN
```

## API Reference

### `AniListClient`

| Method | Description |
|--------|-------------|
| `get_media(id)` | Get media by AniList ID |
| `search_media(query)` | Search by title |
| `get_seasonal(year, season)` | Get seasonal media |
| `get_trending()` | Currently trending |
| `get_media_recommendations(id)` | Similar titles |
| `get_media_relations(id)` | Sequels, prequels, adaptations |
| `get_media_trends(id)` | Daily trend stats |
| `get_media_characters(id)` | Characters in a show |
| `get_media_staff(id)` | Staff for a show |
| `get_media_studios(id)` | Studios for a show |
| `get_media_rankings(id)` | Rankings |
| `get_character(id)` | Character by ID |
| `search_characters(query)` | Search characters |
| `get_staff(id)` | Staff by ID |
| `search_studios(query)` | Search studios |
| `get_airing_schedule()` | Upcoming episodes |
| `get_user(id\|name)` | User profile |
| `get_user_list(user_id)` | User's anime/manga list |
| `get_genres()` | All media genres |
| `get_media_tags()` | All media tags |
| `get_site_statistics()` | Site-wide stats |

### Authentication

```python
from anilist.auth import AniListAuth

auth = AniListAuth(
    client_id="YOUR_CLIENT_ID",
    client_secret="YOUR_CLIENT_SECRET",
)

# Get authorization URL
url = auth.get_authorization_url()
# User visits url → redirected back with ?code=...

# Exchange code for token
token = auth.exchange_code("code_from_callback")

# Use with client
client = AniListClient(auth=auth)
user = client.get_user()  # Returns the authenticated viewer

# Persist token
auth.save("token.json")
auth = AniListAuth.load("YOUR_CLIENT_ID", "YOUR_CLIENT_SECRET", "token.json")
```

## Rate Limiting

AniList allows ~90 requests per minute. The wrapper defaults to 80 rpm with a token bucket that supports short bursts (up to 10 concurrent requests).

```python
# Stricter limit
client = AniListClient(rate_limit_rpm=60)

# More burst
from anilist.rate_limiter import RateLimiter
# Internal use only — the client handles this automatically
```

## Enums

All AniList enums are available:

```python
from anilist import (
    MediaFormat,     # TV, MOVIE, OVA, ONA, etc.
    MediaStatus,     # FINISHED, RELEASING, etc.
    MediaSeason,     # WINTER, SPRING, SUMMER, FALL
    MediaSort,       # POPULARITY_DESC, SCORE_DESC, TRENDING_DESC, etc.
    MediaSource,     # ORIGINAL, MANGA, LIGHT_NOVEL, etc.
    MediaListStatus, # CURRENT, PLANNING, COMPLETED, DROPPED, etc.
    CharacterSort,
    StaffSort,
)
```

## Exceptions

```python
from anilist import (
    AniListError,         # Base
    GraphQLError,         # API returned errors
    RateLimitError,       # HTTP 429
    AuthenticationError,  # Auth failure
    NotFoundError,        # Resource not found
    ValidationError,      # Input validation
)
```

## Requirements

- Python 3.10+
- httpx >= 0.25.0
- pydantic >= 2.0.0

## License

MIT
