import pytest
from base import dt
from race import matcher


class TestAgeGroupLowerUppedBounds:
    def test_mpro(self):
        assert matcher.get_min_max_years('MPRO') == (18, 50)

    def test_fpro(self):
        assert matcher.get_min_max_years('FPRO') == (18, 50)

    def test_hc(self):
        assert matcher.get_min_max_years('HC') == (18, 90)

    def test_pc(self):
        assert matcher.get_min_max_years('PC') == (18, 90)

    def test_no_dash(self):
        assert matcher.get_min_max_years('M30_34') == (18, 90)

    def test_m18_24(self):
        assert matcher.get_min_max_years('M18-24') == (18, 24)

    def test_f50_54(self):
        assert matcher.get_min_max_years('F18-24') == (18, 24)

    def test_invalid_no_gender(self):
        with pytest.raises(Exception):
            matcher.get_min_max_years('18-24')

    def test_invalid_wrond_order(self):
        with pytest.raises(Exception):
            matcher.get_min_max_years('M24-18')


class TestMinMaxBirthDate:
    def test_basic_group(self):
        m, M = matcher.get_min_max_birth_dates(
            age_group='M18-24', date=dt.datetime(2025, 10, 23))
        assert m == dt.datetime(2000, 10, 24)
        assert M == dt.datetime(2007, 10, 23)

    def test_pro_group(self):
        m, M = matcher.get_min_max_birth_dates(
            age_group='MPRO', date=dt.datetime(2025, 10, 23))
        assert m == dt.datetime(1974, 10, 24)
        assert M == dt.datetime(2007, 10, 23)

    def test_unknown_group(self):
        m, M = matcher.get_min_max_birth_dates(
            age_group='unknown', date=dt.datetime(2025, 10, 23))
        assert m == dt.datetime(1934, 10, 24)
        assert M == dt.datetime(2007, 10, 23)
