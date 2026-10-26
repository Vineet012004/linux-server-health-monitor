"""Format terminal output and save timestamped JSON reports."""

import json
import logging
import os
import platform
import socket
from datetime import datetime, timezone
from typing import Optional

from health_monitor.analyzer import format_alert_message

logger = logging.getLogger(__name__)

SEP  = "=" * 60
THIN = "-" * 60


def _hostname() -> str:
    try:    return socket.gethostname()
    except: return "unknown"  # noqa: E722


def _os_info() -> str:
    try:    return f"{platform.system()} {platform.release()} ({platform.version()})"
    except: return "unknown"  # noqa: E722


def print_report(metrics: dict, analysis: dict) -> None:
    cpu   = metrics.get("cpu", {})
    mem   = metrics.get("memory", {})
    disk  = metrics.get("disk", {})
    up    = metrics.get("uptime", {})
    procs = metrics.get("processes", [])

    print(f"\n{SEP}")
    print(f" LINUX SERVER HEALTH MONITOR")
    print(f" Generated : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f" Hostname  : {_hostname()}")
    print(f" OS        : {_os_info()}")
    print(SEP)

    print(f"\nCPU\n  Utilization : {cpu.get('percent', 'N/A'):.1f}%")

    print(f"\nMEMORY")
    print(f"  Utilization : {mem.get('percent', 'N/A'):.1f}%")
    print(f"  Total       : {mem.get('total_gb', 'N/A')} GB")
    print(f"  Used        : {mem.get('used_gb', 'N/A')} GB")
    print(f"  Available   : {mem.get('available_gb', 'N/A')} GB")

    print(f"\nDISK")
    print(f"  Path        : {disk.get('path', 'N/A')}")
    print(f"  Utilization : {disk.get('percent', 'N/A'):.1f}%")
    print(f"  Total       : {disk.get('total_gb', 'N/A')} GB")
    print(f"  Used        : {disk.get('used_gb', 'N/A')} GB")
    print(f"  Free        : {disk.get('free_gb', 'N/A')} GB")

    print(f"\nUPTIME\n  Running for : {up.get('uptime_human', 'N/A')}")

    print(f"\nTOP PROCESSES (by memory %)")
    if procs:
        print(f"  {'PID':<8} {'NAME':<25} {'CPU %':<10} {'MEM %'}")
        print(f"  {THIN}")
        for p in procs:
            cpu_s = f"{p['cpu_percent']:.2f}" if p["cpu_percent"] is not None else "N/A"
            print(f"  {p['pid']:<8} {p['name'][:24]:<25} {cpu_s:<10} {p['memory_percent']:.2f}")
    else:
        print("  No process information available.")

    alerts = analysis.get("alerts", [])
    print(f"\n{THIN}\nALERTS\n{THIN}")
    if alerts:
        for a in alerts:
            print(f"  {format_alert_message(a)}")
    else:
        print("  No configured resource thresholds were exceeded during the check.")

    print(f"\n{SEP}")
    print(f" OVERALL STATUS: {analysis.get('status', 'UNKNOWN')}")
    print(f" {analysis.get('summary', '')}")
    print(f"{SEP}\n")


def build_report(metrics: dict, analysis: dict) -> dict:
    return {
        "timestamp":      datetime.now(timezone.utc).isoformat(),
        "hostname":       _hostname(),
        "os_info":        _os_info(),
        "cpu":            metrics.get("cpu"),
        "memory":         metrics.get("memory"),
        "disk":           metrics.get("disk"),
        "uptime":         metrics.get("uptime"),
        "top_processes":  metrics.get("processes"),
        "alerts":         analysis.get("alerts"),
        "overall_status": analysis.get("status"),
        "summary":        analysis.get("summary"),
    }


def save_report(report: dict, output_dir: str) -> Optional[str]:
    try:
        os.makedirs(output_dir, exist_ok=True)
    except OSError as e:
        logger.error("Cannot create output dir '%s': %s", output_dir, e)
        print(f"[ERROR] Cannot create output directory '{output_dir}': {e}")
        return None

    ts       = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join(output_dir, f"health_report_{ts}.json")
    if os.path.exists(filepath):
        filepath = filepath.replace(".json", "_1.json")

    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        logger.info("Report saved to '%s'.", filepath)
        print(f"[INFO] Report saved: {filepath}")
        return filepath
    except OSError as e:
        logger.error("Failed to write report '%s': %s", filepath, e)
        print(f"[ERROR] Failed to write report '{filepath}': {e}")
        return None
