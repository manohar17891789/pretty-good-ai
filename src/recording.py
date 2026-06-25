"""Download the Twilio call recording and run a Whisper backup transcription.

We keep two transcript sources per call:
  1. The structured turn-by-turn transcript built live from Twilio's Gather
     SpeechResult (fast, exactly time-aligned with what drove the bot's
     decisions, but Twilio's built-in ASR can mangle clinical/insurance
     terms).
  2. A Whisper transcription of the full recording (slower, after the call
     ends, but materially more accurate) used as the QA-grade backup and
     for catching anything the live ASR missed entirely.
"""

import time
from pathlib import Path

import requests
from openai import OpenAI
from twilio.rest import Client

from src.config import Config

RECORDINGS_DIR = Path(__file__).resolve().parent.parent / "calls" / "recordings"


def wait_for_recording(client: Client, call_sid: str, timeout_s: int = 30, poll_s: int = 2):
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        recordings = client.recordings.list(call_sid=call_sid)
        if recordings:
            return recordings[0]
        time.sleep(poll_s)
    return None


def download_recording(config: Config, client: Client, call_sid: str, dest_filename: str) -> Path | None:
    recording = wait_for_recording(client, call_sid)
    if recording is None:
        return None

    media_url = f"https://api.twilio.com{recording.uri.replace('.json', '.mp3')}"
    resp = requests.get(
        media_url,
        auth=(config.twilio_account_sid, config.twilio_auth_token),
        timeout=30,
    )
    resp.raise_for_status()

    RECORDINGS_DIR.mkdir(parents=True, exist_ok=True)
    dest_path = RECORDINGS_DIR / dest_filename
    dest_path.write_bytes(resp.content)
    return dest_path


def transcribe_with_whisper(config: Config, audio_path: Path) -> str:
    client = OpenAI(api_key=config.openai_api_key)
    with open(audio_path, "rb") as f:
        result = client.audio.transcriptions.create(
            model=config.openai_whisper_model,
            file=f,
        )
    return result.text
