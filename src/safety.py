"""Hard guardrail: this bot may only ever call the designated test number.

This constant is intentionally not read from the environment so a bad
.env value can never widen the set of numbers this code will dial.
"""

ALLOWED_TEST_NUMBER = "+18054398008"


class DisallowedNumberError(Exception):
    pass


def assert_allowed_number(number: str) -> None:
    normalized = number.strip().replace(" ", "").replace("-", "")
    if normalized != ALLOWED_TEST_NUMBER:
        raise DisallowedNumberError(
            f"Refusing to call {number!r}. This bot is only allowed to call "
            f"{ALLOWED_TEST_NUMBER}."
        )
