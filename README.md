# Linux Server Health Monitor

A Python CLI tool that collects CPU, memory, disk, and process metrics, checks them against configurable thresholds, prints a terminal summary, and saves a timestamped JSON report.

> Runs as a single on-demand check — not a background daemon or real-time dashboard.

---

## Features

- CPU, memory, disk utilization with absolute figures
- System uptime and top-5 processes by memory
- Configurable thresholds via `config.json` (default 80%)
- `[WARNING]` alerts with explanations and investigation suggestions
- Timestamped JSON reports saved to `reports/`
- Graceful error handling (missing files, denied processes, bad config)
- pytest test suite — no real system state needed

## Tech Stack

Python 3.10+ · psutil · argparse · logging · json · pytest

---

## Project Structure

```
linux-server-health-monitor/
├── monitor.py               # CLI entry point
├── config.json              # Threshold configuration
├── requirements.txt
├── src/health_monitor/
│   ├── config_loader.py     # Load & validate config
│   ├── collector.py         # Collect metrics via psutil
│   ├── analyzer.py          # Threshold checks & alerts
│   └── reporter.py          # Terminal output & JSON report
├── tests/
│   ├── test_analyzer.py
│   ├── test_config_loader.py
│   └── test_reporter.py
└── reports/                 # Saved JSON reports
```

---

## Installation (Ubuntu / WSL 2)

```bash
git clone https://github.com/YOUR_USERNAME/linux-server-health-monitor.git
cd linux-server-health-monitor

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt
```

---

## Configuration

Edit `config.json` — all values are percentages (0–100):

```json
{
  "thresholds": {
    "cpu_percent": 80,
    "memory_percent": 80,
    "disk_percent": 80
  }
}
```

The app validates on startup and exits with a clear error for missing keys, non-numeric values, or out-of-range numbers.

---

## Usage

| Command                                          | Description            |
| ------------------------------------------------ | ---------------------- |
| `python monitor.py`                              | Run check, save report |
| `python monitor.py --config path/to/config.json` | Custom config          |
| `python monitor.py --output-dir /tmp/reports`    | Custom report dir      |
| `python monitor.py --no-report`                  | Run check, skip saving |
| `python monitor.py --verbose`                    | Debug logging          |
| `python monitor.py --version`                    | Print version          |

---

## Example Output

```
============================================================
 LINUX SERVER HEALTH MONITOR
 Generated : 2026-10-27 12:00:00
 Hostname  : web-server-01
 OS        : Linux 5.15.0-91-generic
============================================================

CPU
  Utilization : 23.4%

MEMORY
  Utilization : 89.0%
  Total       : 7.34 GB
  Used        : 6.54 GB
  Available   : 0.81 GB

DISK
  Path        : /
  Utilization : 48.7%
  Total       : 233.47 GB
  Used        : 113.7 GB
  Free        : 119.77 GB

UPTIME
  Running for : 3d 14h 22m 5s

TOP PROCESSES (by memory %)
  PID      NAME                      CPU %      MEM %
  ------------------------------------------------------------
  3320     MemCompression            0.00       10.45
  1842     postgres                  0.20        4.31

------------------------------------------------------------
ALERTS
------------------------------------------------------------
  [WARNING] Memory utilization is 89.0%, exceeding the configured threshold of
  80.0%. High memory may indicate a leak or undersized server.
  Suggested investigation: Run 'free -h' and 'ps aux --sort=-%mem | head -20'.

============================================================
 OVERALL STATUS: WARNING
 1 threshold(s) exceeded: Memory utilization.
============================================================

[INFO] Report saved: reports/health_report_20261027_120000.json
```

_Values shown are illustrative._

---

## Example JSON Report

```json
{
  "timestamp": "2026-10-27T12:00:00+00:00",
  "hostname": "web-server-01",
  "os_info": "Linux 5.15.0-91-generic",
  "cpu": { "percent": 23.4 },
  "memory": {
    "percent": 89.0,
    "total_gb": 7.34,
    "used_gb": 6.54,
    "available_gb": 0.81
  },
  "disk": {
    "path": "/",
    "percent": 48.7,
    "total_gb": 233.47,
    "used_gb": 113.7,
    "free_gb": 119.77
  },
  "uptime": { "uptime_seconds": 296525, "uptime_human": "3d 14h 22m 5s" },
  "top_processes": [
    {
      "pid": 3320,
      "name": "MemCompression",
      "cpu_percent": 0.0,
      "memory_percent": 10.45
    }
  ],
  "alerts": [
    {
      "severity": "WARNING",
      "metric": "Memory utilization",
      "observed_value": 89.0,
      "threshold": 80.0,
      "explanation": "High memory may indicate a leak or undersized server.",
      "suggestion": "Run 'free -h' and 'ps aux --sort=-%mem | head -20'."
    }
  ],
  "overall_status": "WARNING",
  "summary": "1 threshold(s) exceeded: Memory utilization."
}
```

_Values shown are illustrative._

---

## Running Tests

```bash
source venv/bin/activate
python -m pytest tests/ -v
```

All tests use synthetic data — no real CPU/memory/disk state is read.

---

## Troubleshooting

**`ModuleNotFoundError: No module named 'psutil'`** → `pip install -r requirements.txt` inside the active venv.

**`ModuleNotFoundError: No module named 'health_monitor'`** → Run from the project root, not from inside `src/`.

**`ConfigError: Config file not found`** → Ensure `config.json` is in the project root or pass `--config`.

---

## Useful Linux Commands

```bash
top                              # live CPU/memory by process
free -h                          # memory and swap
df -h                            # disk usage per filesystem
du -sh /*                        # disk usage by top-level dir
ps aux --sort=-%cpu | head -20   # top CPU processes
ps aux --sort=-%mem | head -20   # top memory processes
uptime                           # uptime and load averages
systemctl status <service>       # service status
journalctl -u <service> -n 50   # last 50 log lines for a service
```

---

## Limitations

- Monitors only the root filesystem (`/`)
- Single on-demand check — add cron for scheduling (see below)
- No network, swap, or per-service monitoring

## Optional: Schedule with cron

```bash
crontab -e
# Add:
*/15 * * * * /path/to/venv/bin/python /path/to/monitor.py >> /path/to/cron.log 2>&1
```

---

## GitHub

```bash
git init
git add .
git commit -m "Initial commit: Linux Server Health Monitor v1.0.0"
git remote add origin https://github.com/YOUR_USERNAME/linux-server-health-monitor.git
git branch -M main
git push -u origin main
```

**Repo name:** `linux-server-health-monitor`  
**Description:** `Python-based Linux system health monitoring tool — CPU, memory, disk, process inspection, threshold alerts, JSON reporting.`
