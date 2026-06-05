#!/usr/bin/env python3
"""
Verifica las URLs almacenadas en variantes.url_producto y marca como
descatalogado=1 aquellas que devuelven 301, 404 o 410 (producto removido
del catálogo del supermercado).

Uso:
    DATABASE_URL=postgresql://... python scripts/chequear_urls.py
    DATABASE_URL=postgresql://... python scripts/chequear_urls.py --fuente anonima --limit 50 --dry-run
"""

import argparse
import logging
import sys
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse

import requests

sys.path.insert(0, ".")
from db import Database

log = logging.getLogger(__name__)

ESTADOS_DESCATALOGADO = {301, 404, 410}
TIMEOUT = 10
WORKERS = 5
DELAY_POR_DOMINIO = 0.5  # segundos entre requests al mismo host
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}


def chequear_url(url: str) -> int:
    """Devuelve el HTTP status code sin seguir redirects. 0 si hay error de red."""
    try:
        resp = requests.head(url, allow_redirects=False, timeout=TIMEOUT, headers=HEADERS)
        # Muchos sitios bloquean HEAD con 403/405 (WAF). En ese caso usar GET.
        if resp.status_code >= 400:
            resp = requests.get(url, allow_redirects=False, timeout=TIMEOUT, headers=HEADERS)
        return resp.status_code
    except requests.RequestException as e:
        log.debug(f"Error de red en {url}: {e}")
        return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description="Verifica URLs de variantes y marca descatalogadas")
    parser.add_argument("--fuente", help="Limitar a una fuente específica (ej: anonima)")
    parser.add_argument("--limit", type=int, help="Máximo de variantes a chequear")
    parser.add_argument("--dry-run", action="store_true", help="No actualizar DB, solo informar")
    parser.add_argument("--recheck", action="store_true",
                        help="Re-chequear variantes ya marcadas como descatalogadas")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    db = Database()

    where_clauses = ["v.url_producto IS NOT NULL", "v.url_producto != ''"]
    params = []

    if not args.recheck:
        where_clauses.append("v.descatalogado = 0")

    if args.fuente:
        where_clauses.append("f.nombre = ?")
        params.append(args.fuente)

    sql = f"""
        SELECT v.id, v.url_producto, v.nombre_original, f.nombre AS fuente
        FROM variantes v
        JOIN fuentes f ON v.fuente_id = f.id
        WHERE {' AND '.join(where_clauses)}
        ORDER BY v.id
    """
    if args.limit:
        sql += f" LIMIT {args.limit}"

    variantes = db._fetchall(sql, tuple(params))
    total = len(variantes)
    log.info(f"Chequeando {total} variante(s)...")

    # Agrupar por dominio para rate limiting
    por_dominio = defaultdict(list)
    for v in variantes:
        domain = urlparse(v["url_producto"]).netloc
        por_dominio[domain].append(dict(v))

    resultados = {}  # variante_id → (status_code, variante_dict)

    def chequear_dominio(variantes_dominio):
        for v in variantes_dominio:
            status = chequear_url(v["url_producto"])
            resultados[v["id"]] = (status, v)
            time.sleep(DELAY_POR_DOMINIO)

    with ThreadPoolExecutor(max_workers=WORKERS) as executor:
        futures = {
            executor.submit(chequear_dominio, vs): domain
            for domain, vs in por_dominio.items()
        }
        for future in as_completed(futures):
            future.result()

    marcados = 0
    errores_red = 0
    for variante_id, (status, v) in resultados.items():
        if status == 0:
            errores_red += 1
            log.debug(f"[ERROR RED] {v['fuente']} — {v['nombre_original']}")
        elif status in ESTADOS_DESCATALOGADO:
            log.info(f"[{status}] DESCATALOGADO: {v['fuente']} — {v['nombre_original']}")
            if not args.dry_run:
                db._execute(
                    "UPDATE variantes SET descatalogado = 1 WHERE id = ?",
                    (variante_id,),
                )
                db.commit()
            marcados += 1
        else:
            log.debug(f"[{status}] OK: {v['fuente']} — {v['nombre_original']}")

    modo = " (dry-run)" if args.dry_run else ""
    log.info(
        f"Resumen{modo}: {marcados}/{total} descatalogadas, "
        f"{errores_red} errores de red (no marcados)"
    )


if __name__ == "__main__":
    main()
