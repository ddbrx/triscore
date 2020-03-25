UNKNOWN_PROFILE = 'unknown'
UNKNOWN_RACER = 'unknown'


def get_brand(race):
    return get_race_url(race).split('/')[1]


def get_value_or(item, field, default):
    if field not in item or not item[field]:
        return default
    return item[field]


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


def get_profile(item):
    profile_url = item['ProfileUrl']
    if profile_url:
        return profile_url.replace('/profile', '')

    country = get_country(item)
    assert country

    racer_url = item['RacerUrl']
    if racer_url:
        return f'/{country.lower()}{racer_url}'

    return UNKNOWN_PROFILE


def get_name(item):
    return ' '.join(x.lower().capitalize() for x in reversed(get_value_or(item, 'Racer', UNKNOWN_RACER).strip().replace(',', ' ').split()))


def get_country(item):
    return item['Country']


def get_gender(item):
    return item['Sex']


def get_group(item):
    return item['Division'].lower()


def get_results(race):
    return race['Results']


def str_time_to_seconds(str):
    total_seconds = 0
    sec_multiplier = 1
    for part in reversed(str.split(':')):
        total_seconds += int(part) * sec_multiplier
        sec_multiplier *= 60
    return total_seconds


def get_finish_time(item):
    return str_time_to_seconds(item['Finish'])


def get_swim_time(item):
    return str_time_to_seconds(item['Swim'])


def get_t1_time(item):
    return str_time_to_seconds(item['T1'])


def get_bike_time(item):
    return str_time_to_seconds(item['Bike'])


def get_t2_time(item):
    return str_time_to_seconds(item['T2'])


def get_run_time(item):
    return str_time_to_seconds(item['Run'])


def fix_profile_country(results, race_country):
    for result in results:
        if not result['Country']:
            result['Country'] = race_country
