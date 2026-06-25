import pytest

from src.safety import ALLOWED_TEST_NUMBER, DisallowedNumberError, assert_allowed_number


def test_allowed_number_passes():
    assert_allowed_number(ALLOWED_TEST_NUMBER)


def test_disallowed_number_raises():
    with pytest.raises(DisallowedNumberError):
        assert_allowed_number("+15551234567")


def test_whitespace_and_dashes_normalized():
    assert_allowed_number("+1 805-439-8008")
