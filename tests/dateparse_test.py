from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import pytest

from funpayparsers.parsers.utils import (
    MONTHS,
    TODAY_WORDS,
    YESTERDAY_WORDS,
    parse_date_string,
)

CURR_DATE = datetime.now(ZoneInfo('Europe/Moscow')).replace(
    hour=0,
    minute=0,
    second=0,
    microsecond=0,
)

SEPARATORS = (',', ' at', ' в', ' о')


@pytest.mark.parametrize(
    'date_str,expected', [
        (
            '12:20:24',
            CURR_DATE.replace(hour=12, minute=20, second=24).timestamp()
        ),
        (
            '12.05.24',
            CURR_DATE.replace(day=12, month=5, year=2024).timestamp()
        ),
        *[
            (
                f'{word}{sep} 12:20',
                CURR_DATE.replace(hour=12, minute=20).timestamp()
            ) for word in TODAY_WORDS for sep in SEPARATORS
        ],
        *[
            (
                f'{word}{sep} 12:20',
                (CURR_DATE.replace(hour=12, minute=20) - timedelta(days=1)).timestamp()
            ) for word in YESTERDAY_WORDS for sep in SEPARATORS
        ],
        *[
            (
                f'12 {month_name}{sep} 12:20',
                CURR_DATE.replace(month=month, day=12, hour=12, minute=20).timestamp()
            ) for month_name, month in MONTHS.items() for sep in SEPARATORS
        ],
        *[
            (
                f'12 {month_name} 2024{sep} 12:20',
                CURR_DATE.replace(year=2024, month=month, day=12, hour=12, minute=20).timestamp()
            ) for month_name, month in MONTHS.items() for sep in SEPARATORS
        ],
    ]
)
def test_date_string_parsing(date_str: str, expected: datetime) -> None:
    assert parse_date_string(date_str) == expected


class _UtcHostClock(datetime):
    """`datetime` whose naive `now()` is the UTC wall clock, as on a UTC server."""

    @classmethod
    def now(cls, tz=None):
        utc = datetime(2026, 10, 20, 22, 30, tzinfo=ZoneInfo('UTC'))
        return utc.astimezone(tz) if tz else utc.replace(tzinfo=None)


def test_today_follows_the_moscow_day_on_a_utc_host(monkeypatch):
    monkeypatch.setattr('funpayparsers.parsers.utils.datetime', _UtcHostClock)

    # 22:30 UTC on the 20th is 01:30 MSK on the 21st.
    expected = datetime(2026, 10, 21, 12, 0, tzinfo=ZoneInfo('Europe/Moscow')).timestamp()
    assert parse_date_string('сегодня, 12:00') == expected
