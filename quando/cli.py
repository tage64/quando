import argparse
import itertools
import sys
from typing import Iterator

import requests
import ics  # type: ignore
import arrow  # type: ignore

from . import show


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Parse an ics calender and show it")
    parser.add_argument("-u", "--url")
    parser.add_argument("-s", "--start", type=arrow.get)
    parser.add_argument("-e", "--end", type=arrow.get)
    args = parser.parse_args()
    url = args.url.strip()
    if url:
        text = requests.get(url).text
    else:
        calendar = ics.Calendar(sys.stdin.read())
    calendar = ics.Calendar(text)
    events: Iterator[ics.Event] = iter(calendar.timeline)
    if args.start:
        events = itertools.dropwhile(lambda x: x.begin < args.start, events)
    if args.end:
        events = itertools.takewhile(lambda x: x.begin <= args.end, events)
    show.show_events(events)
