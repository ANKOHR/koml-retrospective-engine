import pytest
from koml_retrospective_engine.core import analyze, SchemaError
from koml_retrospective_engine.fixtures import fixture_records

@pytest.mark.parametrize("field,value", [("cost_pence", -1), ("duration_minutes", True), ("completed_on", "2026-10-01"), ("summary", "x"*100001), ("status", "unknown"), ("budget_pence", 1.5)], ids=["negative", "bool", "future", "extreme", "status", "float"])
def test_rejects_adversarial_values(field, value):
    records = fixture_records(); records[0][field] = value
    with pytest.raises(SchemaError, match=field): analyze(records, "2026-09-30")

def test_duplicate_ids():
    records = fixture_records(); records[1]["id"] = records[0]["id"]
    with pytest.raises(SchemaError, match="duplicate"): analyze(records, "2026-09-30")

def test_handles_unicode_and_long_inputs():
    records = fixture_records(); records[0]["summary"] = "任務 café C:\\Users\\henry " + "a"*50000
    assert analyze(records, "2026-09-30")["postmortems"][0]["summary"] == records[0]["summary"]

def test_corrupted_ground_truth_changes_output():
    records = fixture_records(); records[100]["status"] = "failed"
    assert analyze(records, "2026-09-30")["totals"]["significant"] == 61


def test_overlapping_triggers_count_one_postmortem():
    r = fixture_records()[0]; r["cost_pence"] = 150; r["duration_minutes"] = 180
    result = analyze([r], "2026-09-30")
    assert result["totals"]["significant"] == 1
    assert result["postmortems"][0]["triggers"] == ["failed", "over_budget", "over_duration"]

def test_boundary_equality_is_not_significant():
    r = fixture_records()[100]; r["duration_minutes"] = r["planned_minutes"]
    assert analyze([r], "2026-09-30")["totals"]["significant"] == 0
