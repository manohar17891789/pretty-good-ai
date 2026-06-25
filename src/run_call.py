"""CLI: run a single scenario call end-to-end.

Usage:
    python -m src.run_call schedule_simple
    python -m src.run_call --list
"""

import argparse

from src.caller import place_call
from src.scenarios import SCENARIOS


def main() -> None:
    parser = argparse.ArgumentParser(description="Run one test call against the clinic agent.")
    parser.add_argument("scenario_id", nargs="?", help="Scenario id, e.g. schedule_simple")
    parser.add_argument("--list", action="store_true", help="List available scenario ids and exit")
    args = parser.parse_args()

    if args.list or not args.scenario_id:
        for s in SCENARIOS:
            print(f"{s.id:30s} [{s.category}] {s.title}")
        return

    place_call(args.scenario_id)


if __name__ == "__main__":
    main()
