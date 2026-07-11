"""CLI interface for the AniList API wrapper."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Optional

from . import AniListClient, MediaFormat, MediaSeason, MediaSort
from .auth import AniListAuth


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="anilist",
        description="Query the AniList API from the command line.",
    )
    parser.add_argument(
        "--token", type=str, help="AniList OAuth access token for authenticated queries",
    )

    sub = parser.add_subparsers(dest="command")

    # search
    p_search = sub.add_parser("search", help="Search for anime/manga")
    p_search.add_argument("query", type=str)
    p_search.add_argument("--type", choices=["ANIME", "MANGA"], default="ANIME")
    p_search.add_argument("--format", type=str, choices=[f.value for f in MediaFormat])
    p_search.add_argument("--page", type=int, default=1)
    p_search.add_argument("--per-page", type=int, default=10)
    p_search.add_argument("--sort", type=str, default="SEARCH_MATCH")
    p_search.add_argument("--json", action="store_true", help="Output as JSON")

    # get
    p_get = sub.add_parser("get", help="Get a media entry by ID")
    p_get.add_argument("id", type=int)
    p_get.add_argument("--type", choices=["ANIME", "MANGA"], default="ANIME")
    p_get.add_argument("--json", action="store_true", help="Output as JSON")

    # seasonal
    p_seasonal = sub.add_parser("seasonal", help="Get seasonal anime")
    p_seasonal.add_argument("--year", type=int, required=True)
    p_seasonal.add_argument("--season", type=str, required=True, choices=[s.value for s in MediaSeason])
    p_seasonal.add_argument("--page", type=int, default=1)
    p_seasonal.add_argument("--per-page", type=int, default=20)
    p_seasonal.add_argument("--json", action="store_true")

    # trending
    p_trend = sub.add_parser("trending", help="Get trending anime/manga")
    p_trend.add_argument("--type", choices=["ANIME", "MANGA"], default="ANIME")
    p_trend.add_argument("--page", type=int, default=1)
    p_trend.add_argument("--per-page", type=int, default=20)
    p_trend.add_argument("--json", action="store_true")

    # character
    p_char = sub.add_parser("character", help="Search characters")
    p_char.add_argument("query", type=str)
    p_char.add_argument("--json", action="store_true")

    # studio
    p_studio = sub.add_parser("studio", help="Search studios")
    p_studio.add_argument("query", type=str)
    p_studio.add_argument("--json", action="store_true")

    # genres
    sub.add_parser("genres", help="List all media genres")

    # user
    p_user = sub.add_parser("user", help="Get user info (requires auth)")
    p_user.add_argument("--name", type=str)
    p_user.add_argument("--json", action="store_true")

    # schedule
    p_sched = sub.add_parser("schedule", help="Get airing schedule")
    p_sched.add_argument("--page", type=int, default=1)
    p_sched.add_argument("--per-page", type=int, default=20)
    p_sched.add_argument("--json", action="store_true")

    return parser


def _print_media(m: dict, json_mode: bool = False) -> None:
    if json_mode:
        print(json.dumps(m, indent=2, ensure_ascii=False))
        return
    title = m.get("title", {}).get("romaji") or m.get("title", {}).get("english", "?")
    score = m.get("averageScore", "?")
    fmt = m.get("format", "?")
    eps = m.get("episodes", "?")
    pop = m.get("popularity", "?")
    print(f"  [{m['id']}] {title}")
    print(f"       {fmt} | {eps} eps | Score: {score}% | Pop: {pop}")


def _print_character(c: dict, json_mode: bool = False) -> None:
    if json_mode:
        print(json.dumps(c, indent=2, ensure_ascii=False))
        return
    name = c.get("name", {}).get("full", "?")
    print(f"  [{c['id']}] {name}")


def main(argv: Optional[list[str]] = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return

    auth = None
    if args.token:
        auth = AniListAuth(client_id="", client_secret="")
        auth.load_token(args.token)

    client = AniListClient(auth=auth)

    try:
        if args.command == "search":
            fmt = [MediaFormat(args.format)] if getattr(args, "format", None) else None
            result = client.search_media(
                args.query,
                media_type=args.type,  # noqa
                page=args.page,
                per_page=args.per_page,
                sort=MediaSort(getattr(args, "sort", "SEARCH_MATCH")),
                format_in=fmt,
            )
            if args.json:
                print(json.dumps(
                    [m.model_dump(by_alias=True) for m in result.nodes],
                    indent=2, ensure_ascii=False,
                ))
            else:
                print(f"Found {result.page_info.total} results (page {args.page}):")
                for m in result.nodes:
                    _print_media(m.model_dump(by_alias=True))

        elif args.command == "get":
            media = client.get_media(args.id, media_type=args.type)
            if media:
                if args.json:
                    print(json.dumps(media.model_dump(by_alias=True), indent=2, ensure_ascii=False))
                else:
                    _print_media(media.model_dump(by_alias=True))
            else:
                print(f"No media found with ID {args.id}", file=sys.stderr)

        elif args.command == "seasonal":
            result = client.get_seasonal(
                args.year,
                MediaSeason(args.season),
                page=args.page,
                per_page=args.per_page,
            )
            if args.json:
                print(json.dumps(
                    [m.model_dump(by_alias=True) for m in result.nodes],
                    indent=2, ensure_ascii=False,
                ))
            else:
                print(f"Found {result.page_info.total} ({args.season} {args.year}):")
                for m in result.nodes:
                    _print_media(m.model_dump(by_alias=True))

        elif args.command == "trending":
            result = client.get_trending(
                media_type=args.type,
                page=args.page,
                per_page=args.per_page,
            )
            if args.json:
                print(json.dumps(
                    [m.model_dump(by_alias=True) for m in result.nodes],
                    indent=2, ensure_ascii=False,
                ))
            else:
                print(f"Trending {args.type} (page {args.page}):")
                for m in result.nodes:
                    _print_media(m.model_dump(by_alias=True))

        elif args.command == "character":
            result = client.search_characters(args.query)
            if args.json:
                print(json.dumps(
                    [c.model_dump(by_alias=True) for c in result.nodes],
                    indent=2, ensure_ascii=False,
                ))
            else:
                for c in result.nodes:
                    _print_character(c.model_dump(by_alias=True))

        elif args.command == "studio":
            result = client.search_studios(args.query)
            if result:
                if args.json:
                    print(json.dumps(result.model_dump(by_alias=True), indent=2, ensure_ascii=False))
                else:
                    print(f"  [{result.id}] {result.name}")
                    print(f"       Animation: {result.is_animation_studio} | Favourites: {result.favourites}")
            else:
                print(f"No studio found for '{args.query}'", file=sys.stderr)

        elif args.command == "genres":
            genres = client.get_genres()
            print("\n".join(genres))

        elif args.command == "user":
            user = client.get_user(name=args.name)
            if user:
                if args.json:
                    print(json.dumps(user.model_dump(by_alias=True), indent=2, ensure_ascii=False))
                else:
                    print(f"  {user.name} (ID: {user.id})")
                    if user.statistics and user.statistics.anime:
                        a = user.statistics.anime
                        print(f"       Anime: {a.count} | Mean: {a.mean_score} | Episodes: {a.episodes_watched}")
                    print(f"       Site: {user.site_url}")
            else:
                print("User not found or authentication required", file=sys.stderr)

        elif args.command == "schedule":
            result = client.get_airing_schedule(
                page=args.page,
                per_page=args.per_page,
            )
            if args.json:
                print(json.dumps(result, indent=2, ensure_ascii=False))
            else:
                schedules = result.get("airingSchedules", [])
                for s in schedules:
                    media_title = s.get("media", {}).get("title", {}).get("romaji", "?")
                    print(f"  Ep {s['episode']} | {media_title} | {s['airingAt']}")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        client.close()


if __name__ == "__main__":
    main()
