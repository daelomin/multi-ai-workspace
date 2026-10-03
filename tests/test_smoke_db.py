"""Database part of the smoke test; runs only when SMOKE_DATABASE_URL is set."""

import os

import pytest

from traffic.smoke import run

DATABASE_URL = os.environ.get("SMOKE_DATABASE_URL")


@pytest.mark.skipif(not DATABASE_URL, reason="SMOKE_DATABASE_URL not set (needs Postgres + PostGIS)")
def test_smoke_load_passes_all_checks():
    assert run(DATABASE_URL) == []
