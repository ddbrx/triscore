from base import log


logger = log.setup_logger(__file__)

UNKNOWN_PROFILE = 'unknown'
UNKNOWN_RACER = 'unknown'


def get_value_or(result, field, default):
    if field not in result or not result[field]:
        return default
    return result[field]


def get_race_country(race):
    return race['RaceCountry']


def get_racer_count(race):
    return race['RacerCount']


def get_race_date(race):
    return race['Date']


def get_race_name(race):
    return race['RaceName']


def get_race_url(race):
    return race['RaceUrl']


def get_race_type(race):
    race_event_url = race['EventUrl']
    return race_event_url.split('/')[-1]


def get_race_brand(race):
    return get_race_name(race).split()[0]


def get_profile(result):
    profile_url = result['ProfileUrl']
    if profile_url:
        return profile_url.replace('/profile', '')

    country = get_country(result)
    assert country

    racer_url = result['RacerUrl']
    if racer_url:
        return f'/{country.lower()}{racer_url}'

    return UNKNOWN_PROFILE


def get_name(result):
    return ' '.join(x.lower().capitalize() for x in reversed(get_value_or(result, 'Racer', UNKNOWN_RACER).strip().replace(',', ' ').split()))


def get_country(result):
    return result['Country']


def get_gender(result):
    return result['Sex']


def get_group(result):
    return result['Division'].lower()


def get_race_results(race):
    return race['Results']


def str_time_to_seconds(str):
    total_seconds = 0
    sec_multiplier = 1
    for part in reversed(str.split(':')):
        total_seconds += int(part) * sec_multiplier
        sec_multiplier *= 60
    return total_seconds


def get_finish_time(result):
    return str_time_to_seconds(result['Finish'])


def get_swim_time(result):
    return str_time_to_seconds(result['Swim'])


def get_t1_time(result):
    return str_time_to_seconds(result['T1'])


def get_bike_time(result):
    return str_time_to_seconds(result['Bike'])


def get_t2_time(result):
    return str_time_to_seconds(result['T2'])


def get_run_time(result):
    return str_time_to_seconds(result['Run'])


def fix_profile_country(results, race_country):
    for result in results:
        if not result['Country']:
            result['Country'] = race_country
