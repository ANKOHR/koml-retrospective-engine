import json
from koml_retrospective_engine.fixtures import generate, fixture_records, EXPECTED
from koml_retrospective_engine.core import analyze

def test_fixtures_labelled_synthetic(tmp_path):
    generate(tmp_path)
    for p in tmp_path.glob("*.json"):
        assert json.loads(p.read_text())["synthetic"] is True
    assert "synthetic: true" in (tmp_path/"LABEL.md").read_text()
    assert all(r["synthetic"] for r in fixture_records())

def test_fixture_ground_truth_matches_hand_computed():
    assert analyze(fixture_records(), "2026-09-30")["totals"] == EXPECTED
