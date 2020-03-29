import pytest
from resolver import LocationResolver


class TestGetOneAndOnlyCountry:
    resolver = LocationResolver()

    def test_valid_codes(self):
        self._test_country_name_by_fifa_code('RUS', 'Russian Federation')
        self._test_country_name_by_fifa_code('BLR', 'Belarus')
        self._test_country_name_by_fifa_code('SUI', 'Switzerland')
        self._test_country_name_by_fifa_code('GER', 'Germany')

    def test_invalid_code(self):
        assert not self._get_country_name_by_fifa_code('UNKNOWN')

    def _test_country_name_by_fifa_code(self, fifa_code, expected_name):
        assert self._get_country_name_by_fifa_code(fifa_code) == expected_name

    def _get_country_name_by_fifa_code(self, fifa_code):
        country = self.resolver.get_country_or_none(
            lambda x: x['fifa'] == fifa_code)
        return country['name'] if country else None


class TestIsCyrillicCountry:
    def test_cyrillic_country(self):
        assert LocationResolver.is_cyrillic_fifa_code('RUS')
        assert LocationResolver.is_cyrillic_fifa_code('BLR')
        assert LocationResolver.is_cyrillic_fifa_code('UKR')

    def test_not_cyrillic_country(self):
        assert not LocationResolver.is_cyrillic_fifa_code('USA')
        assert not LocationResolver.is_cyrillic_fifa_code('GER')
        assert not LocationResolver.is_cyrillic_fifa_code('SUI')


class TestTryDeduceCountry:
    resolver = LocationResolver()

    def test_netherlands(self):
        assert self.resolver.try_deduce_country('The Netherlands')

    def test_korea(self):
        assert self.resolver.try_deduce_country('Korea')

    def test_england(self):
        assert self.resolver.try_deduce_country('England')

    def test_victoria(self):
        assert self.resolver.try_deduce_country('Victoria')

    def test_ny(self):
        assert self.resolver.try_deduce_country('NY')
