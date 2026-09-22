"""GPS geofence dwell-time + spoofing heuristics (P2-01/P2-02).

Acceptance: dwell-time error <=+-2min against 50 real visits, battery <=3%/day
(mobile-side sampling interval, not this module's concern), and 100% catch
rate on 5 mock-location app types on the tested set.

Everything here is a pure function over a list of GPS pings so it's testable
without a device, a database, or a live geofence service — the API layer
(not yet wired; see docs/PROGRESS.md) is a thin wrapper that loads pings from
`location_pings` and calls these.
"""

import math
from dataclasses import dataclass
from datetime import datetime

EARTH_RADIUS_KM = 6371.0
IMPOSSIBLE_SPEED_KMH = 150.0

# Mock-location apps frequently report a suspiciously exact accuracy (many
# report exactly 1.0m, since they don't simulate real GPS noise) or a
# constant reading across pings that should naturally jitter.
SUSPICIOUS_ACCURACY_M = 1.0


@dataclass(frozen=True)
class GpsPing:
    lat: float
    lon: float
    accuracy_m: float
    is_mock_provider_flag: bool  # from the OS location API (Android isFromMockProvider / iOS equivalent)
    recorded_at: datetime


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


def is_within_geofence(ping: GpsPing, *, center_lat: float, center_lon: float, radius_m: float) -> bool:
    distance_km = haversine_distance_km(ping.lat, ping.lon, center_lat, center_lon)
    return distance_km * 1000 <= radius_m


def compute_dwell_seconds(pings: list[GpsPing], *, center_lat: float, center_lon: float, radius_m: float) -> float:
    """Sum of time between consecutive pings that are *both* inside the
    geofence — a ping pair straddling the boundary (one in, one out) doesn't
    count, which biases slightly conservative (undercounts dwell) rather
    than overcounts, matching the SOW's fraud-resistance intent.
    """
    inside = [p for p in sorted(pings, key=lambda p: p.recorded_at) if is_within_geofence(p, center_lat=center_lat, center_lon=center_lon, radius_m=radius_m)]
    if len(inside) < 2:
        return 0.0

    total = 0.0
    for a, b in zip(inside, inside[1:]):
        gap = (b.recorded_at - a.recorded_at).total_seconds()
        # A gap far longer than a plausible re-entry (>10min) means the user
        # likely left and came back — don't count the gap itself as dwell.
        if gap <= 600:
            total += gap
    return total


def detect_speed_jump(pings: list[GpsPing]) -> list[tuple[GpsPing, GpsPing, float]]:
    """Returns (prev, curr, implied_speed_kmh) for every consecutive pair
    that implies travel faster than IMPOSSIBLE_SPEED_KMH."""
    ordered = sorted(pings, key=lambda p: p.recorded_at)
    anomalies = []
    for a, b in zip(ordered, ordered[1:]):
        hours = (b.recorded_at - a.recorded_at).total_seconds() / 3600
        if hours <= 0:
            continue
        distance_km = haversine_distance_km(a.lat, a.lon, b.lat, b.lon)
        speed_kmh = distance_km / hours
        if speed_kmh > IMPOSSIBLE_SPEED_KMH:
            anomalies.append((a, b, speed_kmh))
    return anomalies


def detect_mock_location(pings: list[GpsPing]) -> bool:
    if any(p.is_mock_provider_flag for p in pings):
        return True
    if detect_speed_jump(pings):
        return True
    if len(pings) >= 3 and len({p.accuracy_m for p in pings}) == 1 and pings[0].accuracy_m <= SUSPICIOUS_ACCURACY_M:
        return True  # identical, suspiciously-perfect accuracy across every ping
    return False
