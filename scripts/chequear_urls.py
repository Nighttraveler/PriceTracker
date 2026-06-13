#!/usr/bin/env python3
"""
Checks URLs stored in variantes.url_producto and marks as discontinued=1
those that return 301, 404, or 410 (product removed from the supermarket catalog).

Usage:
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

DISCONTINUED_STATUSES = {301, 404, 410}
TIMEOUT = 10
WORKERS = 5
DELAY_PER_DOMAIN = 0.5  # seconds between requests to the same host
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}


def check_url(url: str) -> int:
    """Return the HTTP status code without following redirects. Returns 0 on network error."""
    try:
        resp = requests.head(url, allow_redirects=False, timeout=TIMEOUT, headers=HEADERS)
        # Some sites block HEAD with 403/405 (WAF). Fall back to GET in that case.
        if resp.status_code >= 400:
            resp = requests.get(url, allow_redirects=False, timeout=TIMEOUT, headers=HEADERS)
        return resp.status_code
    except requests.RequestException as e:
        log.debug(f"Network error on {url}: {e}")
        return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description="Check variant URLs and mark discontinued ones")
    parser.add_argument("--fuente", help="Limit to a specific source (e.g.: anonima)")
    parser.add_argument("--limit", type=int, help="Maximum number of variants to check")
    parser.add_argument("--dry-run", action="store_true", help="Do not update DB, only report")
    parser.add_argument("--recheck", action="store_true",
                        help="Re-check variants already marked as discontinued")
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
    log.info(f"Checking {total} variant(s)...")

    # Group by domain for rate limiting
    by_domain = defaultdict(list)
    for v in variantes:
        domain = urlparse(v["url_producto"]).netloc
        by_domain[domain].append(dict(v))

    results = {}  # variante_id → (status_code, variante_dict)

    def check_domain(domain_variants):
        for v in domain_variants:
            status = check_url(v["url_producto"])
            results[v["id"]] = (status, v)
            time.sleep(DELAY_PER_DOMAIN)

    with ThreadPoolExecutor(max_workers=WORKERS) as executor:
        futures = {
            executor.submit(check_domain, vs): domain
            for domain, vs in by_domain.items()
        }
        for future in as_completed(futures):
            future.result()

    marked = 0
    network_errors = 0
    for variante_id, (status, v) in results.items():
        if status == 0:
            network_errors += 1
            log.debug(f"[NETWORK ERROR] {v['fuente']} — {v['nombre_original']}")
        elif status in DISCONTINUED_STATUSES:
            log.info(f"[{status}] DISCONTINUED: {v['fuente']} — {v['nombre_original']}")
            if not args.dry_run:
                db._execute(
                    "UPDATE variantes SET descatalogado = 1 WHERE id = ?",
                    (variante_id,),
                )
                db.commit()
            marked += 1
        else:
            log.debug(f"[{status}] OK: {v['fuente']} — {v['nombre_original']}")

    mode = " (dry-run)" if args.dry_run else ""
    log.info(
        f"Summary{mode}: {marked}/{total} discontinued, "
        f"{network_errors} network errors (not marked)"
    )


if __name__ == "__main__":
    main()
