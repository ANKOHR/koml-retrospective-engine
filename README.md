# KOML Retrospective Engine

`kre` produces factual postmortems for significant completed missions. A mission is significant if it failed, its recorded cost exceeds its budget, or its recorded duration exceeds its plan. Equality is not a breach. Multiple triggers create one postmortem. Lessons and actions come from the operator; causes are never inferred.

## Quickstart

Python 3.10 or later, CPU only. No runtime dependencies, network calls, model calls or GPU packages.

```powershell
python -m pip install --no-build-isolation --no-deps -e .
kre fixtures --out demo
kre run --input demo
kre report --format md
python -m pytest -q
```

If your Python Scripts directory is absent from PATH, replace `kre` with `python -m koml_retrospective_engine.cli`. Installation uses locally available setuptools; no downloads are needed. For the smallest example run `kre run --input examples/tiny`. These five manually specified synthetic records produce three postmortems.

## Input format

An input directory contains exactly one workflow input, `missions.json`. Other files are metadata and are not ingested. JSON must be UTF-8. CSV and YAML are not supported. The root has `synthetic` (boolean), `as_of` (ISO date), and `records` (array). Root `synthetic` is true when all nonempty records are synthetic, false for real or mixed inputs. Each record contains all of these fields and no others:

| Field | Rule |
| --- | --- |
| id | Unique nonempty string |
| synthetic | Boolean; true for fixtures, false for Henry's hand-entered real data |
| completed_on | ISO date no later than explicit as_of |
| status | succeeded or failed |
| cost_pence, budget_pence | Nonnegative integer GBP pence |
| duration_minutes, planned_minutes | Nonnegative integer minutes |
| summary, lesson, action | Operator-supplied strings; empty lesson/action gets an explicit fallback |

Numbers are bounded at 1,000,000,000,000; booleans and floats are rejected as numbers. Strings are bounded at 100,000 characters. Unicode and Windows paths are preserved. Em dash characters are rejected in text to honor the output constraint. Dates use the supplied cutoff, never the wall clock, so reruns remain deterministic. Costs are input observations, not independently audited transactions. Counts and costs include all missions, including those without postmortems.

See `examples/tiny/missions.json` for a complete example. Henry may replace the synthetic records with his own observations and set their provenance flags to false. Keep real trial data outside the tracked repo. Provenance declarations are trusted and not independently verified.

## Subcommands

- `kre fixtures --out demo`: generate 200 labelled synthetic records and hand-computed expectations.
- `kre run --input demo --state .kre/results.json`: validate, compute and atomically store results. Default state is relative to the current directory; latest successful run replaces it.
- `kre report --format md`: print stored results. `kre report --format json --out report.json` writes atomically. Reports do not rerun input ingestion.
- `kre validate --input demo`: check schema, provenance consistency and adversarial values without writing state.
- `kre triage --input demo`: print significant missions, factual triggers, totals and provenance without writing state.

Every subcommand supplies `--help` with an example. JSON report keys are sorted; missions are sorted by ID. No randomness is used, so no seed is applicable. Identical inputs produce identical UTF-8 reports and state bytes.

## Architecture

```text
missions.json -> CLI parse and validate -> pure core analyze
                                           -> totals + factual postmortems
                                           -> atomic local state
local state -> report renderer -> Markdown or JSON + provenance banner
fixture generator -> missions.json + labelled expectations.json
```

The core has no I/O. The CLI is responsible for file handling and named errors. Expectations are never consumed by the workflow.

## Honesty boundary and fixture policy

This tool computes only from explicit inputs. All synthetic figures are labelled synthetic in each record, in root objects, in expectations and in report banners. JSON cannot carry header comments; its `synthetic: true` field is the machine-readable label. Fixture Markdown carries a synthetic header comment. Mixed reports enumerate both synthetic and declared real input counts. Synthetic performance and accuracy evidence does not establish real-world accuracy or savings.

No illustrative or hypothetical savings are presented as measured. Without a measured baseline the report explicitly states savings are unmeasured and claims none. This version does not implement baseline comparisons. No root cause, prediction, revenue, or time saved is invented. Operator statements in postmortems are labelled operator supplied. Default actions request a hand-check and are suggestions, not measured findings.

## Failure rules

An empty directory renders zeros with a fixed as_of date of 1970-01-01 (sentinel, not a mission date). A nonexistent directory raises MissingInput with a usage hint. A nonempty directory without missions.json also fails. Invalid JSON produces ParseError naming the file and parser line. SchemaError names the file, offending field and record index; line 1 is explicitly marked semantic validation, not a guessed source location. Invalid values and duplicate IDs reject the entire run; nothing is silently dropped. Failed runs preserve previous state. Report failures produce WriteError and temporary files are cleaned up. Exit code 2 means failure; no traceback is emitted for expected input or write errors.

## Acceptance evidence

The deterministic fixture has 200 missions: 20 failures, 20 separate budget breaches, 20 separate duration breaches, and 140 insignificant missions. Expected significant IDs are mission-000 through mission-059. Hand arithmetic: cost = 20*50 + 20*150 + 160*100 = 20,000 pence; duration = 180*60 + 20*180 = 14,400 minutes. Expected totals are independently specified in fixtures.py and expectations.json. Tests check every reported total, exact significant IDs, no false positives, and changed output when a planted record is corrupted. `EVIDENCE.json` records local timing; it is synthetic-fixture evidence, not real usage evidence.

## Two-week improvement hook and verdict

After two weeks of real use, record the number of actual runs and hand-check a sample of mission classifications, triggers and copied facts. Measure error rate as incorrect checked missions / total checked missions. Record sample IDs, numerator, denominator, dates and method privately. If no missions are checked, accuracy is unmeasured. If error exceeds 10 percent, fix the single largest observed cause and recheck; if the tool is unused, record the finding and kill it.

The operational verdict is pending the real evidence window. Do not invent a verdict from synthetic results. At the end record the reason in VERDICT.md: expand for daily use or revenue; integrate for heavy sibling overlap; commercialise if a buyer would pay as-is; maintain as portfolio evidence otherwise; kill for no use or unmet acceptance criteria. Local acceptance is demonstrated; real utility remains unmeasured.
