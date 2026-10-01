"""Deterministic rendering with explicit provenance on every report."""
import json

def banner(result):
    t = result["totals"]
    return (f"Data provenance: {t['synthetic']} synthetic fixture missions; "
            f"{t['real_operator_entered']} real operator-entered missions (declared by input, not independently verified).")

def render(result, format="md"):
    if format == "json":
        return json.dumps({"provenance": banner(result), **result}, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    lines = ["# KOML retrospective report", "", banner(result), "", f"As of: {result['as_of']}", "",
             "Figures below are computed from supplied inputs; synthetic figures are not real outcomes.", ""]
    lines += [f"- {k}: {v}" for k, v in result["totals"].items()]
    lines += ["", result["savings"], ""]
    for r in result["postmortems"]:
        lines += [f"## {r['id']}", "", "Provenance: " + ("synthetic" if r["synthetic"] else "real operator-entered"),
            f"Triggers: {', '.join(r['triggers'])}", f"Summary (operator supplied): {r['summary']}",
            f"Cost: {r['cost_pence']} pence; budget: {r['budget_pence']} pence",
            f"Duration: {r['duration_minutes']} minutes; planned: {r['planned_minutes']} minutes",
            f"Cause: {r['cause']}", f"Lesson (operator supplied): {r['lesson']}", f"Action: {r['action']}", ""]
    return "\n".join(lines) + "\n"
