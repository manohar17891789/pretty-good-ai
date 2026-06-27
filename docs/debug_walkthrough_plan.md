# Screen-Recorded Debugging/Fix Walkthrough Plan

Goal: demonstrate a real debugging cycle on this codebase, not a staged
one. Candidate B below actually reproduced during the real call batch
and was fixed for real — record that one. Candidate A is left as a
secondary option only if time permits.

## What actually happened (record this)

During the first full 12-scenario batch run against the real Twilio test
line, 6 of 12 calls failed with an unhandled exception partway through
`place_call()` in `src/caller.py`, even though every one of the 12
underlying phone conversations completed correctly (confirmed via the
Flask server's `/gather` logs showing full, coherent turn-by-turn
dialogue for all 12 calls).

**Recording script:**
1. Show the terminal output from the failing batch run — the
   `run_all` summary line listing the 6 failed scenario IDs, and the
   traceback/404 coming from `download_recording()` in
   `src/recording.py`.
2. Open `src/recording.py` and walk through `download_recording()`
   before the fix: `wait_for_recording()` polls `client.recordings.list()`
   until it returns a recording, then the code does a single `GET` on
   the derived media URL and calls `resp.raise_for_status()` immediately.
   Explain the race: Twilio's recording-list API can report a recording
   as "found" slightly before the `.mp3` is actually live on Twilio's
   CDN, so that single immediate GET can 404 even though
   `wait_for_recording()` just succeeded.
3. Show the fix diff: the GET is now wrapped in a loop (up to 6 attempts,
   backing off `5 * attempt` seconds) that retries specifically on a 404
   status; any other status still fails fast via `raise_for_status()`.
4. Re-run one of the previously-failing scenarios live
   (`python -m src.run_call <scenario_id>`) and show the recording
   downloading cleanly with no 404, the transcript and bug-findings files
   being written, end to end.
5. Mention `docs/changelog.md`'s "v0.2" entry, which documents this same
   root cause and fix for the record.

## Candidates not used (kept for reference)

### Candidate bug A: live ASR misrecognition causing a derailed turn

**Symptom:** `calls/transcripts/<scenario>_*.md`'s live transcript shows
the patient bot replying to something the agent didn't actually say,
while the Whisper backup transcript for the same turn shows what was
really said.

**Walkthrough steps to record:**
1. Show the live vs. Whisper transcript diff side by side for the
   affected turn.
2. Open `src/telephony/server.py`'s `/gather` handler, point at
   `SpeechResult` being passed straight to `PatientBot.respond()` with no
   confidence check.
3. Fix: read Twilio's `Confidence` field from the Gather callback; below a
   threshold, treat it like an empty result (re-prompt) instead of feeding
   a low-confidence guess to the LLM.
4. Re-run `python -m src.simulate <scenario>` or a fresh real call to show
   the corrected behavior, and add/update a test in `tests/test_twiml.py`
   or a new `tests/test_server.py` asserting the confidence gate.

### Candidate bug B: call ends before the recording is available for download

**Symptom:** `download_recording` in `src/recording.py` occasionally
returns `None` right after a call completes because Twilio hasn't
finished processing the recording yet, even though `wait_for_recording`
polls for it.

**Walkthrough steps to record:**
1. Show the `WARNING: no recording found for this call.` log line from a
   real `run_call` invocation.
2. Open `src/recording.py`, point at `wait_for_recording`'s timeout/poll
   loop, and reason about why the default 30s window might not be enough
   right after `CallStatus=completed`.
3. Fix: increase `timeout_s`, and/or switch to a `RecordingStatusCallback`
   on the call (Twilio pushes a webhook the moment the recording is
   actually ready) instead of polling blindly.
4. Re-run the affected scenario, confirm the `.mp3` now downloads, and
   show the resulting `calls/recordings/` file and transcript.

## Recording notes

Capture the actual error/log output first (don't fake it), then the fix
diff, then the passing re-run — that sequence is what makes this a real
debugging walkthrough rather than a tour of code that already works.