-- Core measure model for Phase 0 (P0-14), following D8 and D11.
-- Raw measures are keyed on the measurement site and keep every source revision.
-- Idempotent: safe to run on every smoke-test run.

CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE IF NOT EXISTS measurement_site (
    site_id      TEXT        NOT NULL,
    source       TEXT        NOT NULL,
    site_version TEXT,
    name         TEXT,
    geom         geometry(Point, 4326) NOT NULL,   -- storage CRS EPSG:4326 (conventions)
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (site_id, source)
);

-- D8 + D11: one row per (site, source, measurement time, source revision).
CREATE TABLE IF NOT EXISTS traffic_measure (
    site_id        TEXT        NOT NULL,
    source         TEXT        NOT NULL,
    source_ts      TIMESTAMPTZ NOT NULL,   -- measurement time from the source (UTC)
    source_version TIMESTAMPTZ NOT NULL,   -- publication time of the carrying payload
    ingest_ts      TIMESTAMPTZ NOT NULL DEFAULT now(),
    flow           REAL,                   -- veh/h
    avg_speed      REAL,                   -- km/h
    occupancy      REAL,
    travel_time    REAL,                   -- s
    confidence     SMALLINT,
    PRIMARY KEY (site_id, source, source_ts, source_version)
);

-- Hypertable when TimescaleDB is available (the dev stack has it; plain Postgres skips this).
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'timescaledb') THEN
        PERFORM create_hypertable('traffic_measure', 'source_ts', if_not_exists => TRUE, migrate_data => TRUE);
    END IF;
END
$$;

-- D11: latest revision per (site, source, measurement time). Aggregates read from here.
CREATE OR REPLACE VIEW traffic_measure_current AS
SELECT DISTINCT ON (site_id, source, source_ts) *
FROM traffic_measure
ORDER BY site_id, source, source_ts, source_version DESC;

-- Map layer for the smoke test: each site with its most recent current measure.
-- Martin publishes it as a vector-tile source named `site_latest_traffic`.
CREATE OR REPLACE VIEW site_latest_traffic AS
SELECT s.site_id, s.source, s.name, s.geom,
       m.source_ts, m.source_version, m.flow, m.avg_speed
FROM measurement_site s
LEFT JOIN LATERAL (
    SELECT c.source_ts, c.source_version, c.flow, c.avg_speed
    FROM traffic_measure_current c
    WHERE c.site_id = s.site_id AND c.source = s.source
    ORDER BY c.source_ts DESC
    LIMIT 1
) m ON TRUE;
