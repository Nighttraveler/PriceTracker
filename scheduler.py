#!/usr/bin/env python3
"""scheduler.py — Automatiza scraping periódico y generación de reportes."""

import argparse
import logging
import schedule
import time
from datetime import date
from pathlib import Path

log = logging.getLogger(__name__)

DIAS_ES = {
    "lunes": "monday", "martes": "tuesday", "miercoles": "wednesday",
    "jueves": "thursday", "viernes": "friday", "sabado": "saturday",
    "domingo": "sunday",
}


def run_scraping():
    log.info("▶ Iniciando scraping automático...")
    from tracker import run
    run("all")


def run_reporte():
    log.info("▶ Generando reporte semanal...")
    from db import Database
    from reporter import generar_reporte
    hoy = date.today().isoformat()
    output = f"data/reportes/reporte_{hoy}.html"
    Path("data/reportes").mkdir(parents=True, exist_ok=True)
    db = Database()
    generar_reporte(db, dias=7, output=output)
    log.info(f"Reporte guardado en {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Hermes Scheduler")
    parser.add_argument("--hour", type=int, default=7,
                        help="Hora (0-23) para el scraping (default: 7)")
    parser.add_argument("--report-day", default="lunes",
                        choices=list(DIAS_ES.keys()),
                        help="Día de la semana para el reporte semanal")
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

    # Scraping lunes, miércoles y viernes a la hora configurada
    schedule.every().monday.at(hora_str).do(run_scraping)
    schedule.every().wednesday.at(hora_str).do(run_scraping)
    schedule.every().friday.at(hora_str).do(run_scraping)

    # Reporte semanal
    dia_en = DIAS_ES[args.report_day]
    getattr(schedule.every(), dia_en).at(hora_str).do(run_reporte)

    log.info(f"Scheduler iniciado — scraping lun/mié/vie a las {hora_str}, "
             f"reporte los {args.report_day}")

    # Ejecutar una vez al arrancar
    #run_scraping()

    while True:
        schedule.run_pending()
        time.sleep(60)
