"""Pure domain logic. Currency is integer pence; no estimates or model calls."""
from datetime import date

class SchemaError(ValueError):
    """Named invalid input error."""

FIELDS = {"id", "synthetic", "completed_on", "status", "cost_pence", "budget_pence",
          "duration_minutes", "planned_minutes", "summary", "lesson", "action"}

def validate(records, as_of):
    try:
        cutoff = date.fromisoformat(as_of)
    except (ValueError, TypeError):
        raise SchemaError("as_of: expected ISO date") from None
    seen = set()
    for index, record in enumerate(records, 1):
        prefix = f"record {index}"
        if not isinstance(record, dict):
            raise SchemaError(f"{prefix}: expected object")
        if set(record) != FIELDS:
            raise SchemaError(f"{prefix}: fields missing={sorted(FIELDS-set(record))} unknown={sorted(set(record)-FIELDS)}")
        for field in ("id", "summary", "lesson", "action"):
            value = record[field]
            if not isinstance(value, str) or len(value) > 100000 or "\u2014" in value:
                raise SchemaError(f"{prefix}: {field}: expected text of at most 100000 characters without em dash")
        if not record["id"] or record["id"] in seen:
            raise SchemaError(f"{prefix}: id: empty or duplicate")
        seen.add(record["id"])
        if type(record["synthetic"]) is not bool:
            raise SchemaError(f"{prefix}: synthetic: expected boolean")
        if record["status"] not in ("succeeded", "failed"):
            raise SchemaError(f"{prefix}: status: expected succeeded or failed")
        for field in ("cost_pence", "budget_pence", "duration_minutes", "planned_minutes"):
            value = record[field]
            if type(value) is not int or not 0 <= value <= 10**12:
                raise SchemaError(f"{prefix}: {field}: expected integer in 0..1000000000000")
        try:
            completed = date.fromisoformat(record["completed_on"])
        except (ValueError, TypeError):
            raise SchemaError(f"{prefix}: completed_on: expected ISO date") from None
        if completed > cutoff:
            raise SchemaError(f"{prefix}: completed_on: future date relative to as_of")
    return records

def reasons(record):
    result = []
    if record["status"] == "failed":
        result.append("failed")
    if record["cost_pence"] > record["budget_pence"]:
        result.append("over_budget")
    if record["duration_minutes"] > record["planned_minutes"]:
        result.append("over_duration")
    return result

def analyze(records, as_of):
    validate(records, as_of)
    ordered = sorted(records, key=lambda r: r["id"])
    postmortems = []
    for r in ordered:
        triggers = reasons(r)
        if triggers:
            postmortems.append({**r, "triggers": triggers,
                "cause": "Not measured. No cause inferred.",
                "lesson": r["lesson"] or "Not supplied by operator.",
                "action": r["action"] or "Hand-check this mission and record an action."})
    return {"as_of": as_of, "totals": {"missions": len(records),
        "significant": len(postmortems), "synthetic": sum(r["synthetic"] for r in records),
        "real_operator_entered": sum(not r["synthetic"] for r in records),
        "cost_pence": sum(r["cost_pence"] for r in records),
        "duration_minutes": sum(r["duration_minutes"] for r in records),
        **{key: sum(key in reasons(r) for r in records) for key in ("failed", "over_budget", "over_duration")}},
        "postmortems": postmortems,
        "savings": "Unmeasured: no measured baseline supplied; no time or money saved claimed."}
