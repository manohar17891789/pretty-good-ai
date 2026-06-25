from src.telephony.twiml import (
    VOICES,
    gather_response,
    hangup_only,
    say_and_hangup,
    voice_for_scenario,
)


def test_voice_for_scenario_is_stable():
    v1 = voice_for_scenario("schedule_simple")
    v2 = voice_for_scenario("schedule_simple")
    assert v1 == v2
    assert v1 in VOICES


def test_gather_response_contains_say_and_action():
    xml = gather_response("hello there", "https://example.com/gather/x", "Polly.Joanna-Neural", "https://example.com/voice/x")
    assert "<Gather" in xml
    assert "hello there" in xml
    assert "https://example.com/gather/x" in xml


def test_say_and_hangup_contains_hangup():
    xml = say_and_hangup("goodbye", "Polly.Joanna-Neural")
    assert "<Hangup" in xml
    assert "goodbye" in xml


def test_hangup_only():
    xml = hangup_only()
    assert "<Hangup" in xml
