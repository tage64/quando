import argparse
import itertools
import json
import os
import sys
from typing import Iterator

import appdirs  # type: ignore
import requests
import ics  # type: ignore
import arrow  # type: ignore

from . import show


def main() -> None:
    parser = argparse.ArgumentParser(description="Parse an ics calender and show it")
    parser.add_argument("-u", "--url")
    parser.add_argument(
        "-o",
        "--ofline",
        action="store_true",
        help="Try to read the calender from the cache instead of fetching from a URL. (Only applicable if a URL is given.)",
    )
    parser.add_argument("-s", "--start", type=arrow.get)
    parser.add_argument("-e", "--end", type=arrow.get)
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument(
        "--cache-file",
        default=os.path.join(appdirs.user_cache_dir(), "quando.json"),
        help="Path to the cache file.",
    )
    args = parser.parse_args()
    if args.url:
        text: str | None = None
        if not args.ofline:
            try:
                text = requests.get(args.url.strip()).text
            except Exception as ex:
                print(f"Warning: Failed to fetch calender: {ex}")
                print("Will try local cache.")
                print()
        if text is None:
            try:
                with open(args.cache_file) as f:
                    cache = json.load(f)
                    assert isinstance(
                        cache, dict
                    ), f"The cache file at {args.cache_file} is of a bad format. Should be JSON dictionary."
                    try:
                        text = cache[args.url]
                        assert isinstance(
                            text, str
                        ), f"The cache file at {args.cache_file} is of a bad format. Keys in the map should be strings."
                    except IndexError:
                        exit(
                            f"Could not find a entry for {args.url} in the cache at {args.cache}"
                        )
            except EnvironmentError as e:
                exit(
                    f"Could not open/read cache file at {args.cache_file}. The error was: {e}"
                )

        assert isinstance(text, str)
        calendar = ics.Calendar(text)
        try:
            with open(args.cache_file) as f:
                cache = json.load(f)
                assert isinstance(
                    cache, dict
                ), f"The cache file at {args.cache_file} is of a bad format. Should be JSON dictionary."
        except FileNotFoundError:
            cache = dict()
            with open(args.cache_file, "w") as f:
                cache[args.url] = text
                json.dump(cache, f)
        except EnvironmentError as e:
            print(
                f"Warning: Could not update cache file at {args.cache_file}. The error was: {e}"
            )
    else:
        calendar = ics.Calendar(sys.stdin.read())
    events: Iterator[ics.Event] = iter(calendar.timeline)
    if args.start:
        events = itertools.dropwhile(lambda x: x.begin < args.start, events)
    if args.end:
        events = itertools.takewhile(lambda x: x.begin <= args.end, events)
    show.show_events(events, args.verbose)
