Per-call transcripts land here automatically (`<scenario>_<timestamp>.md`
and `.json`), written by `src/transcript_writer.py` each time
`python -m src.run_call` / `run_all.py` completes a call. None exist yet in
this checkout because no real call has been placed in this build
environment (no Twilio/OpenAI credentials, no telephony access). Run
`python -m src.run_all` after filling in `.env` to populate this folder
with at least 10 transcripts.
