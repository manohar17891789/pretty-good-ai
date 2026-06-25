# Loom Walkthrough Plan

Target length: 4–6 minutes.

1. **Intro (15s)** — what this is: an automated patient-voice-bot that
   calls the clinic test line and QA's the agent on the other end.
2. **Architecture, on screen (60–90s)** — open `docs/architecture.md`,
   walk through the diagram-in-prose: Twilio call → Flask webhook → patient
   bot (LLM) → recording + Whisper backup → bug extraction. Point out the
   hardcoded safety guardrail in `src/safety.py`.
3. **Code tour (90s)** — `src/scenarios.py` (show 2-3 scenarios, explain
   persona/goal/quirks design instead of rigid scripts), `src/llm.py`
   (system prompt, why replies are short), `src/telephony/server.py` (the
   Gather/Say turn loop, barge-in via nested Say).
4. **Live (or recorded) call demo (90–120s)** — run
   `python -m src.run_call schedule_simple` against the real test number
   on screen, show the Flask server logs streaming each turn live, then
   show the resulting transcript `.md` and play a few seconds of the
   downloaded `.mp3`.
5. **Bug report (45s)** — open `docs/bug_report.md`, walk through 2-3
   concrete findings, emphasizing the evidence quote + "should have done
   instead" format.
6. **Wrap-up (15s)** — one command to reproduce everything
   (`python -m src.run_all`), cost note (~a few dollars total), and where
   to find all deliverables in the repo.

Recording notes: capture terminal + browser/editor, not full screen;
mute/skip any dead air while waiting for an actual call to connect (cut to
a pre-recorded segment if needed to keep total runtime tight).
