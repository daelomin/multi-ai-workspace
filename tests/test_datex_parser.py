from datetime import datetime, timezone
from pathlib import Path

import pytest

from traffic.datex.parser import parse_measured_data, parse_measurement_sites

SAMPLES = Path(__file__).resolve().parents[1] / "samples" / "datex"


def test_parses_sites_with_coordinates():
    sites = parse_measurement_sites(SAMPLES / "measurement_sites.xml")
    assert [s.site_id for s in sites] == ["SMOKE_SITE_001", "SMOKE_SITE_002", "SMOKE_SITE_003"]
    assert sites[0].latitude == pytest.approx(47.25)
    assert sites[0].longitude == pytest.approx(-1.45)
    assert sites[0].name == "Site fictif 001"


def test_parses_flow_speed_and_version():
    measures = parse_measured_data(SAMPLES / "measured_data.xml")
    assert len(measures) == 3
    m = measures[1]
    assert (m.site_id, m.flow, m.avg_speed) == ("SMOKE_SITE_002", 2410.0, 64.5)
    assert m.source_ts == datetime(2026, 10, 3, 6, 54, tzinfo=timezone.utc)
    assert m.source_version == datetime(2026, 10, 3, 7, 0, tzinfo=timezone.utc)


def test_correction_has_same_time_and_later_version():
    original = {m.site_id: m for m in parse_measured_data(SAMPLES / "measured_data.xml")}
    (fix,) = parse_measured_data(SAMPLES / "measured_data_correction.xml")
    assert fix.source_ts == original[fix.site_id].source_ts
    assert fix.source_version > original[fix.site_id].source_version


def test_rejects_wrong_publication_type():
    with pytest.raises(ValueError, match="MeasuredDataPublication"):
        parse_measured_data(SAMPLES / "measurement_sites.xml")
