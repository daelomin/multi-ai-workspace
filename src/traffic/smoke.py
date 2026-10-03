"""End-to-end smoke test (P0-14): DATEX II XML -> parser -> Postgres -> map layer.

Usage, with the dev stack running (`make -C dev up`):

    make -C dev smoke
    # or: uv run --env-file .env python -m traffic.smoke

Then open web/smoke_map.html in a browser to see the sites served by Martin.
Exits with a non-zero status if any check fails.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import psycopg

from traffic.datex.parser import parse_measured_data, parse_measurement_sites
from traffic.load import apply_schema, insert_measures, upsert_sites

ROOT = Path(__file__).resolve().parents[2]
SAMPLES = ROOT / "samples" / "datex"
SOURCE = "smoke"

# Expected state after loading the three sample files.
EXPECTED_SITES = 3
EXPECTED_RAW_ROWS = 4          # 3 measures + 1 correction kept as a revision (D11)
EXPECTED_CURRENT_SITE_002 = 58.0  # the correction's speed, not the original 64.5


def run(database_url: str) -> list[str]:
    """Load the samples and return a list of failed checks (empty when all pass)."""
    sites = parse_measurement_sites(SAMPLES / "measurement_sites.xml")
    measures = parse_measured_data(SAMPLES / "measured_data.xml")
    correction = parse_measured_data(SAMPLES / "measured_data_correction.xml")

    failures: list[str] = []
    with psycopg.connect(database_url, autocommit=True) as conn:
        apply_schema(conn)
        # Start clean so the checks are repeatable; only the smoke source is touched.
        conn.execute("DELETE FROM traffic_measure WHERE source = %s", (SOURCE,))
        conn.execute("DELETE FROM measurement_site WHERE source = %s", (SOURCE,))

        upsert_sites(conn, SOURCE, sites)
        insert_measures(conn, SOURCE, measures)
        insert_measures(conn, SOURCE, correction)
        insert_measures(conn, SOURCE, measures)  # re-delivery of the same file must add nothing

        n_sites = conn.execute("SELECT count(*) FROM measurement_site WHERE source = %s", (SOURCE,)).fetchone()[0]
        n_raw = conn.execute("SELECT count(*) FROM traffic_measure WHERE source = %s", (SOURCE,)).fetchone()[0]
        current = conn.execute(
            "SELECT avg_speed FROM traffic_measure_current WHERE source = %s AND site_id = 'SMOKE_SITE_002'",
            (SOURCE,),
        ).fetchone()
        layer = conn.execute(
            "SELECT site_id, name, avg_speed, flow, ST_AsText(geom) FROM site_latest_traffic "
            "WHERE source = %s ORDER BY site_id",
            (SOURCE,),
        ).fetchall()

    if n_sites != EXPECTED_SITES:
        failures.append(f"measurement_site: expected {EXPECTED_SITES} rows, found {n_sites}")
    if n_raw != EXPECTED_RAW_ROWS:
        failures.append(f"traffic_measure: expected {EXPECTED_RAW_ROWS} rows, found {n_raw}")
    if current is None or current[0] != EXPECTED_CURRENT_SITE_002:
        failures.append(f"traffic_measure_current: expected SMOKE_SITE_002 speed {EXPECTED_CURRENT_SITE_002}, found {current}")
    if len(layer) != EXPECTED_SITES or any(row[2] is None for row in layer):
        failures.append(f"site_latest_traffic: expected {EXPECTED_SITES} sites with a speed, found {layer}")

    print(f"sites: {n_sites}  raw measures: {n_raw}  map layer rows: {len(layer)}")
    for site_id, name, speed, flow, geom in layer:
        print(f"  {site_id}  {name}  {speed} km/h  {flow} veh/h  {geom}")
    return failures


def main() -> int:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("DATABASE_URL is not set (copy .env.example to .env and use `uv run --env-file .env`).", file=sys.stderr)
        return 2
    failures = run(database_url)
    if failures:
        print("SMOKE TEST FAILED", file=sys.stderr)
        for f in failures:
            print(f"  - {f}", file=sys.stderr)
        return 1
    print("SMOKE TEST PASSED — open web/smoke_map.html to check the map layer.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
