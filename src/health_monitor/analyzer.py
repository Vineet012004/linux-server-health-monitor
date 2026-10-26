"""Compare metrics against thresholds and produce alerts. No I/O or psutil calls —
pure dict-in / dict-out so this module is trivial to unit-test."""

import logging

logger = logging.getLogger(__name__)

STATUS_HEALTHY = "HEALTHY"
STATUS_WARNING = "WARNING"
STATUS_ERROR   = "ERROR"

_CHECKS = [
    (
        "cpu",    "percent", "cpu_percent",    "CPU utilization",
        "High CPU may indicate a runaway process or workload spike. "
        "This does not confirm a failure on its own.",
        "Run 'top' or 'ps aux --sort=-%cpu | head -20'.",
    ),
    (
        "memory", "percent", "memory_percent", "Memory utilization",
        "High memory may indicate a leak or undersized server. "
        "Check whether available memory is critically low.",
        "Run 'free -h' and 'ps aux --sort=-%mem | head -20'.",
    ),
]


def format_alert_message(alert: dict) -> str:
    return (
        f"[{alert['severity']}] {alert['metric']} is {alert['observed_value']:.1f}%, "
        f"exceeding the configured threshold of {alert['threshold']:.1f}%. "
        f"{alert['explanation']} "
        f"Suggested investigation: {alert['suggestion']}"
    )


def analyze_metrics(metrics: dict, thresholds: dict) -> dict:
    alerts = []

    for section, field, tkey, label, explanation, suggestion in _CHECKS:
        val = metrics.get(section, {}).get(field)
        thr = thresholds[tkey]
        if val is not None and val > thr:
            alerts.append({"severity": "WARNING", "metric": label,
                           "observed_value": val, "threshold": thr,
                           "explanation": explanation, "suggestion": suggestion})

    # Disk — needs path from metrics for the explanation
    disk = metrics.get("disk", {})
    disk_val = disk.get("percent")
    disk_thr = thresholds["disk_percent"]
    disk_path = disk.get("path", "/")
    if disk_val is not None and disk_val > disk_thr:
        alerts.append({
            "severity": "WARNING", "metric": "Disk utilization",
            "observed_value": disk_val, "threshold": disk_thr,
            "explanation": (f"Disk on '{disk_path}' is high. Exhausted disk can cause "
                            "services to fail when writing logs or data."),
            "suggestion": "Run 'df -h' and 'du -sh /*' to find large directories.",
        })

    if alerts:
        status  = STATUS_WARNING
        summary = (f"{len(alerts)} threshold(s) exceeded: "
                   + ", ".join(a["metric"] for a in alerts) + ".")
    else:
        status  = STATUS_HEALTHY
        summary = "No configured resource thresholds were exceeded during the check."

    logger.debug("Status: %s | Alerts: %d", status, len(alerts))
    return {"alerts": alerts, "status": status, "summary": summary}
