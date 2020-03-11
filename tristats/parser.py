DEFAULT_COUNTRY = 'unknown'


def get_value_or(item, field, default):
    if field not in item or not item[field]:
        return default
    return item[field]


def get_name(racer):
    return ' '.join([x.capitalize() for x in racer.lower().strip().split(' ')[::-1]])


def get_race_country(race):
    return get_value_or(race, 'RaceCountry', DEFAULT_COUNTRY).lower()


def get_profile(item, race):
    profile_url_or_null = item['ProfileUrl']
    if not profile_url_or_null:
        racer = item['Racer']
        assert racer, f'Racer is null item {item}'
        race_country = get_race_country(race)
        formatted_racer = racer.lower().strip(" .").replace('.', '-').replace(' ', '-')
        return f'/{race_country}/profile/{formatted_racer}'
    return profile_url_or_null
