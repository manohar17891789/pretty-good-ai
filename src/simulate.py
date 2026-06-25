"""Text-only dry run: the patient bot talks to a second LLM playing a mock
clinic agent, with no Twilio/telephony involved at all.

Why this exists: telephony minutes and Twilio recordings cost real money
and are slow to iterate on. Before spending those, this lets you sanity
check a scenario's persona, goal, and conversational quality purely in
text, in a few seconds, for $0.0x in OpenAI usage. It is NOT a substitute
for the real call deliverables - just a fast feedback loop while writing
scenarios.

Usage:
    python -m src.simulate schedule_simple
"""

import sys

from openai import OpenAI

from src.config import load_config
from src.llm import PatientBot
from src.scenarios import get_scenario

MOCK_AGENT_SYSTEM_PROMPT = """You are a front-desk phone agent at a generic medical clinic. Be \
helpful, reasonably efficient, and mostly competent, but you are allowed to \
occasionally be slightly imperfect (e.g. ask for info already given, be a \
little vague on policy) since this is used to test a QA system. Keep \
replies to 1-3 sentences, phone-call style. Greet the caller first."""


def run_simulation(scenario_id: str, max_turns: int = 8) -> list[dict]:
    config = load_config()
    scenario = get_scenario(scenario_id)
    client = OpenAI(api_key=config.openai_api_key)
    patient = PatientBot(config, scenario)

    agent_history = [{"role": "system", "content": MOCK_AGENT_SYSTEM_PROMPT}]
    greeting = "Thanks for calling, how can I help you today?"
    agent_history.append({"role": "assistant", "content": greeting})

    transcript = [{"speaker": "human_agent", "text": greeting}]
    patient_reply = patient.opening_line()
    transcript.append({"speaker": "patient_bot", "text": patient_reply})

    for _ in range(max_turns):
        agent_history.append({"role": "user", "content": patient_reply})
        completion = client.chat.completions.create(
            model=config.openai_chat_model,
            messages=agent_history,
            temperature=0.7,
            max_tokens=120,
        )
        agent_text = completion.choices[0].message.content.strip()
        agent_history.append({"role": "assistant", "content": agent_text})
        transcript.append({"speaker": "human_agent", "text": agent_text})

        patient_reply, should_end = patient.respond(agent_text)
        transcript.append({"speaker": "patient_bot", "text": patient_reply})
        if should_end:
            break

    return transcript


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m src.simulate <scenario_id>")
        sys.exit(1)
    for turn in run_simulation(sys.argv[1]):
        print(f"{turn['speaker']}: {turn['text']}")
