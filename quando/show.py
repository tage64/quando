from typing import Iterator

import ics  # type: ignore


def event_str(event: ics.Event) -> str:
    event_str: str = ""
    begin = event.begin.to("local")  # Convert to local timezone.
    if event.all_day:
        event_str += begin.format("YY-MM-DD")
    else:
        end = event.end.to("local")
        if begin != end:
            if begin.date() == end.date():
                event_str += begin.format(
                    "YY-MM-DD HH:MM") + " - " + end.format("HH:MM")
            else:
                event_str += begin.format(
                    "YY-MM-DD HH:MM") + " - " + end.format("YY-MM-DD HH:MM")
        else:
            event_str += begin.format("YY-MM-DD HH:MM")
    if event.name:
        event_str += ": "
        event_str += event.name
    return event_str


def show_events(events: Iterator[ics.Event]) -> None:
    for event in events:
        print(event_str(event))
