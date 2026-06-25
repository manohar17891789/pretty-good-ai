"""Local Flask webhook server that drives one call's turn-by-turn dialogue.

Twilio hits this server over a public tunnel (ngrok) while a call is live.
State per call is kept in memory, keyed by Twilio's CallSid - this process
is only ever meant to run for the duration of a local test session, not as
a persistent service, so no database is needed.
"""

import logging
from dataclasses import dataclass, field

from flask import Flask, request

from src.config import load_config
from src.llm import PatientBot
from src.scenarios import Scenario, get_scenario
from src.telephony.twiml import (
    gather_response,
    hangup_only,
    say_and_hangup,
    voice_for_scenario,
)

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("voicebot.server")

app = Flask(__name__)
config = load_config()

MAX_EMPTY_RETRIES = 2


@dataclass
class CallState:
    bot: PatientBot
    scenario: Scenario
    voice: str
    turns: int = 0
    empty_retries: int = 0
    transcript: list[dict] = field(default_factory=list)


CALLS: dict[str, CallState] = {}


def _base_url() -> str:
    return config.public_base_url


@app.route("/voice/<scenario_id>", methods=["POST"])
def voice(scenario_id: str):
    call_sid = request.form.get("CallSid", "")
    scenario = get_scenario(scenario_id)
    bot = PatientBot(config, scenario)
    voice_name = voice_for_scenario(scenario_id)
    opening = bot.opening_line()

    state = CallState(bot=bot, scenario=scenario, voice=voice_name)
    state.transcript.append({"speaker": "patient_bot", "text": opening})
    CALLS[call_sid] = state

    log.info("[%s] call started, scenario=%s", call_sid, scenario_id)

    gather_action = f"{_base_url()}/gather/{scenario_id}"
    retry_action = f"{_base_url()}/voice/{scenario_id}"
    return gather_response(opening, gather_action, voice_name, retry_action)


@app.route("/gather/<scenario_id>", methods=["POST"])
def gather(scenario_id: str):
    call_sid = request.form.get("CallSid", "")
    agent_speech = request.form.get("SpeechResult", "").strip()
    state = CALLS.get(call_sid)

    if state is None:
        log.warning("[%s] gather hit with no known call state", call_sid)
        return hangup_only()

    gather_action = f"{_base_url()}/gather/{scenario_id}"

    if not agent_speech:
        state.empty_retries += 1
        log.info("[%s] empty speech result (retry %d)", call_sid, state.empty_retries)
        if state.empty_retries > MAX_EMPTY_RETRIES:
            closing = "Sorry, I'm having trouble hearing you. I'll try calling back another time. Bye."
            state.transcript.append({"speaker": "patient_bot", "text": closing})
            return say_and_hangup(closing, state.voice)
        reprompt = "Sorry, I didn't catch that, could you say that again?"
        state.transcript.append({"speaker": "patient_bot", "text": reprompt})
        return gather_response(reprompt, gather_action, state.voice, gather_action)

    state.empty_retries = 0
    state.transcript.append({"speaker": "human_agent", "text": agent_speech})
    log.info("[%s] agent: %s", call_sid, agent_speech)

    state.turns += 1
    reply, should_end = state.bot.respond(agent_speech)
    state.transcript.append({"speaker": "patient_bot", "text": reply})
    log.info("[%s] patient_bot: %s", call_sid, reply)

    if should_end or state.turns >= state.scenario.max_turns:
        return say_and_hangup(reply, state.voice)

    return gather_response(reply, gather_action, state.voice, gather_action)


@app.route("/transcript/<call_sid>", methods=["GET"])
def transcript_endpoint(call_sid: str):
    state = CALLS.get(call_sid)
    if state is None:
        return {"error": "unknown call_sid"}, 404
    return {
        "call_sid": call_sid,
        "scenario_id": state.scenario.id,
        "turns": state.turns,
        "transcript": state.transcript,
    }


@app.route("/status", methods=["POST"])
def status():
    call_sid = request.form.get("CallSid", "")
    call_status = request.form.get("CallStatus", "")
    log.info("[%s] status callback: %s", call_sid, call_status)
    return "", 204


def get_transcript(call_sid: str) -> list[dict] | None:
    state = CALLS.get(call_sid)
    return state.transcript if state else None


def get_scenario_for_call(call_sid: str) -> Scenario | None:
    state = CALLS.get(call_sid)
    return state.scenario if state else None


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=config.port)
