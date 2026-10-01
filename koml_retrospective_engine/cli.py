"""Local-file CLI with named errors and atomic report writes."""
import argparse
import json
import os
from pathlib import Path
import sys
import tempfile
from .core import SchemaError, analyze
from .fixtures import generate
from .report import render, banner

class InputError(ValueError):
    pass

def load(path):
    directory = Path(path)
    if not directory.is_dir():
        raise InputError(f"MissingInput: {directory}; use kre fixtures --out demo or supply an input directory")
    source = directory / "missions.json"
    if not source.exists():
        if any(directory.iterdir()):
            raise InputError(f"MissingInput: {source}; expected missions.json")
        return analyze([], "1970-01-01")
    try:
        data = json.loads(source.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise InputError(f"ParseError: {source}: line {e.lineno}: {e.msg}") from None
    except UnicodeError:
        raise InputError(f"ParseError: {source}: line 1: invalid UTF-8") from None
    try:
        if not isinstance(data, dict) or set(data) != {"synthetic", "as_of", "records"}:
            raise SchemaError("root fields: expected synthetic, as_of, records")
        if type(data["synthetic"]) is not bool or not isinstance(data["records"], list):
            raise SchemaError("synthetic must be boolean; records must be array")
        if data["synthetic"] != all(r.get("synthetic") is True for r in data["records"] if isinstance(r, dict)) and data["records"]:
            raise SchemaError("synthetic: root must reflect whether all records are synthetic")
        return analyze(data["records"], data["as_of"])
    except SchemaError as e:
        raise InputError(f"SchemaError: {source}: line 1 (semantic validation): {e}") from None

def atomic_write(path, text):
    target = Path(path)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n", dir=target.parent, delete=False) as f:
            temporary = Path(f.name)
            f.write(text)
        os.replace(temporary, target)
    except OSError as e:
        raise InputError(f"WriteError: {target}: {e}") from None
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()

def main(argv=None):
    parser = argparse.ArgumentParser(description="Compute postmortems from explicit local mission inputs.")
    subs = parser.add_subparsers(dest="command", required=True)
    f = subs.add_parser("fixtures", help="Generate 200 labelled synthetic missions", epilog="Example: kre fixtures --out demo")
    f.add_argument("--out", required=True)
    for command, description in (("run", "Compute and persist mission postmortems"), ("validate", "Validate mission schema and values"),
                                 ("triage", "List significant mission IDs and factual triggers")):
        p = subs.add_parser(command, help=description, description=description, epilog=f"Example: kre {command} --input demo")
        p.add_argument("--input", required=True)
        if command == "run":
            p.add_argument("--state", default=".kre/results.json")
    p = subs.add_parser("report", help="Render stored results with provenance", epilog="Example: kre report --format md")
    p.add_argument("--format", choices=("md", "json"), default="md")
    p.add_argument("--state", default=".kre/results.json")
    p.add_argument("--out")
    args = parser.parse_args(argv)
    try:
        if args.command == "fixtures":
            generate(args.out)
            print("Generated 200 synthetic fixture missions.")
        elif args.command in ("run", "validate", "triage"):
            result = load(args.input)
            if args.command == "run":
                Path(args.state).parent.mkdir(parents=True, exist_ok=True)
                atomic_write(args.state, render(result, "json"))
                print(f"Computed {result['totals']['significant']} postmortems. " + banner(result))
            elif args.command == "validate":
                print(f"Valid: {result['totals']['missions']} missions; synthetic={result['totals']['synthetic']}; real operator-entered={result['totals']['real_operator_entered']}")
            else:
                print(render(result, "json"))
        else:
            try:
                result = json.loads(Path(args.state).read_text(encoding="utf-8"))
            except (OSError, ValueError) as e:
                raise InputError(f"StateError: {args.state}: {e}; run kre run --input <dir> first") from None
            output = render(result, args.format)
            if args.out:
                atomic_write(args.out, output)
            else:
                print(output, end="")
        return 0
    except (InputError, OSError, KeyError, TypeError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2

if __name__ == "__main__":
    sys.exit(main())
