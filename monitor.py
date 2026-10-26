"""
Linux Server Health Monitor — CLI entry point.

  python monitor.py                        # run check, save report
  python monitor.py --config config.json   # custom config
  python monitor.py --output-dir reports/  # custom report dir
  python monitor.py --no-report            # skip saving
  python monitor.py --verbose              # debug logging
  python monitor.py --version / --help
"""

import argparse
import logging
import os
import sys

_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_ROOT, "src"))

from health_monitor import __version__
from health_monitor.config_loader import ConfigError, load_config
from health_monitor.collector import collect_all_metrics
from health_monitor.analyzer import analyze_metrics, STATUS_ERROR
from health_monitor.reporter import print_report, build_report, save_report


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="monitor.py",
        description="Linux Server Health Monitor — collects CPU/memory/disk metrics, "
                    "evaluates thresholds, and saves a JSON report.",
    )
    p.add_argument("--version",    action="version", version=f"%(prog)s {__version__}")
    p.add_argument("--config",     default=os.path.join(_ROOT, "config.json"),
                   metavar="PATH", help="JSON config file (default: config.json)")
    p.add_argument("--output-dir", default=os.path.join(_ROOT, "reports"),
                   metavar="DIR",  help="Report output directory (default: reports/)")
    p.add_argument("--no-report",  action="store_true", help="Skip saving JSON report")
    p.add_argument("--verbose",    action="store_true", help="Enable debug logging")
    return p


def run(args: argparse.Namespace) -> int:
    try:
        config = load_config(args.config)
    except ConfigError as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        return 1

    try:
        metrics = collect_all_metrics()
    except Exception as e:
        print(f"[ERROR] Metric collection failed: {e}", file=sys.stderr)
        if not args.no_report:
            save_report(build_report({}, {"alerts": [], "status": STATUS_ERROR,
                                          "summary": f"Health check failed: {e}"}),
                        args.output_dir)
        return 1

    analysis = analyze_metrics(metrics, config["thresholds"])
    print_report(metrics, analysis)

    if not args.no_report:
        save_report(build_report(metrics, analysis), args.output_dir)

    return 0


def main() -> None:
    args = _parser().parse_args()
    logging.basicConfig(
        format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        level=logging.DEBUG if args.verbose else logging.INFO,
    )
    sys.exit(run(args))


if __name__ == "__main__":
    main()
