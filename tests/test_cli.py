import json
import time
import pytest
from koml_retrospective_engine.cli import main
from koml_retrospective_engine.fixtures import generate

@pytest.fixture
def demo(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path); generate("demo"); return tmp_path

def test_run_completes_on_fixture(demo):
    start = time.perf_counter()
    assert main(["run", "--input", "demo"]) == 0
    assert main(["report", "--format", "md"]) == 0
    assert time.perf_counter()-start < 5

def test_cli_smoke_all_subcommands(demo):
    for args in (["fixtures", "--out", "other"], ["run", "--input", "demo"], ["validate", "--input", "demo"], ["triage", "--input", "demo"], ["report", "--format", "json"]):
        assert main(args) == 0
    for command in ("fixtures", "run", "validate", "triage", "report"):
        with pytest.raises(SystemExit) as e: main([command, "--help"])
        assert e.value.code == 0

def test_empty_input_renders_without_traceback(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path); (tmp_path/"empty").mkdir()
    assert main(["run", "--input", "empty"]) == 0
    assert main(["report"]) == 0
    assert "missions: 0" in capsys.readouterr().out

def test_malformed_input_named_error(tmp_path, capsys):
    (tmp_path/"missions.json").write_text('{\n broken')
    assert main(["validate", "--input", str(tmp_path)]) == 2
    err = capsys.readouterr().err
    assert "ParseError" in err and "missions.json: line 2" in err

def test_missing_input(tmp_path, capsys):
    assert main(["run", "--input", str(tmp_path/"missing")]) == 2
    assert "MissingInput" in capsys.readouterr().err

def test_schema_drift(demo, capsys):
    p = demo/"demo/missions.json"; data = json.loads(p.read_text()); data["records"][0]["extra"] = 1; p.write_text(json.dumps(data))
    assert main(["validate", "--input", "demo"]) == 2
    assert "extra" in capsys.readouterr().err

def test_report_write_failure_no_partial_files(demo, capsys):
    assert main(["run", "--input", "demo"]) == 0
    before = set(demo.iterdir())
    assert main(["report", "--out", "absent/report.md"]) == 2
    assert "WriteError" in capsys.readouterr().err
    assert set(demo.iterdir()) == before

def test_end_to_end_byte_identical(demo):
    assert main(["run", "--input", "demo"]) == 0
    a = (demo/".kre/results.json").read_bytes()
    assert main(["run", "--input", "demo"]) == 0
    assert a == (demo/".kre/results.json").read_bytes()
