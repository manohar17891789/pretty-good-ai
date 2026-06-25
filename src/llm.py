"""LLM wrapper for the patient bot's conversational turns.

Responses are deliberately kept to 1-3 short sentences: long replies read
fine as text but make a phone call sound like a monologue and add TTS
latency. Natural disfluencies ("um", "sorry, one sec") are allowed but not
forced every turn, since overusing them sounds scripted too.
"""

from openai import OpenAI

from src.config import Config
from src.scenarios import Scenario

SYSTEM_PROMPT_TEMPLATE = """You are role-playing as a patient calling their doctor's office on the \
phone. Stay fully in character as the patient at all times. Never mention \
that you are an AI, a bot, or that this is a test.

Persona: {persona}

Your goal for this call: {goal}

Conversational style:
- Speak like a real person on the phone: short sentences, contractions, occasional natural filler ("um", "let me think").
- Keep each reply to 1-3 sentences. Do not info-dump.
- Answer the agent's questions naturally and stay on topic; don't repeat yourself.
- Pursue your goal proactively. If the agent doesn't ask something needed to reach the goal, bring it up yourself.
- If the agent says or does something confusing, contradictory, or wrong, react like a real patient would (ask for clarification, push back politely, or express mild confusion) instead of just accepting it.
- Known quirks for this call: {quirks}
- When your goal has been reached (or it's clearly a dead end), wrap up politely and say goodbye, then output the exact token [END_CALL] at the end of your message.
"""


def build_system_prompt(scenario: Scenario) -> str:
    quirks = "; ".join(scenario.quirks) if scenario.quirks else "none in particular"
    return SYSTEM_PROMPT_TEMPLATE.format(
        persona=scenario.persona, goal=scenario.goal, quirks=quirks
    )


class PatientBot:
    def __init__(self, config: Config, scenario: Scenario):
        self.client = OpenAI(api_key=config.openai_api_key)
        self.model = config.openai_chat_model
        self.scenario = scenario
        self.history: list[dict] = [
            {"role": "system", "content": build_system_prompt(scenario)}
        ]

    def opening_line(self) -> str:
        self.history.append({"role": "assistant", "content": self.scenario.opening_line})
        return self.scenario.opening_line

    def respond(self, agent_utterance: str) -> tuple[str, bool]:
        """Returns (reply_text, should_end_call)."""
        self.history.append({"role": "user", "content": agent_utterance})
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=self.history,
            temperature=0.8,
            max_tokens=120,
        )
        raw = completion.choices[0].message.content.strip()
        should_end = "[END_CALL]" in raw
        reply = raw.replace("[END_CALL]", "").strip()
        self.history.append({"role": "assistant", "content": reply})
        return reply, should_end

    def transcript(self) -> list[dict]:
        return [m for m in self.history if m["role"] != "system"]
