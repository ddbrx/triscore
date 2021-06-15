def get_race_processed(race):
    return race['_processed']


def get_race_name(race):
    return race['name']


def get_race_date(race):
    return race['date']


def get_race_brand(race):
    return race['brand']


def get_race_type(race):
    return race['type']


def get_race_country_iso_num(race, default=0):
    location_info = race['location']
    return location_info['c'] if 'c' in location_info else default


def get_result_country_iso_num(result):
    return result['c']


def get_athlete_id(result):
    return result['id']


def get_athlete_name(result):
    n = result['n']
    return n if n else ''


def get_bib(result):
    return result['b']


def get_finish_status(result):
    return result['st']


def get_finish_time(result):
    return result['t']


def get_age_group(result):
    return result['a']


def get_age_group_size(result):
    return result['as']


def get_age_group_rank(result):
    return result['ar']


def get_time_age_group_rank(result):
    return result['tar']


def get_gender(result):
    return result['g']


def get_gender_size(result):
    return result['gs']


def get_gender_rank(result):
    return result['gr']


def get_time_gender_rank(result):
    return result['tgr']


def get_overall_size(result):
    return result['os']


def get_overall_rank(result):
    return result['or']


def get_time_overall_rank(result):
    return result['tor']


def get_legs(result):
    return result['legs']
