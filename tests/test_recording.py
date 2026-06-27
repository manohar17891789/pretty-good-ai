from unittest.mock import MagicMock, patch

from src.config import Config
from src.recording import download_recording


def _config() -> Config:
    return Config(
        twilio_account_sid="AC_test",
        twilio_auth_token="token_test",
        twilio_caller_number="+10000000000",
        public_base_url="https://example.test",
        port=5000,
        openai_api_key="sk-test",
        openai_chat_model="gpt-4o-mini",
        openai_whisper_model="whisper-1",
    )


def _fake_recording():
    recording = MagicMock()
    recording.uri = "/2010-04-01/Accounts/AC_test/Recordings/RE_test.json"
    return recording


def test_download_recording_retries_past_404_then_succeeds(tmp_path):
    """Regression test for the Twilio CDN propagation-delay race condition.

    wait_for_recording() can report a recording exists slightly before the
    actual media file is downloadable, so the first GET(s) may 404 even
    though the recording is genuinely there a few seconds later.
    """
    not_ready = MagicMock(status_code=404)
    ready = MagicMock(status_code=200, content=b"fake-audio-bytes")
    ready.raise_for_status = MagicMock()

    with (
        patch("src.recording.wait_for_recording", return_value=_fake_recording()),
        patch("src.recording.requests.get", side_effect=[not_ready, not_ready, ready]) as mock_get,
        patch("src.recording.time.sleep"),
        patch("src.recording.RECORDINGS_DIR", tmp_path),
    ):
        result = download_recording(_config(), MagicMock(), "CA_test", "test.mp3")

    assert result == tmp_path / "test.mp3"
    assert result.read_bytes() == b"fake-audio-bytes"
    assert mock_get.call_count == 3


def test_download_recording_raises_on_non_404_failure(tmp_path):
    server_error = MagicMock(status_code=500)
    server_error.raise_for_status.side_effect = Exception("server error")

    with (
        patch("src.recording.wait_for_recording", return_value=_fake_recording()),
        patch("src.recording.requests.get", return_value=server_error) as mock_get,
        patch("src.recording.RECORDINGS_DIR", tmp_path),
    ):
        try:
            download_recording(_config(), MagicMock(), "CA_test", "test.mp3")
            assert False, "expected an exception for a non-404 failure"
        except Exception:
            pass

    assert mock_get.call_count == 1