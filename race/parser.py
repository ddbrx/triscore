def get_race_name(race):
    return race['name']


def get_race_date(race):
    return race['date']


def get_race_brand(race):
    return race['brand']


def get_race_type(race):
    return race['type']


def get_race_fifa_code(race):
    return race['location']['c']


def get_race_results(race):
    return race['results']


def get_athlete_id(result):
    return result['id']


def get_athlete_name(result):
    return result['n']


def get_country_fifa_code(result):
    return result['c']


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


def get_gender(result):
    return result['g']


def get_gender_size(result):
    return result['gs']


def get_gender_rank(result):
    return result['gr']


def get_overall_size(result):
    return result['os']


def get_overall_rank(result):
    return result['or']


def get_legs(result):
    return result['legs']
