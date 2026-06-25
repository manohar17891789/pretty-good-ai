"""Places one outbound call for a given scenario and runs the full pipeline:
dial -> wait for completion -> fetch live transcript from the webhook
server -> download recording -> Whisper backup transcript -> bug-finding
extraction -> save everything under calls/.

This is the only place that actually dials a phone number, and it always
runs the number through src.safety.assert_allowed_number first.
"""

import sys
import time
from datetime import datetime, timezone

import requests
from twilio.rest import Client

from src.bug_report import extract_bugs, save_findings
from src.config import load_config
from src.recording import download_recording, transcribe_with_whisper
from src.safety import ALLOWED_TEST_NUMBER, assert_allowed_number
from src.scenarios import get_scenario
from src.transcript_writer import write_transcript

TERMINAL_STATUSES = {"completed", "busy", "failed", "no-answer", "canceled"}


def place_call(scenario_id: str, skip_bug_analysis: bool = False) -> None:
    config = load_config()
    assert_allowed_number(ALLOWED_TEST_NUMBER)  # belt-and-suspenders; see also Calls.create below
    scenario = get_scenario(scenario_id)

    if not config.public_base_url:
        raise RuntimeError("PUBLIC_BASE_URL is not set in .env - point it at your ngrok https URL.")

    client = Client(config.twilio_account_sid, config.twilio_auth_token)

    to_number = ALLOWED_TEST_NUMBER
    assert_allowed_number(to_number)  # hard stop before any Twilio API call

    started_at = datetime.now(timezone.utc).isoformat()
    print(f"Dialing {to_number} for scenario '{scenario_id}'...")

    call = client.calls.create(
        to=to_number,
        from_=config.twilio_caller_number,
        url=f"{config.public_base_url}/voice/{scenario_id}",
        status_callback=f"{config.public_base_url}/status",
        status_callback_event=["completed"],
        record=True,
        timeout=30,
    )
    call_sid = call.sid
    print(f"Call placed: {call_sid}. Waiting for completion...")

    while True:
        fetched = client.calls(call_sid).fetch()
        if fetched.status in TERMINAL_STATUSES:
            print(f"Call ended with status: {fetched.status}")
            break
        time.sleep(3)

    transcript_resp = requests.get(f"{config.public_base_url}/transcript/{call_sid}", timeout=10)
    if transcript_resp.status_code != 200:
        print("WARNING: could not fetch live transcript from webhook server.", file=sys.stderr)
        turns = []
    else:
        turns = transcript_resp.json().get("transcript", [])

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    base_filename = f"{scenario_id}_{timestamp}"

    recording_path = download_recording(config, client, call_sid, f"{base_filename}.mp3")
    whisper_text = None
    if recording_path:
        print(f"Recording saved: {recording_path}")
        try:
            whisper_text = transcribe_with_whisper(config, recording_path)
        except Exception as exc:  # whisper failure shouldn't lose the live transcript
            print(f"WARNING: Whisper transcription failed: {exc}", file=sys.stderr)
    else:
        print("WARNING: no recording found for this call.", file=sys.stderr)

    json_path, md_path = write_transcript(
        base_filename=base_filename,
        scenario_id=scenario_id,
        call_sid=call_sid,
        started_at=started_at,
        turn_transcript=turns,
        whisper_backup=whisper_text,
        recording_filename=recording_path.name if recording_path else None,
    )
    print(f"Transcript saved: {md_path}")

    if not skip_bug_analysis and turns:
        findings = extract_bugs(config, scenario_id, turns)
        findings_path = save_findings(scenario_id, findings)
        print(f"Bug findings ({len(findings)}) saved: {findings_path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m src.caller <scenario_id>")
        sys.exit(1)
    place_call(sys.argv[1])
