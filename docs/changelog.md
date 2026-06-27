# Changelog / Iteration Log

Reverse-chronological log of how this was built and why, kept for
"evidence of iteration."

## v0.1 — Initial build

- Decided against a real-time speech-to-speech architecture (Twilio Media
  Streams + a streaming model) in favor of a turn-based
  `<Gather input="speech">` + `<Say>` loop. Reasoning: the streaming
  approach sounds slightly more natural but needs a WebSocket bridge,
  audio framing/buffering, and is much harder to debug and keep within a
  $20 budget; the turn-based loop is one HTTP round trip per turn, trivial
  to log, and still supports barge-in because `<Say>` is nested inside
  `<Gather>`.
- Chose Twilio `<Say>` + Amazon Polly Neural voices over a separate TTS
  provider (e.g. ElevenLabs) for the patient bot's voice. Tradeoff: Polly
  is a notch less expressive, but it's synthesized server-side by Twilio
  with zero extra latency, no audio hosting, and no added per-call cost.
- Built `src/simulate.py` (two LLMs talking to each other in text, no
  telephony) specifically so scenario personas/goals could be sanity
  checked for naturalness before spending real Twilio minutes on them.
- Kept the live, turn-by-turn transcript (built from Twilio's Gather
  SpeechResult) as the primary transcript, and added a Whisper pass over
  the full recording as a secondary/backup transcript, after noticing
  Twilio's built-in speech recognition can mangle clinical/insurance
  terminology that matters for bug-finding accuracy.
- Added a hard, environment-independent guardrail (`src/safety.py`) that
  is checked immediately before every single outbound call, rather than
  trusting `.env` configuration alone, since a misconfigured `.env` value
  must never be able to widen which numbers get dialed.
- Defined 12 scenarios (more than the 10 minimum) explicitly covering all
  five required categories, including 4 distinct edge cases
  (vague/underspecified request, mid-sentence interruption, caller
  pushing back on incorrect info, an out-of-scope request) chosen because
  they're the failure modes most likely to surface real agent bugs rather
  than just exercising the happy path.
- Bug-report rubric (`src/bug_report.py`) was written to require a direct
  transcript quote and a "what should have happened instead" for every
  finding, specifically to avoid generic/unhelpful "could be more polite"
  style notes.

## v0.2 — Real call batch + recording-download fix

- Ran the full 12-scenario batch against the real Twilio test line for
  the first time. All 12 calls completed successfully end-to-end (live
  transcript captured, conversation correct), but 6 of 12 raised an
  unhandled 404 partway through `download_recording()` in
  `src/recording.py`, which aborted `place_call()` before the transcript
  or bug-findings write step ever ran for those scenarios — exactly
  "Candidate bug B" anticipated in `docs/debug_walkthrough_plan.md`.
- Root cause: `client.recordings.list(call_sid=...)` returns recording
  metadata slightly before the actual `.mp3` is live on Twilio's CDN, so
  the immediate `GET` on the media URL can 404 even though
  `wait_for_recording()` just confirmed the recording exists.
- Fix: wrapped the media `GET` itself in a retry loop (up to 6 attempts,
  backing off `5 * attempt` seconds) that only retries on a 404 response;
  any other failure still raises immediately via `resp.raise_for_status()`.
  This is a smaller, more targeted fix than the plan's original two
  options (raising `wait_for_recording`'s timeout, or switching to a
  `RecordingStatusCallback` webhook) — it fixes the actual observed race
  without adding webhook plumbing for a one-off download step.
- Re-ran the 6 affected scenarios individually after the fix; all 6
  downloaded cleanly on the first or second attempt with no further
  404s. Re-aggregated `docs/bug_report.md` so it now reflects findings
  from all 12 scenarios instead of the 6 that succeeded in the original
  batch run.

## Next iteration candidates (not yet done)

- Review the Whisper vs. live transcript diffs to see how often Twilio's
  live ASR caused the bot to misunderstand the agent, and tune
  `speech_timeout`/retry behavior if that's a frequent failure mode.
- If barge-in feels too aggressive or too passive, adjust
  `speech_timeout` and Gather sensitivity rather than the conversation
  prompt.
