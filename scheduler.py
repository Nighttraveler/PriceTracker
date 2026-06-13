#!/usr/bin/env python3
"""scheduler.py — Automates periodic scraping and report generation."""

import argparse
import logging
import schedule
import time
from datetime import date
from pathlib import Path

log = logging.getLogger(__name__)

DAYS_MAP = {
    "lunes": "monday", "martes": "tuesday", "miercoles": "wednesday",
    "jueves": "thursday", "viernes": "friday", "sabado": "saturday",
    "domingo": "sunday",
}


def run_scraping():
    log.info("▶ Starting automatic scraping...")
    from tracker import run
    run("all")


def run_report():
    log.info("▶ Generating weekly report...")
    from db import Database
    from reporter import generate_report
    hoy = date.today().isoformat()
    output = f"data/reportes/reporte_{hoy}.html"
    Path("data/reportes").mkdir(parents=True, exist_ok=True)
    db = Database()
    generate_report(db, dias=7, output=output)
    log.info(f"Report saved to {output}")


def run_url_check():
    log.info("▶ Checking discontinued URLs...")
    from scripts.chequear_urls import main as check_urls
    check_urls([])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Hermes Scheduler")
    parser.add_argument("--hour", type=int, default=7,
                        help="Hour (0-23) for scraping runs (default: 7)")
    parser.add_argument("--report-day", default="lunes",
                        choices=list(DAYS_MAP.keys()),
                        help="Day of the week for the weekly report")
    parser.add_argument("--check-day", default="domingo",
                        choices=list(DAYS_MAP.keys()),
                        help="Day of the week for URL discontinuation check (default: domingo)")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler("logs/tracker.log"),
            logging.StreamHandler()
        ]
    )

    hora_str = f"{args.hour:02d}:00"

    # Scraping runs Monday, Wednesday, and Friday at the configured hour
    schedule.every().monday.at(hora_str).do(run_scraping)
    schedule.every().wednesday.at(hora_str).do(run_scraping)
    schedule.every().friday.at(hora_str).do(run_scraping)

    # Weekly report
    dia_en = DAYS_MAP[args.report_day]
    getattr(schedule.every(), dia_en).at(hora_str).do(run_report)

    # Weekly URL discontinuation check
    check_day_en = DAYS_MAP[args.check_day]
    getattr(schedule.every(), check_day_en).at(hora_str).do(run_url_check)

    log.info(
        f"Scheduler started — scraping Mon/Wed/Fri at {hora_str}, "
        f"report on {args.report_day}, "
        f"URL check on {args.check_day}"
    )

    # Uncomment to run once on startup:
    #run_scraping()

    while True:
        schedule.run_pending()
        time.sleep(60)
