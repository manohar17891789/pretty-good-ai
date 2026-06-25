"""Per-call bug/quality-issue extraction, plus aggregation into one report.

We deliberately ask for *findings with evidence*, not a generic quality
score - vague "agent could be more empathetic" notes aren't actionable.
Each finding must quote the transcript and say what a correct agent should
have done instead, so the bug report is useful rather than noise.
"""

import json
from pathlib import Path

from openai import OpenAI

from src.config import Config

DOCS_DIR = Path(__file__).resolve().parent.parent / "docs"

RUBRIC_PROMPT = """You are a QA analyst reviewing a transcript of a phone call between a \
patient (played by an automated test caller) and a medical clinic's phone \
agent. The "patient_bot" speaker is the test caller; the "human_agent" \
speaker is the system under test.

Review the transcript and identify concrete bugs or quality issues in the \
human_agent's behavior. Only report things that would matter to a real \
clinic. Categories to consider (do not force a finding into every category):
- factual_error: gave incorrect or contradictory information (hours, insurance, policy, scheduling)
- task_failure: failed to complete the patient's stated request despite having the chance to
- ignored_input: ignored or talked past something the patient explicitly said or asked
- broken_flow: repeated itself, looped, lost context, or contradicted its own earlier statement
- scope_violation: promised or did something a front-desk agent shouldn't (e.g. medical advice, controlled substance refill) without escalating
- confirmation_gap: failed to confirm key details (date/time, name, medication, etc.) before concluding
- tone_naturalness: broke character, sounded robotic/scripted in a way a real caller would notice, or had unnatural dead air implied by abrupt non-sequiturs
- other: anything else concretely wrong

For each finding return: category, severity (low/medium/high), a short \
title, a direct quote from the transcript as evidence, and what the agent \
should have done instead. If there are truly no issues, return an empty list.

Respond ONLY with JSON in this shape:
{{"findings": [{{"category": "...", "severity": "...", "title": "...", "evidence": "...", "should_have": "..."}}]}}

Transcript:
{transcript_text}
"""


def _format_transcript(turns: list[dict]) -> str:
    lines = []
    for turn in turns:
        speaker = turn.get("speaker", "unknown")
        lines.append(f"{speaker}: {turn.get('text', '')}")
    return "\n".join(lines)


def extract_bugs(config: Config, scenario_id: str, turns: list[dict]) -> list[dict]:
    client = OpenAI(api_key=config.openai_api_key)
    prompt = RUBRIC_PROMPT.format(transcript_text=_format_transcript(turns))
    completion = client.chat.completions.create(
        model=config.openai_chat_model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        response_format={"type": "json_object"},
    )
    raw = completion.choices[0].message.content
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return []
    findings = parsed.get("findings", [])
    for finding in findings:
        finding["scenario_id"] = scenario_id
    return findings


def save_findings(scenario_id: str, findings: list[dict]) -> Path:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    findings_dir = DOCS_DIR / "findings"
    findings_dir.mkdir(parents=True, exist_ok=True)
    path = findings_dir / f"{scenario_id}.json"
    path.write_text(json.dumps(findings, indent=2))
    return path


def aggregate_bug_report() -> Path:
    findings_dir = DOCS_DIR / "findings"
    all_findings: list[dict] = []
    if findings_dir.exists():
        for path in sorted(findings_dir.glob("*.json")):
            all_findings.extend(json.loads(path.read_text()))

    severity_order = {"high": 0, "medium": 1, "low": 2}
    all_findings.sort(key=lambda f: severity_order.get(f.get("severity", "low"), 3))

    lines = ["# Bug Report", "", f"Total findings: {len(all_findings)}", ""]

    by_severity: dict[str, int] = {}
    for f in all_findings:
        by_severity[f.get("severity", "unknown")] = by_severity.get(f.get("severity", "unknown"), 0) + 1
    if by_severity:
        lines.append("## Summary by severity")
        lines.append("")
        for sev, count in sorted(by_severity.items()):
            lines.append(f"- **{sev}**: {count}")
        lines.append("")

    lines.append("## Findings")
    lines.append("")
    for f in all_findings:
        lines.append(f"### [{f.get('severity', '?').upper()}] {f.get('title', '(untitled)')}")
        lines.append(f"- Scenario: `{f.get('scenario_id', '?')}`")
        lines.append(f"- Category: `{f.get('category', '?')}`")
        lines.append(f"- Evidence: \"{f.get('evidence', '')}\"")
        lines.append(f"- Should have: {f.get('should_have', '')}")
        lines.append("")

    out_path = DOCS_DIR / "bug_report.md"
    out_path.write_text("\n".join(lines))
    return out_path
