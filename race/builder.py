import re
from base import log

logger = log.setup_logger(__file__)


FINISH_STATUS_DQ = 'DQ'
FINISH_STATUS_DNS = 'DNS'
FINISH_STATUS_DNF = 'DNF'
FINISH_STATUS_OK = 'ok'

MAX_TIME = 99999
FLOAT_DECIMALS = 2

SWIM_LEG = 's'
T1_LEG = 't1'
BIKE_LEG = 'b'
T2_LEG = 't2'
RUN_LEG = 'r'
FINISH_LEG = 'f'


def build_stats(total, success, male, female):
    success_percent = 100. * success / total
    return {
        't': total,
        's': success,
        'p': f'{success_percent:.1f}',
        'm': male,
        'f': female
    }


def build_location_info(country_iso, continent, country, state, city):
    return {
        'country_iso': country_iso,
        'continent': continent,
        'country': country,
        'state': state,
        'city': city,
    }


def build_distance_info(total_distance, swim_type, bike_type, run_type):
    return {
        'td': total_distance,
        'st': swim_type,
        'bt': bike_type,
        'rt': run_type,
    }


def build_race_info(name, date, brand, tri_type, location_info, distance_info, stats):
    return {
        'name': name,
        'date': date,
        'brand': brand,
        'type': tri_type,
        'location': location_info,
        'distance': distance_info,
        'stats': stats
    }


def build_athlete_result(athlete_id, athlete_name, country_fifa_code, bib, status, age_group, age_group_size, gender, gender_size, overall_size, legs):
    assert len(legs) == 6

    inner_legs = {
        leg: legs[leg] for leg in [SWIM_LEG, T1_LEG, BIKE_LEG, T2_LEG, RUN_LEG]
    }

    return {
        'id': athlete_id,
        'n': athlete_name,
        'c': country_fifa_code,
        'b': bib,
        'st': status,

        't': legs[FINISH_LEG]['t'],

        'a': age_group,
        'as': age_group_size,
        'ar': legs[FINISH_LEG]['ar'],
        'tar': _format_float(legs[FINISH_LEG]['tar']),

        'g': gender,
        'gs': gender_size,
        'gr': legs[FINISH_LEG]['gr'],
        'tgr': _format_float(legs[FINISH_LEG]['tgr']),

        'os': overall_size,
        'or': legs[FINISH_LEG]['or'],
        'tor': _format_float(legs[FINISH_LEG]['tor']),

        'legs': inner_legs,
    }


def build_leg(time, age_rank, gender_rank, overall_rank, time_age_rank, time_gender_rank, time_overall_rank):
    return {
        't': time,
        'ar': age_rank,
        'gr': gender_rank,
        'or': overall_rank,
        'tar': _format_float(time_age_rank),
        'tgr': _format_float(time_gender_rank),
        'tor': _format_float(time_overall_rank)
    }


def _format_float(f):
    return round(f, FLOAT_DECIMALS)
