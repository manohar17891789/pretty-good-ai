"""TwiML construction helpers.

Voice: Twilio's `<Say>` with an Amazon Polly Neural voice instead of a
separate TTS service + `<Play>`. Tradeoff: Polly Neural sounds a little
less expressive than ElevenLabs-grade voices, but it's synthesized
server-side by Twilio with no extra network hop, no hosting of audio
files, and no added per-call cost beyond the call itself - the right
tradeoff for latency and cost on a fixed budget.

Gather: nesting `<Say>` inside `<Gather input="speech">` lets the agent's
speech start being recognized as soon as our bot starts talking, which is
what gives us natural barge-in / interruption behavior without any extra
plumbing.
"""

from twilio.twiml.voice_response import VoiceResponse, Gather

# A small rotation of Polly neural voices so different scenarios don't all
# sound like the exact same caller.
VOICES = [
    "Polly.Joanna-Neural",
    "Polly.Matthew-Neural",
    "Polly.Kendra-Neural",
    "Polly.Joey-Neural",
    "Polly.Salli-Neural",
    "Polly.Kimberly-Neural",
]


def voice_for_scenario(scenario_id: str) -> str:
    return VOICES[hash(scenario_id) % len(VOICES)]


def gather_response(say_text: str, gather_action: str, voice: str, retry_action: str) -> str:
    vr = VoiceResponse()
    gather = Gather(
        input="speech",
        action=gather_action,
        method="POST",
        speech_timeout="auto",
        action_on_empty_result=True,
        language="en-US",
    )
    gather.say(say_text, voice=voice)
    vr.append(gather)
    # If Gather itself returns without ever hitting `action` (shouldn't
    # normally happen since action_on_empty_result=True), fall back here.
    vr.redirect(retry_action, method="POST")
    return str(vr)


def say_and_hangup(say_text: str, voice: str) -> str:
    vr = VoiceResponse()
    vr.say(say_text, voice=voice)
    vr.hangup()
    return str(vr)


def hangup_only() -> str:
    vr = VoiceResponse()
    vr.hangup()
    return str(vr)
