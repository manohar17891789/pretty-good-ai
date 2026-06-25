# Screen-Recorded Debugging/Fix Walkthrough Plan

Goal: demonstrate a real debugging cycle on this codebase, not a staged
one. Pick whichever of the two below actually reproduces once real calls
have been run; both are realistic given the architecture.

## Candidate bug A: live ASR misrecognition causing a derailed turn

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

## Candidate bug B: call ends before the recording is available for download

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
