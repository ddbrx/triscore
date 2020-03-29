import json
import os

SCRIPT_DIR = os.path.dirname(__file__)

CYRILLIC_FIFA_CODES = ['RUS', 'BLR', 'UKR']


class LocationResolver:
    COUNTRY_EXCEPTION_MAPPING = {
        'Korea': 'Korea, South',
        'England': 'United Kingdom',
        'Victoria': 'Australia'
    }

    def __init__(self):
        country_code_file = os.path.join(SCRIPT_DIR, 'country_codes.json')
        with open(country_code_file) as ccf:
            self.countries = json.load(ccf)

        usa_states_file = os.path.join(SCRIPT_DIR, 'usa_states.json')
        with open(usa_states_file) as usf:
            self.states = json.load(usf)

    @staticmethod
    def is_cyrillic_fifa_code(fifa_code):
        return fifa_code in CYRILLIC_FIFA_CODES

    def get_country_by_iso2_code_or_none(self, iso2_code):
        filtered_a2 = self.get_countries(lambda x: x['a2'] == iso2_code)
        if len(filtered_a2) == 1:
            return filtered_a2[0]

        filtered_a2_ioc = self.get_countries(lambda x: x['ioc'] == iso2_code)
        if len(filtered_a2_ioc) == 1:
            return filtered_a2_ioc[0]

        return None


    def get_country_or_none(self, condition):
        filtered_a2 = self.get_countries(condition)
        if len(filtered_a2) == 1:
            return filtered_a2[0]
        return None

    def get_countries(self, condition):
        return list(filter(lambda x: condition(x), self.countries))

    def get_usa_state_names(self):
        return

    def try_deduce_country(self, name):
        country_options = [name]
        country_words = name.split()
        for i in range(0, len(country_words) + 1):
            for j in range(i + 1, len(country_words) + 1):
                country_option = ' '.join(country_words[i:j])
                country_options.append(country_option)

        for country_option in country_options:
            if country_option in self.COUNTRY_EXCEPTION_MAPPING:
                country_option = self.COUNTRY_EXCEPTION_MAPPING[country_option]

            if country_option in self.states.values() or country_option.upper() in self.states.keys():
                return self.get_country_by_iso2_code_or_none('US')

            countries = self.get_countries(
                lambda x: x['name'] == country_option)
            if len(countries) == 1:
                return countries[0]

        return None
