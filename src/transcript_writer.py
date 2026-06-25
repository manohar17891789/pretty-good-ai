import json
from pathlib import Path

TRANSCRIPTS_DIR = Path(__file__).resolve().parent.parent / "calls" / "transcripts"


def write_transcript(
    base_filename: str,
    scenario_id: str,
    call_sid: str,
    started_at: str,
    turn_transcript: list[dict],
    whisper_backup: str | None,
    recording_filename: str | None,
) -> tuple[Path, Path]:
    TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)

    json_path = TRANSCRIPTS_DIR / f"{base_filename}.json"
    json_path.write_text(
        json.dumps(
            {
                "scenario_id": scenario_id,
                "call_sid": call_sid,
                "started_at": started_at,
                "recording_filename": recording_filename,
                "turns": turn_transcript,
                "whisper_backup_transcript": whisper_backup,
            },
            indent=2,
        )
    )

    md_lines = [
        f"# Call transcript - {scenario_id}",
        "",
        f"- Call SID: `{call_sid}`",
        f"- Started: {started_at}",
        f"- Recording: `{recording_filename}`" if recording_filename else "- Recording: (none captured)",
        "",
        "## Turn-by-turn (live, from Twilio speech recognition)",
        "",
    ]
    for turn in turn_transcript:
        speaker = "Patient bot" if turn["speaker"] == "patient_bot" else "Clinic agent"
        md_lines.append(f"**{speaker}:** {turn['text']}")
        md_lines.append("")

    if whisper_backup:
        md_lines += [
            "## Whisper backup transcript (full recording, single-stream)",
            "",
            whisper_backup,
            "",
        ]

    md_path = TRANSCRIPTS_DIR / f"{base_filename}.md"
    md_path.write_text("\n".join(md_lines))

    return json_path, md_path
