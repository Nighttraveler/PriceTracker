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
    parser.add_argument("--day", default="lunes",
                        choices=list(DIAS_ES.keys()),
                        help="Día de la semana para el reporte")
    parser.add_argument("--hour", type=int, default=6,
                        help="Hora (0-23) para correr tareas")
    parser.add_argument("--scrape-interval", type=int, default=24,
                        help="Intervalo en horas entre scrapings")
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
    dia_en = DIAS_ES[args.day]

    # Scraping cada N horas
    schedule.every(args.scrape_interval).hours.do(run_scraping)

    # Reporte semanal el día y hora configurados
    getattr(schedule.every(), dia_en).at(hora_str).do(run_reporte)

    log.info(f"Scheduler iniciado — scraping cada {args.scrape_interval}h, "
             f"reporte los {args.day} a las {hora_str}")

    # Ejecutar una vez al arrancar
    run_scraping()

    while True:
        schedule.run_pending()
        time.sleep(60)
