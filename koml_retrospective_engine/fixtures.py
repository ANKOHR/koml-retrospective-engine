"""Synthetic, deterministic fixtures. No randomness; seed is not applicable."""
import json
from pathlib import Path

# Hand-computed: 20 failures, 20 budget breaches, 20 duration breaches.
# Cost: 20*50 + 20*150 + 160*100 = 20000 pence.
# Duration: 180*60 + 20*180 = 14400 minutes.
EXPECTED = {"missions": 200, "significant": 60, "synthetic": 200,
            "real_operator_entered": 0, "cost_pence": 20000, "duration_minutes": 14400,
            "failed": 20, "over_budget": 20, "over_duration": 20}

def fixture_records():
    return [{"id": f"mission-{i:03}", "synthetic": True,
        "completed_on": "2026-09-30", "status": "failed" if i < 20 else "succeeded",
        "cost_pence": 50 if i < 20 else 150 if i < 40 else 100,
        "budget_pence": 100, "duration_minutes": 180 if 40 <= i < 60 else 60,
        "planned_minutes": 120, "summary": f"Synthetic mission {i}",
        "lesson": "Synthetic operator lesson", "action": "Synthetic review action"} for i in range(200)]

def generate(out):
    path = Path(out)
    path.mkdir(parents=True, exist_ok=True)
    for name, value in (("missions.json", {"synthetic": True, "as_of": "2026-09-30", "records": fixture_records()}),
                        ("expectations.json", {"synthetic": True, "totals": EXPECTED,
                         "significant_ids": [f"mission-{i:03}" for i in range(60)]})):
        (path / name).write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    (path / "LABEL.md").write_text("<!-- synthetic: true -->\nAll files in this fixture set are synthetic. No real trial results.\n", encoding="utf-8")
