"""Load parsed DATEX II data into Postgres (P0-14)."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

import psycopg

from traffic.datex.parser import Measure, MeasurementSite

SCHEMA_FILE = Path(__file__).resolve().parents[2] / "sql" / "001_measures.sql"


def apply_schema(conn: psycopg.Connection) -> None:
    conn.execute(SCHEMA_FILE.read_text(encoding="utf-8"))


def upsert_sites(conn: psycopg.Connection, source: str, sites: Iterable[MeasurementSite]) -> int:
    count = 0
    with conn.cursor() as cur:
        for s in sites:
            cur.execute(
                """
                INSERT INTO measurement_site (site_id, source, site_version, name, geom)
                VALUES (%s, %s, %s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326))
                ON CONFLICT (site_id, source) DO UPDATE
                SET site_version = EXCLUDED.site_version,
                    name         = EXCLUDED.name,
                    geom         = EXCLUDED.geom,
                    updated_at   = now()
                """,
                (s.site_id, source, s.site_version, s.name, s.longitude, s.latitude),
            )
            count += 1
    return count


def insert_measures(conn: psycopg.Connection, source: str, measures: Iterable[Measure]) -> int:
    """Append measures; a repeated (site, time, revision) is ignored, a new revision is kept (D11)."""
    inserted = 0
    with conn.cursor() as cur:
        for m in measures:
            cur.execute(
                """
                INSERT INTO traffic_measure (site_id, source, source_ts, source_version, flow, avg_speed)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
                """,
                (m.site_id, source, m.source_ts, m.source_version, m.flow, m.avg_speed),
            )
            inserted += cur.rowcount
    return inserted
