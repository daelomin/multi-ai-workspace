"""Tolerant DATEX II 2.2 parser for measurement sites and measured data (P0-14).

Tolerant by design (spec Phase 0 risks): elements are matched by local name, so the
namespace prefix or exact namespace version does not matter, and unknown elements are
ignored. Only what the smoke test needs is extracted: site locations, vehicle flow
(veh/h) and average speed (km/h).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from lxml import etree

XSI_TYPE = "{http://www.w3.org/2001/XMLSchema-instance}type"


@dataclass(frozen=True)
class MeasurementSite:
    site_id: str
    site_version: str
    name: str | None
    latitude: float
    longitude: float


@dataclass(frozen=True)
class Measure:
    """One measurement for one site at one time.

    `source_version` is the publication time of the payload that carried it: a later
    publication for the same (site, measurement time) is a correction (D11).
    """

    site_id: str
    source_ts: datetime
    source_version: datetime
    flow: float | None
    avg_speed: float | None


def _children(el: etree._Element, name: str) -> list[etree._Element]:
    return [c for c in el if isinstance(c.tag, str) and etree.QName(c).localname == name]


def _first(el: etree._Element, *path: str) -> etree._Element | None:
    """Follow a path of local names, returning the first match or None."""
    current: etree._Element | None = el
    for name in path:
        if current is None:
            return None
        matches = _children(current, name)
        current = matches[0] if matches else None
    return current


def _text(el: etree._Element, *path: str) -> str | None:
    found = _first(el, *path)
    if found is None or found.text is None:
        return None
    return found.text.strip()


def _float(value: str | None) -> float | None:
    return float(value) if value not in (None, "") else None


def _datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _xsi_type(el: etree._Element) -> str | None:
    value = el.get(XSI_TYPE)
    return value.split(":")[-1] if value else None


def _payload(path: Path, expected_type: str) -> etree._Element:
    root = etree.parse(str(path)).getroot()
    payload = _first(root, "payloadPublication")
    if payload is None:
        raise ValueError(f"{path}: no payloadPublication element")
    if _xsi_type(payload) != expected_type:
        raise ValueError(f"{path}: expected {expected_type}, found {_xsi_type(payload)}")
    return payload


def parse_measurement_sites(path: Path) -> list[MeasurementSite]:
    """Parse a MeasurementSiteTablePublication; skip sites without point coordinates."""
    payload = _payload(path, "MeasurementSiteTablePublication")
    sites: list[MeasurementSite] = []
    for table in _children(payload, "measurementSiteTable"):
        for record in _children(table, "measurementSiteRecord"):
            coords = _first(record, "measurementSiteLocation", "pointByCoordinates", "pointCoordinates")
            if coords is None:
                continue
            lat, lon = _float(_text(coords, "latitude")), _float(_text(coords, "longitude"))
            if lat is None or lon is None:
                continue
            sites.append(
                MeasurementSite(
                    site_id=record.get("id", ""),
                    site_version=record.get("version", ""),
                    name=_text(record, "measurementSiteName", "values", "value"),
                    latitude=lat,
                    longitude=lon,
                )
            )
    return sites


def parse_measured_data(path: Path) -> list[Measure]:
    """Parse a MeasuredDataPublication into one Measure per site and measurement time."""
    payload = _payload(path, "MeasuredDataPublication")
    version = _datetime(_text(payload, "publicationTime"))
    if version is None:
        raise ValueError(f"{path}: missing publicationTime")

    measures: list[Measure] = []
    for site in _children(payload, "siteMeasurements"):
        ref = _first(site, "measurementSiteReference")
        source_ts = _datetime(_text(site, "measurementTimeDefault"))
        if ref is None or source_ts is None:
            continue
        flow = speed = None
        for indexed in _children(site, "measuredValue"):
            basic = _first(indexed, "measuredValue", "basicData")
            if basic is None:
                continue
            kind = _xsi_type(basic)
            if kind == "TrafficFlow":
                flow = _float(_text(basic, "vehicleFlow", "vehicleFlowRate"))
            elif kind == "TrafficSpeed":
                speed = _float(_text(basic, "averageVehicleSpeed", "speed"))
        measures.append(
            Measure(site_id=ref.get("id", ""), source_ts=source_ts, source_version=version, flow=flow, avg_speed=speed)
        )
    return measures
