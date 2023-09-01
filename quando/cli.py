import argparse
import itertools
import json
import os
import sys
from typing import *

import appdirs  # type: ignore
import requests
import ics  # type: ignore
import arrow  # type: ignore

from . import show


def main() -> None:
    argparser = argparse.ArgumentParser(
        description="Show ICS calenders in the terminal.",
    )
    argparser.add_argument(
        "-V", "--version", action="version", version="%(prog)s 1.0.0"
    )
    argparser.add_argument(
        "--cache-file",
        default=os.path.join(appdirs.user_cache_dir(), "quando.json"),
        help="Path to the cache file.",
    )
    argparser.add_argument(
        "--data-file",
        default=os.path.join(appdirs.user_data_dir(), "quando.json"),
        help="Path to the data file where all calender names and URLs are remembered.",
    )
    subcmds = argparser.add_subparsers(dest="subcmd")
    show_argparser = subcmds.add_parser("show", help="Show a calender.")
    show_argparser.add_argument(
        "name",
        help="Name of the calender. A dash ('-') will read the ICS file from STDIN.",
    )
    retrieve_kind_group = show_argparser.add_mutually_exclusive_group()
    retrieve_kind_group.add_argument(
        "-u",
        "--url",
        help="Retrieve the ICS calender from this URL and remember the URL in the future.",
    )
    retrieve_kind_group.add_argument(
        "-c",
        "--cache",
        action="store_true",
        help="Try to read the calender from the cache instead of fetching from a URL.",
    )
    show_argparser.add_argument("-s", "--start", type=arrow.get)
    show_argparser.add_argument("-e", "--end", type=arrow.get)
    show_argparser.add_argument("-v", "--verbose", action="store_true")
    show_argparser.add_argument(
        "-p", "--past", action="store_true", help="Include past events."
    )
    subcmds.add_parser("ls", help="List all calenders.")
    rm_argparser = subcmds.add_parser("rm", help="Remove a calender.")
    rm_argparser.add_argument("name", help="Name of the calender to remove.")
    subcmds.add_parser("clear", help="Remove all calenders.")
    args = argparser.parse_args()

    data: dict[str, str] = load_data_file(args.data_file)

    match args.subcmd:
        case "show":
            do_show(args, data)
        case "rm":
            do_rm(args, data)
        case "clear":
            do_clear(args, data)
        case "ls":
            do_ls(data)
        case cmd:
            exit(f"Error: Unknown subcommand: {cmd}")


def load_data_file(path: str) -> dict[str, str]:
    "Returns a dict with calender names as keys and URLs as values."
    try:
        with open(path) as f:
            data = json.load(f)
            assert isinstance(data, dict)
            for name, url in data.items():
                assert isinstance(name, str) and isinstance(url, str)
    except FileNotFoundError:
        data = {}
    except AssertionError:
        exit(
            f"Error: Failed to parse the data file at {path}: Expected JSON dictionary of names and URLs"
        )
    except EnvironmentError as e:
        exit(f"Error: Could not open/read data file at {path}. The error was: {e}")
    return data


def load_cache_file(path: str) -> dict[str, str]:
    "Returns a dict with calender names as keys and ICS calenders as values."
    try:
        with open(path) as f:
            cache = json.load(f)
            assert isinstance(cache, dict)
            for name, ics in cache.items():
                assert isinstance(name, str) and isinstance(ics, str)
    except FileNotFoundError:
        cache = {}
    except AssertionError:
        exit(
            f"Failed to parse the cache file at {path}: Expected JSON dictionary of names and ICS content"
        )
    except EnvironmentError as e:
        exit(f"Could not open/read cache file at {path}. The error was: {e}")
    return cache


def save_data(path: str, data: dict[str, str]) -> None:
    try:
        with open(path, "w") as f:
            json.dump(data, f)
    except EnvironmentError as e:
        exit(f"Error: Couldn't update data file at {path}: {e}")


def save_cache(path: str, cache: dict[str, str]) -> None:
    try:
        with open(path, "w") as f:
            json.dump(cache, f)
    except EnvironmentError as e:
        print(f"Warning: Couldn't update cache file at {path}: {e}", file=sys.stderr)


def do_show(args, data: dict[str, str]) -> None:
    cache: dict[str, str] = load_cache_file(args.cache_file)
    if args.url:
        data[args.name] = args.url
    try:
        url: str = data[args.name]
    except KeyError:
        exit(
            f"Error: No calender named {args.name}, consider creating one by specifying a URL with the '-u' flag"
        )

    ics_text: Optional[str] = None
    if args.name == "-":
        ics_text = sys.stdin.read()
    elif not args.cache:
        try:
            ics_text = requests.get(url).text
        except Exception as ex:
            print(f"Warning: Failed to fetch calender from {url}: {ex}")
            print("Will try local cache.")
    if ics_text is None:
        try:
            ics_text = cache[args.name]
        except KeyError:
            exit(
                f"Could not find an entry for {args.name} in the cache at {args.cache_file}"
            )

    assert isinstance(ics_text, str)
    calendar = ics.Calendar(ics_text)

    cache[args.name] = ics_text
    save_cache(args.cache_file, cache)
    save_data(args.data_file, data)

    events: Iterator[ics.Event] = iter(calendar.timeline)
    if args.start:
        events = itertools.dropwhile(lambda x: x.begin < args.start, events)
    if args.end:
        events = itertools.takewhile(lambda x: x.begin <= args.end, events)
    if not args.past:
        now = arrow.now()
        events = itertools.dropwhile(lambda x: x.begin < now, events)
    show.show_events(events, args.verbose)


def do_rm(args, data: dict[str, str]) -> None:
    try:
        data.pop(args.name)
    except KeyError:
        print(f"Warning: No calender named {args.name}", file=sys.stderr)
    save_data(args.data_file, data)


def do_clear(args, data: dict[str, str]) -> None:
    save_data(args.data_file, {})


def do_ls(data: dict[str, str]) -> None:
    for name, url in data.items():
        print(f"{name}: {url}")
