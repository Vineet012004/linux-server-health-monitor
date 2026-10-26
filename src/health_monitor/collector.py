"""Collect system metrics via psutil. CPU is sampled over 1 second (interval=1)
so the first call returns a real value instead of 0.0. Inaccessible processes
are silently skipped — they never crash the application."""

import logging
import os
import sys
import time

import psutil

logger = logging.getLogger(__name__)


def _gb(b: int) -> float:
    return round(b / 1024 ** 3, 2)


def collect_cpu() -> dict:
    pct = psutil.cpu_percent(interval=1)
    return {"percent": pct}


def collect_memory() -> dict:
    m = psutil.virtual_memory()
    return {"percent": m.percent, "total_gb": _gb(m.total),
            "used_gb": _gb(m.used), "available_gb": _gb(m.available)}


def collect_disk(path: str = "/") -> dict:
    if not os.path.exists(path) and sys.platform == "win32":
        path = os.path.splitdrive(os.getcwd())[0] + "\\"
    u = psutil.disk_usage(path)
    return {"path": path, "percent": u.percent,
            "total_gb": _gb(u.total), "used_gb": _gb(u.used), "free_gb": _gb(u.free)}


def collect_uptime() -> dict:
    secs = int(time.time() - psutil.boot_time())
    d, r = divmod(secs, 86400)
    h, r = divmod(r, 3600)
    m, s = divmod(r, 60)
    parts = ([f"{d}d"] if d else []) + ([f"{h}h"] if h else []) + ([f"{m}m"] if m else []) + [f"{s}s"]
    return {"boot_timestamp": psutil.boot_time(), "uptime_seconds": secs, "uptime_human": " ".join(parts)}


def collect_top_processes(limit: int = 5) -> list:
    procs = []
    for p in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]):
        try:
            i = p.info
            mem = i.get("memory_percent")
            if mem is None:
                continue
            cpu = i.get("cpu_percent")
            procs.append({"pid": i["pid"], "name": i.get("name") or "unknown",
                          "cpu_percent": round(cpu, 2) if cpu is not None else None,
                          "memory_percent": round(mem, 2)})
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    procs.sort(key=lambda p: p["memory_percent"], reverse=True)
    return procs[:limit]


def collect_all_metrics(disk_path: str = "/") -> dict:
    return {
        "cpu": collect_cpu(),
        "memory": collect_memory(),
        "disk": collect_disk(disk_path),
        "uptime": collect_uptime(),
        "processes": collect_top_processes(),
    }
