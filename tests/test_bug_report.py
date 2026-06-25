from src.bug_report import _format_transcript


def test_format_transcript_basic():
    turns = [
        {"speaker": "patient_bot", "text": "Hi, I'd like to book an appointment."},
        {"speaker": "human_agent", "text": "Sure, what day works for you?"},
    ]
    formatted = _format_transcript(turns)
    assert "patient_bot: Hi, I'd like to book an appointment." in formatted
    assert "human_agent: Sure, what day works for you?" in formatted
