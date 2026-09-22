"""Device binding + 7-day new-device cooldown + impossible-travel detection
(P2-13).

A brand-new device on an existing account can't push a review's PoE past L1
for 7 days — long enough that a stolen/purchased account "warms up" the new
device before it's trusted, short enough not to punish someone who just got
a new phone. Impossible travel reuses the same speed-jump math as
app/domain/geofence.py (a device in Ulaanbaatar and Darkhan 10 minutes apart
is impossible regardless of whether it's one GPS trail or two review
sessions from the "same" account) — acceptance: 100% catch rate on the test
cases.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta

from app.domain.geofence import haversine_distance_km

NEW_DEVICE_COOLDOWN_DAYS = 7
IMPOSSIBLE_TRAVEL_SPEED_KMH = 150.0


@dataclass(frozen=True)
class KnownLocation:
    lat: float
    lon: float
    seen_at: datetime


def is_device_in_cooldown(*, first_seen_at: datetime, now: datetime) -> bool:
    return now - first_seen_at < timedelta(days=NEW_DEVICE_COOLDOWN_DAYS)


def detect_impossible_travel(previous: KnownLocation, current: KnownLocation) -> bool:
    hours = (current.seen_at - previous.seen_at).total_seconds() / 3600
    if hours <= 0:
        return True  # a non-positive time delta between two distinct locations is itself impossible
    distance_km = haversine_distance_km(previous.lat, previous.lon, current.lat, current.lon)
    implied_speed_kmh = distance_km / hours
    return implied_speed_kmh > IMPOSSIBLE_TRAVEL_SPEED_KMH
