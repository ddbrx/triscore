from base import dt
import pytest


class DatetimeString:
    def test_datetime_from_string(self):
        r = dt.datetime_from_string('2020-04-16T09:55:23')
        e = dt.datetime(year=2020, month=4, day=16,
                        hour=9, minute=55, second=23)
        assert r == e

    def test_datetime_to_string(self):
        d = dt.datetime(year=2020, month=4, day=16,
                        hour=9, minute=55, second=23)
        r = dt.datetime_to_string(d)
        e = '2020-04-16T09:55:23'
        assert r == e

    def test_date_from_string(self):
        r = dt.date_from_string('2020-04-16')
        e = dt.datetime(year=2020, month=4, day=16)
        assert r == e

    def test_date_to_string_date_format(self):
        d = dt.datetime(year=2020, month=4, day=16)
        r = dt.date_to_string(d, format=dt.DATE_FORMAT)
        e = '2020-04-16'
        assert r == e


class TestDelta:
    def test_year_positive(self):
        d = dt.datetime(year=2015, month=4, day=16,
                        hour=9, minute=55, second=23)
        r = dt.delta(d, years=1)
        e = dt.datetime(year=2016, month=4, day=16,
                        hour=9, minute=55, second=23)
        assert r == e

    def test_year_negative(self):
        d = dt.datetime(year=2019, month=4, day=16,
                        hour=9, minute=55, second=23)
        r = dt.delta(d, years=-4)
        e = dt.datetime(year=2015, month=4, day=16,
                        hour=9, minute=55, second=23)
        assert r == e

    def test_leap_year(self):
        d = dt.datetime(year=2020, month=2, day=29,
                        hour=9, minute=55, second=23)
        r = dt.delta(d, years=-3)
        e = dt.datetime(year=2017, month=2, day=28,
                        hour=9, minute=55, second=23)
        assert r == e

    def test_days_positive(self):
        d = dt.datetime(year=2019, month=8, day=30,
                        hour=9, minute=55, second=23)
        r = dt.delta(d, days=5)
        e = dt.datetime(year=2019, month=9, day=4,
                        hour=9, minute=55, second=23)
        assert r == e

    def test_days_negative(self):
        d = dt.datetime(year=2020, month=1, day=1,
                        hour=9, minute=55, second=23)
        r = dt.delta(d, days=-1)
        e = dt.datetime(year=2019, month=12, day=31,
                        hour=9, minute=55, second=23)
        assert r == e

    def test_days_and_year(self):
        d = dt.datetime(year=2021, month=2, day=28,
                        hour=23, minute=59, second=59)
        r = dt.delta(d, years=-1, days=1)
        e = dt.datetime(year=2020, month=2, day=29,
                        hour=23, minute=59, second=59)
        assert r == e
