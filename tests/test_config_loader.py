import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest
from health_monitor.config_loader import ConfigError, load_config


def write(tmp_path, data):
    p = str(tmp_path / "config.json")
    with open(p, "w") as f:
        json.dump(data, f)
    return p


VALID = {"thresholds": {"cpu_percent": 80, "memory_percent": 80, "disk_percent": 80}}


# --- Valid config ---
def test_returns_dict(tmp_path):
    assert isinstance(load_config(write(tmp_path, VALID)), dict)

def test_contains_thresholds(tmp_path):
    assert "thresholds" in load_config(write(tmp_path, VALID))

def test_values_are_floats(tmp_path):
    t = load_config(write(tmp_path, VALID))["thresholds"]
    assert all(isinstance(t[k], float) for k in t)

def test_values_match_input(tmp_path):
    d = {"thresholds": {"cpu_percent": 70, "memory_percent": 75, "disk_percent": 85}}
    t = load_config(write(tmp_path, d))["thresholds"]
    assert t["cpu_percent"] == 70.0 and t["memory_percent"] == 75.0 and t["disk_percent"] == 85.0

def test_float_values_accepted(tmp_path):
    d = {"thresholds": {"cpu_percent": 79.5, "memory_percent": 80.0, "disk_percent": 90.0}}
    assert load_config(write(tmp_path, d))["thresholds"]["cpu_percent"] == 79.5

def test_boundary_zero_accepted(tmp_path):
    d = {"thresholds": {"cpu_percent": 0, "memory_percent": 0, "disk_percent": 0}}
    assert load_config(write(tmp_path, d))["thresholds"]["cpu_percent"] == 0.0

def test_boundary_100_accepted(tmp_path):
    d = {"thresholds": {"cpu_percent": 100, "memory_percent": 100, "disk_percent": 100}}
    assert load_config(write(tmp_path, d))["thresholds"]["cpu_percent"] == 100.0


# --- Missing file ---
def test_missing_file_raises(tmp_path):
    with pytest.raises(ConfigError, match="not found"):
        load_config(str(tmp_path / "nope.json"))

def test_missing_file_error_includes_path(tmp_path):
    p = str(tmp_path / "missing.json")
    with pytest.raises(ConfigError, match="missing.json"):
        load_config(p)


# --- Bad JSON ---
def test_invalid_json_raises(tmp_path):
    p = str(tmp_path / "bad.json")
    open(p, "w").write("{ not json }")
    with pytest.raises(ConfigError, match="(?i)invalid json"):
        load_config(p)

def test_empty_file_raises(tmp_path):
    p = str(tmp_path / "empty.json")
    open(p, "w").write("")
    with pytest.raises(ConfigError):
        load_config(p)

def test_array_at_root_raises(tmp_path):
    p = str(tmp_path / "arr.json")
    json.dump([1, 2], open(p, "w"))
    with pytest.raises(ConfigError):
        load_config(p)


# --- Missing / invalid threshold keys ---
def test_missing_thresholds_key(tmp_path):
    with pytest.raises(ConfigError, match="thresholds"):
        load_config(write(tmp_path, {"other": 1}))

def test_missing_cpu_key(tmp_path):
    with pytest.raises(ConfigError, match="cpu_percent"):
        load_config(write(tmp_path, {"thresholds": {"memory_percent": 80, "disk_percent": 80}}))

def test_missing_memory_key(tmp_path):
    with pytest.raises(ConfigError, match="memory_percent"):
        load_config(write(tmp_path, {"thresholds": {"cpu_percent": 80, "disk_percent": 80}}))

def test_missing_disk_key(tmp_path):
    with pytest.raises(ConfigError, match="disk_percent"):
        load_config(write(tmp_path, {"thresholds": {"cpu_percent": 80, "memory_percent": 80}}))

def test_thresholds_not_dict(tmp_path):
    with pytest.raises(ConfigError):
        load_config(write(tmp_path, {"thresholds": "bad"}))


# --- Out-of-range values ---
def test_negative_cpu_raises(tmp_path):
    with pytest.raises(ConfigError, match="cpu_percent"):
        load_config(write(tmp_path, {"thresholds": {"cpu_percent": -1, "memory_percent": 80, "disk_percent": 80}}))

def test_cpu_above_100_raises(tmp_path):
    with pytest.raises(ConfigError, match="cpu_percent"):
        load_config(write(tmp_path, {"thresholds": {"cpu_percent": 101, "memory_percent": 80, "disk_percent": 80}}))

def test_string_value_raises(tmp_path):
    with pytest.raises(ConfigError):
        load_config(write(tmp_path, {"thresholds": {"cpu_percent": "high", "memory_percent": 80, "disk_percent": 80}}))

def test_null_value_raises(tmp_path):
    with pytest.raises(ConfigError):
        load_config(write(tmp_path, {"thresholds": {"cpu_percent": None, "memory_percent": 80, "disk_percent": 80}}))
