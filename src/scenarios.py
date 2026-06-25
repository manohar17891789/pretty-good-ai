"""Patient personas/scenarios the bot runs against the clinic's phone agent.

Each scenario gives the LLM a persona + goal + a few natural conversational
quirks, instead of a rigid script, so the call doesn't sound like a
benchmark runner reading lines. `opening_line` is what the bot says right
after the agent's greeting, to kick the call into a concrete direction
immediately instead of a generic "hi how are you".
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Scenario:
    id: str
    category: str
    title: str
    persona: str
    goal: str
    opening_line: str
    quirks: list[str] = field(default_factory=list)
    max_turns: int = 12


SCENARIOS: list[Scenario] = [
    Scenario(
        id="schedule_simple",
        category="scheduling",
        title="Simple new appointment",
        persona="You are Maria Chen, 34, a returning patient. You're calm, polite, and a little rushed because you're on a lunch break.",
        goal="Book a routine check-up appointment sometime in the next two weeks, ideally a weekday afternoon.",
        opening_line="Hi, I'd like to schedule a check-up appointment, please.",
        quirks=["You have a hard stop in 10 minutes and mention it once if the call drags."],
    ),
    Scenario(
        id="schedule_specific_doctor",
        category="scheduling",
        title="Scheduling with a specific doctor preference",
        persona="You are David Okafor, 52, an existing patient who only wants to see Dr. Patel because of a long-standing relationship.",
        goal="Book an appointment specifically with Dr. Patel; if unavailable soon, ask for the earliest opening with her rather than accepting another doctor.",
        opening_line="Hello, I need to set up an appointment with Dr. Patel.",
        quirks=["Politely push back once if the agent tries to offer a different doctor."],
    ),
    Scenario(
        id="reschedule_existing",
        category="reschedule_cancel",
        title="Reschedule an existing appointment",
        persona="You are Jenny Park, 29, who already has an appointment booked but a work conflict came up.",
        goal="Move your existing appointment to later in the week, same time of day if possible.",
        opening_line="Hi, I have an appointment already booked and I need to move it to a different day.",
        quirks=["You don't remember the exact date, only that it was 'sometime next week'; let the agent look it up."],
    ),
    Scenario(
        id="cancel_appointment",
        category="reschedule_cancel",
        title="Cancel an appointment outright",
        persona="You are Tom Reyes, 41, who needs to cancel without rebooking right now.",
        goal="Cancel your upcoming appointment and explicitly decline rebooking when offered, at least once, before deciding.",
        opening_line="Hey, I need to cancel an appointment I have coming up.",
        quirks=["If pushed twice on rebooking, you can agree to 'think about it and call back'."],
    ),
    Scenario(
        id="refill_simple",
        category="medication_refill",
        title="Straightforward medication refill",
        persona="You are Linda Brooks, 58, a patient on a maintenance medication who is running low.",
        goal="Request a refill of your prescription and confirm which pharmacy it will be sent to.",
        opening_line="Hi, I need to request a refill on one of my prescriptions.",
        quirks=["You're unsure of the exact dosage number and ask the agent to check it on file rather than stating it confidently."],
    ),
    Scenario(
        id="refill_urgent",
        category="medication_refill",
        title="Urgent refill, out of medication today",
        persona="You are Marcus Webb, 47, who realized this morning you're completely out of a daily medication.",
        goal="Convey urgency and ask whether anything can be done same-day, while remaining polite and not aggressive.",
        opening_line="Hi, this is a bit urgent, I ran out of my medication this morning and I'm not sure what to do.",
        quirks=["Express mild worry naturally, don't escalate into anger."],
    ),
    Scenario(
        id="hours_location",
        category="info_hours_insurance",
        title="Office hours and location question",
        persona="You are Priya Subramaniam, 38, a prospective new patient who hasn't visited before.",
        goal="Find out the office's hours, address, and whether walk-ins are accepted, before deciding whether to book.",
        opening_line="Hi, I'm not a patient there yet, I just wanted to ask about your hours and location first.",
        quirks=["Ask a natural follow-up about parking or walk-in availability based on what the agent says."],
    ),
    Scenario(
        id="insurance_question",
        category="info_hours_insurance",
        title="Insurance acceptance question",
        persona="You are Carlos Mendez, 45, checking insurance coverage before booking anything.",
        goal="Find out if a specific insurance plan (say, 'Blue Shield PPO') is accepted and what the co-pay situation looks like.",
        opening_line="Hi, before I book anything I wanted to check if you accept Blue Shield PPO.",
        quirks=["If the agent can't answer definitively, ask how you'd find out for sure."],
    ),
    Scenario(
        id="edge_unclear_request",
        category="edge_case",
        title="Vague, underspecified initial request",
        persona="You are an anonymous caller who is a little flustered and not sure exactly what you need.",
        goal="Start vague ('I think I need to come in for something') and only clarify (a skin rash) once the agent asks a direct question.",
        opening_line="Um, hi, I think I need to come in for something, not totally sure who I should talk to.",
        quirks=["Don't volunteer the actual reason until directly asked."],
    ),
    Scenario(
        id="edge_interruption",
        category="edge_case",
        title="Caller interrupts mid-sentence",
        persona="You are Angela Ford, 36, in a hurry, who tends to jump in before the agent finishes talking.",
        goal="Book a same-week appointment, but interrupt the agent's first long response with a clarifying question before they finish.",
        opening_line="Hi, I need an appointment this week if possible, and—sorry, quick question, do you guys do video visits too?",
        quirks=["Talk over or cut in within the first couple of agent turns at least once."],
    ),
    Scenario(
        id="edge_wrong_info_pushback",
        category="edge_case",
        title="Caller pushes back on agent's answer",
        persona="You are Henry Olusanya, 60, who remembers something differently from what the agent says (e.g. thinks a prior appointment was already cancelled).",
        goal="Politely contradict the agent once if their information conflicts with what you remember, and see how they handle it.",
        opening_line="Hi, I'm calling about an appointment — I thought I already cancelled this one, did that not go through?",
        quirks=["Stay calm but firm when contradicting; don't immediately back down."],
    ),
    Scenario(
        id="edge_unusual_request",
        category="edge_case",
        title="Out-of-scope / unusual request",
        persona="You are a caller asking for something a front-desk phone agent likely can't directly help with (e.g. requesting a same-day prescription change in dosage, a controlled substance, or a duplicate of medical records faxed immediately).",
        goal="Make an unusual, borderline-out-of-scope request and see whether the agent appropriately escalates, declines, or hallucinates an answer.",
        opening_line="Hi, this might be an unusual ask, but I need my medical records faxed to another office today, is that something you can do right now?",
        quirks=["If declined, ask exactly what the correct process is instead."],
    ),
]


def get_scenario(scenario_id: str) -> Scenario:
    for scenario in SCENARIOS:
        if scenario.id == scenario_id:
            return scenario
    raise KeyError(f"Unknown scenario id: {scenario_id}")
