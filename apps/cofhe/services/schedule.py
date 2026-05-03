from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

import pytz
from dateutil.relativedelta import relativedelta

from apps.cofhe.models import ScheduleConfig


@dataclass
class ScheduleExpansion:
    times: list[datetime]


def next_occurrence(schedule: ScheduleConfig, after: datetime) -> Optional[datetime]:
    expansion = expand_schedule(schedule, limit=500)
    for t in expansion.times:
        if t > after:
            return t
    return None


def expand_schedule(schedule: ScheduleConfig, limit: int = 200) -> ScheduleExpansion:
    tz   = pytz.UTC
    now  = schedule.start_at.astimezone(tz)
    end  = schedule.end_at.astimezone(tz) if schedule.end_at else None
    kind = schedule.type

    times: list[datetime] = []

    if kind == "instant":
        times.append(now)
        return ScheduleExpansion(times=times)

    cursor = now.replace(
        hour=schedule.hour,
        minute=schedule.minute,
        second=0,
        microsecond=0,
    )
    if cursor < now:
        cursor = _advance(cursor, kind, schedule)

    while len(times) < limit:
        if end and cursor > end:
            break
        times.append(cursor)
        cursor = _advance(cursor, kind, schedule)

    return ScheduleExpansion(times=times)


def _advance(dt: datetime, kind: str, s: ScheduleConfig) -> datetime:
    if kind == "daily":
        return dt + relativedelta(days=1)
    if kind == "weekly":
        return dt + relativedelta(weeks=1)
    if kind == "monthly":
        return dt + relativedelta(months=1)
    if kind == "yearly":
        return dt + relativedelta(years=1)
    return dt + relativedelta(days=1)