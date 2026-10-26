import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest
from health_monitor.analyzer import (
    analyze_metrics, format_alert_message, STATUS_HEALTHY, STATUS_WARNING
)

THR = {"cpu_percent": 80.0, "memory_percent": 80.0, "disk_percent": 80.0}


def metrics(cpu=50.0, mem=50.0, disk=50.0, path="/"):
    return {
        "cpu":    {"percent": cpu},
        "memory": {"percent": mem,  "total_gb": 16.0,
                   "used_gb": round(16*mem/100, 2), "available_gb": round(16*(100-mem)/100, 2)},
        "disk":   {"path": path, "percent": disk, "total_gb": 500.0,
                   "used_gb": round(500*disk/100, 2), "free_gb": round(500*(100-disk)/100, 2)},
        "uptime": {"uptime_human": "1d", "uptime_seconds": 86400},
        "processes": [],
    }


# --- CPU ---
def test_cpu_below_threshold_no_alert():
    assert [a for a in analyze_metrics(metrics(cpu=79.9), THR)["alerts"]
            if a["metric"] == "CPU utilization"] == []

def test_cpu_at_threshold_no_alert():
    assert [a for a in analyze_metrics(metrics(cpu=80.0), THR)["alerts"]
            if a["metric"] == "CPU utilization"] == []

def test_cpu_above_threshold_warning():
    alerts = [a for a in analyze_metrics(metrics(cpu=87.0), THR)["alerts"]
              if a["metric"] == "CPU utilization"]
    assert len(alerts) == 1
    assert alerts[0]["severity"] == "WARNING"
    assert alerts[0]["observed_value"] == 87.0
    assert alerts[0]["threshold"] == 80.0

def test_cpu_alert_has_suggestion():
    alerts = analyze_metrics(metrics(cpu=95.0), THR)["alerts"]
    assert alerts[0]["suggestion"] != ""

def test_cpu_exceeded_status_is_warning():
    assert analyze_metrics(metrics(cpu=90.0), THR)["status"] == STATUS_WARNING


# --- Memory ---
def test_memory_below_threshold_no_alert():
    assert [a for a in analyze_metrics(metrics(mem=70.0), THR)["alerts"]
            if a["metric"] == "Memory utilization"] == []

def test_memory_above_threshold_warning():
    alerts = [a for a in analyze_metrics(metrics(mem=92.0), THR)["alerts"]
              if a["metric"] == "Memory utilization"]
    assert len(alerts) == 1 and alerts[0]["severity"] == "WARNING"

def test_memory_alert_has_suggestion():
    alerts = [a for a in analyze_metrics(metrics(mem=85.0), THR)["alerts"]
              if a["metric"] == "Memory utilization"]
    assert alerts[0]["suggestion"] != ""


# --- Disk ---
def test_disk_below_threshold_no_alert():
    assert [a for a in analyze_metrics(metrics(disk=75.0), THR)["alerts"]
            if a["metric"] == "Disk utilization"] == []

def test_disk_above_threshold_warning():
    alerts = [a for a in analyze_metrics(metrics(disk=91.0), THR)["alerts"]
              if a["metric"] == "Disk utilization"]
    assert len(alerts) == 1 and alerts[0]["observed_value"] == 91.0

def test_disk_alert_contains_path():
    alerts = [a for a in analyze_metrics(metrics(disk=95.0, path="/data"), THR)["alerts"]
              if a["metric"] == "Disk utilization"]
    assert "/data" in alerts[0]["explanation"]


# --- Multiple / Healthy ---
def test_all_exceeded_three_alerts():
    assert len(analyze_metrics(metrics(cpu=95, mem=95, disk=95), THR)["alerts"]) == 3

def test_multiple_exceeded_status_warning():
    assert analyze_metrics(metrics(cpu=85, mem=90, disk=85), THR)["status"] == STATUS_WARNING

def test_summary_mentions_exceeded_metrics():
    r = analyze_metrics(metrics(cpu=85, mem=85), THR)
    assert "CPU utilization" in r["summary"]
    assert "Memory utilization" in r["summary"]

def test_all_healthy():
    r = analyze_metrics(metrics(cpu=40, mem=40, disk=40), THR)
    assert r["status"] == STATUS_HEALTHY and r["alerts"] == []

def test_healthy_summary_text():
    r = analyze_metrics(metrics(cpu=10, mem=20, disk=30), THR)
    assert "no configured resource thresholds" in r["summary"].lower()


# --- Custom thresholds ---
def test_custom_low_cpu_threshold_triggers_alert():
    r = analyze_metrics(metrics(cpu=15), {**THR, "cpu_percent": 10.0})
    assert len([a for a in r["alerts"] if a["metric"] == "CPU utilization"]) == 1

def test_high_threshold_suppresses_alert():
    r = analyze_metrics(metrics(cpu=85), {**THR, "cpu_percent": 99.0})
    assert [a for a in r["alerts"] if a["metric"] == "CPU utilization"] == []


# --- format_alert_message ---
_ALERT = {"severity": "WARNING", "metric": "CPU utilization",
          "observed_value": 87.0, "threshold": 80.0,
          "explanation": "High CPU.", "suggestion": "Run top."}

def test_format_includes_severity():
    assert "[WARNING]" in format_alert_message(_ALERT)

def test_format_includes_observed_value():
    assert "87.0%" in format_alert_message(_ALERT)

def test_format_includes_threshold():
    a = {**_ALERT, "metric": "Memory utilization", "observed_value": 92.0}
    assert "80.0%" in format_alert_message(a)
