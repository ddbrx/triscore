import re
from base import log

logger = log.setup_logger(__file__)


FINISH_STATUS_DQ = 'DQ'
FINISH_STATUS_DNS = 'DNS'
FINISH_STATUS_DNF = 'DNF'
FINISH_STATUS_OK = 'ok'

MAX_TIME = 99999

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
        'p': f'{success_percent:5.1f}',
        'm': male,
        'f': female
    }


def build_location_info(description, country):
    def get_or_empty(field):
        return country[field] if country else ''

    location_info = {
        'd': description
    }

    location_info['ct'] = get_or_empty('continent_name')
    location_info['cy'] = get_or_empty('name')
    location_info['c'] = get_or_empty('fifa')

    return location_info


def build_distance_info(swim_distance, swim_type, swim_elevation, bike_distance, bike_score, bike_elevation, run_distance, run_score, run_elevation):
    return {
        SWIM_LEG: {
            'd': swim_distance,
            't': swim_type,
            'e': swim_elevation
        },
        BIKE_LEG: {
            'd': bike_distance,
            's': bike_score,
            'e': bike_elevation
        },
        RUN_LEG: {
            'd': run_distance,
            's': run_score,
            'e': run_elevation
        }
    }


def build_race_info(name, date, location_info, brand, tri_type,  distance_info, stats):
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

        'g': gender,
        'gs': gender_size,
        'gr': legs[FINISH_LEG]['gr'],

        'os': overall_size,
        'or': legs[FINISH_LEG]['or'],

        'legs': inner_legs,
    }


def build_leg(time, age_rank, gender_rank, overall_rank):
    return {
        't': time,
        'ar': age_rank,
        'gr': gender_rank,
        'or': overall_rank
    }
