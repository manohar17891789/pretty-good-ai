"""CLI: run every scenario sequentially against the test number, then build
the aggregated bug report.

Sequential (not parallel) on purpose: it keeps Twilio concurrent-call usage
minimal, makes server logs easy to follow per call, and keeps the test
number from getting hit with overlapping calls.
"""

import sys
import time

from src.bug_report import aggregate_bug_report
from src.caller import place_call
from src.scenarios import SCENARIOS

PAUSE_BETWEEN_CALLS_S = 5


def main() -> None:
    failures = []
    for scenario in SCENARIOS:
        print(f"\n=== Scenario: {scenario.id} ({scenario.category}) ===")
        try:
            place_call(scenario.id)
        except Exception as exc:
            print(f"FAILED scenario {scenario.id}: {exc}", file=sys.stderr)
            failures.append(scenario.id)
        time.sleep(PAUSE_BETWEEN_CALLS_S)

    report_path = aggregate_bug_report()
    print(f"\nAggregated bug report written to: {report_path}")

    if failures:
        print(f"\n{len(failures)} scenario(s) failed: {failures}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
