import json
from koml_retrospective_engine.core import analyze
from koml_retrospective_engine.fixtures import fixture_records, EXPECTED
from koml_retrospective_engine.report import render

def result(): return analyze(fixture_records(), "2026-09-30")

def test_report_matches_ground_truth_exact():
    assert json.loads(render(result(), "json"))["totals"] == EXPECTED

def test_report_zero_false_positives():
    assert [r["id"] for r in result()["postmortems"]] == [f"mission-{i:03}" for i in range(60)]

def test_report_carries_provenance_banner():
    for fmt in ("md", "json"):
        assert "200 synthetic fixture missions" in render(result(), fmt)

def test_hypothetical_figures_labelled():
    for fmt in ("md", "json"):
        assert "Unmeasured: no measured baseline" in render(result(), fmt)
        assert "No cause inferred" in render(result(), fmt)

def test_determinism_byte_identical():
    for fmt in ("md", "json"):
        assert render(result(), fmt).encode() == render(result(), fmt).encode()

def test_no_em_dashes_in_outputs():
    for fmt in ("md", "json"):
        assert chr(0x2014) not in render(result(), fmt)
