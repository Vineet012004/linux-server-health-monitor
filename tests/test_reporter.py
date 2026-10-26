import json, os, sys, stat, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest
from health_monitor.reporter import build_report, save_report
from health_monitor.analyzer import STATUS_HEALTHY, STATUS_WARNING

REQUIRED_FIELDS = {
    "timestamp", "hostname", "os_info", "cpu", "memory", "disk",
    "uptime", "top_processes", "alerts", "overall_status", "summary",
}


def sample_metrics():
    return {
        "cpu":    {"percent": 45.0},
        "memory": {"percent": 60.0, "total_gb": 16.0, "used_gb": 9.6, "available_gb": 6.4},
        "disk":   {"path": "/", "percent": 55.0, "total_gb": 500.0, "used_gb": 275.0, "free_gb": 225.0},
        "uptime": {"uptime_human": "5h 30m", "uptime_seconds": 19800},
        "processes": [{"pid": 1, "name": "python", "cpu_percent": 1.0, "memory_percent": 1.0}],
    }


def sample_analysis(status=STATUS_HEALTHY, alerts=None):
    return {"alerts": alerts or [], "status": status,
            "summary": "No configured resource thresholds were exceeded during the check."}


# --- build_report ---
def test_build_returns_dict():
    assert isinstance(build_report(sample_metrics(), sample_analysis()), dict)

def test_build_contains_required_fields():
    missing = REQUIRED_FIELDS - build_report(sample_metrics(), sample_analysis()).keys()
    assert missing == set()

def test_build_timestamp_iso_format():
    from datetime import datetime
    ts = build_report(sample_metrics(), sample_analysis())["timestamp"]
    assert datetime.fromisoformat(ts) is not None

def test_build_status_healthy():
    assert build_report(sample_metrics(), sample_analysis(STATUS_HEALTHY))["overall_status"] == STATUS_HEALTHY

def test_build_status_warning():
    a = [{"severity": "WARNING", "metric": "CPU utilization",
          "observed_value": 90.0, "threshold": 80.0, "explanation": "X", "suggestion": "Y"}]
    assert build_report(sample_metrics(), sample_analysis(STATUS_WARNING, a))["overall_status"] == STATUS_WARNING

def test_build_alerts_preserved():
    a = [{"severity": "WARNING", "metric": "Disk utilization",
          "observed_value": 91.0, "threshold": 80.0, "explanation": "X", "suggestion": "Y"}]
    r = build_report(sample_metrics(), sample_analysis(STATUS_WARNING, a))
    assert len(r["alerts"]) == 1 and r["alerts"][0]["metric"] == "Disk utilization"

def test_build_empty_metrics_no_raise():
    assert "overall_status" in build_report({}, sample_analysis())

def test_build_hostname_is_nonempty_string():
    h = build_report(sample_metrics(), sample_analysis())["hostname"]
    assert isinstance(h, str) and h != ""


# --- save_report ---
def test_save_creates_file(tmp_path):
    p = save_report(build_report(sample_metrics(), sample_analysis()), str(tmp_path / "r"))
    assert p is not None and os.path.isfile(p)

def test_save_writes_valid_json(tmp_path):
    p = save_report(build_report(sample_metrics(), sample_analysis()), str(tmp_path / "r"))
    assert isinstance(json.load(open(p)), dict)

def test_saved_json_has_required_fields(tmp_path):
    p = save_report(build_report(sample_metrics(), sample_analysis()), str(tmp_path / "r"))
    missing = REQUIRED_FIELDS - json.load(open(p)).keys()
    assert missing == set()

def test_filename_has_timestamp_prefix(tmp_path):
    p = save_report(build_report(sample_metrics(), sample_analysis()), str(tmp_path / "r"))
    assert os.path.basename(p).startswith("health_report_") and p.endswith(".json")

def test_save_creates_missing_directory(tmp_path):
    d = str(tmp_path / "a" / "b" / "c")
    assert not os.path.exists(d)
    save_report(build_report(sample_metrics(), sample_analysis()), d)
    assert os.path.isdir(d)

def test_save_returns_none_on_unwritable_dir(tmp_path):
    import platform
    if platform.system() == "Windows":
        pytest.skip("chmod not enforced on Windows")
    d = str(tmp_path / "locked")
    os.makedirs(d)
    os.chmod(d, stat.S_IRUSR | stat.S_IXUSR)
    try:
        assert save_report(build_report(sample_metrics(), sample_analysis()), d) is None
    finally:
        os.chmod(d, stat.S_IRWXU)

def test_successive_saves_produce_different_files(tmp_path):
    d = str(tmp_path / "r")
    r = build_report(sample_metrics(), sample_analysis())
    p1 = save_report(r, d)
    time.sleep(1.1)
    p2 = save_report(r, d)
    assert p1 != p2
