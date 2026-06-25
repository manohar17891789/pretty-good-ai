# Architecture

The bot is a Twilio outbound call driven by a local Flask webhook server.
For each test scenario, `src/caller.py` places a call to the fixed test
number through the Twilio REST API with `record=True` and a webhook URL
pointing at `src/telephony/server.py` (tunneled via ngrok). Once the
clinic agent answers, Twilio hits `/voice/<scenario_id>`, which spins up a
`PatientBot` (an OpenAI chat-completion session seeded with that
scenario's persona, goal, and conversational quirks) and returns TwiML
that speaks the bot's opening line inside a `<Gather input="speech">`
block. Nesting `<Say>` inside `<Gather>` is what gives the call natural
barge-in: Twilio starts listening for the agent's speech the moment our
bot starts talking, so an agent (or our bot, in the interruption scenario)
can cut in mid-sentence instead of waiting for silence. Every subsequent
turn is the same loop: Twilio posts the agent's recognized speech to
`/gather/<scenario_id>`, the server feeds it to the `PatientBot`, gets a
short (1–3 sentence) in-character reply plus an end-of-call signal, and
returns either another `<Gather>` or a `<Say>+<Hangup>`. Turn-taking is
intentionally simple and deterministic (one HTTP round trip per turn, no
raw audio streaming) — it trades a small amount of TTS/ASR latency
compared to a full real-time speech-to-speech pipeline for something far
easier to run, debug, and keep within budget.

After the call ends, `caller.py` polls the Twilio API for terminal call
status, pulls the live turn-by-turn transcript back from the webhook
server's in-memory state (`GET /transcript/<call_sid>`), downloads the
recorded audio, and runs it through Whisper as a second, more accurate
transcript to catch anything Twilio's live speech recognition mangled
(particularly clinical/insurance terminology). Both transcripts are
written to `calls/transcripts/` alongside the `.mp3` in
`calls/recordings/`. Finally, the merged transcript is sent to an LLM
seeded with a fixed QA rubric (factual errors, task failures, ignored
input, broken flow, scope violations, missing confirmations, unnatural
behavior) that returns structured findings with a direct transcript quote
as evidence and what the agent should have done instead; these are saved
per-scenario and rolled up into `docs/bug_report.md` by
`src/bug_report.py`. The entire pipeline for all scenarios runs from one
command, `python -m src.run_all`, with a single hardcoded
`ALLOWED_TEST_NUMBER` guardrail in `src/safety.py` enforced immediately
before every outbound call.
