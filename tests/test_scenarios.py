from src.scenarios import SCENARIOS, get_scenario

REQUIRED_CATEGORIES = {
    "scheduling",
    "reschedule_cancel",
    "medication_refill",
    "info_hours_insurance",
    "edge_case",
}


def test_at_least_ten_scenarios():
    assert len(SCENARIOS) >= 10


def test_unique_ids():
    ids = [s.id for s in SCENARIOS]
    assert len(ids) == len(set(ids))


def test_all_required_categories_present():
    categories = {s.category for s in SCENARIOS}
    assert REQUIRED_CATEGORIES.issubset(categories)


def test_every_scenario_has_opening_line_and_goal():
    for s in SCENARIOS:
        assert s.opening_line.strip()
        assert s.goal.strip()
        assert s.persona.strip()


def test_get_scenario_lookup():
    s = get_scenario(SCENARIOS[0].id)
    assert s.id == SCENARIOS[0].id


def test_get_scenario_missing_raises():
    try:
        get_scenario("does_not_exist")
        assert False, "expected KeyError"
    except KeyError:
        pass
