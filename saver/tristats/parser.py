DEFAULT_COUNTRY = 'nocountry'


def get_value_or(item, field, default):
    if field not in item or not item[field]:
        return default
    return item[field]


def get_name(racer):
    return ' '.join([x.capitalize() for x in racer.lower().strip().split(' ')[::-1]])


def get_race_country(race):
    return get_value_or(race, 'RaceCountry', DEFAULT_COUNTRY).lower()


def get_profile(item, race):
    profile_url = item['ProfileUrl']
    if profile_url:
        return profile_url

    race_country = get_race_country(race)
    racer_url = item['RacerUrl']
    if racer_url:
        return f'/{race_country}/profile{racer_url}'

    return 'unknown'
