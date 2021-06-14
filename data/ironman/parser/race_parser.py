from base import log
from data.ironman.parser.constants import *


logger = log.setup_logger(__file__)


def get_event_name(race):
    return race['Event']


def get_subevent_name(race):
    return race['SubEvent']


def get_subevent_id(race):
    return race['SubEventId']


def get_subevent_type(race):
    return race['SubEventType']


def get_date(race):
    return race['Date']


def get_brand(race):
    return race['Brand']


def get_series(race):
    return race['Series']


def get_country_iso_numeric(race):
    return race["CountryISONumeric"]


def get_continent(race):
    return race["Continent"]


def get_country(race):
    return race["Country"]


def get_state_or_province(race):
    return race["StateOrProvince"]


def get_city(race):
    return race["City"]


def get_distance_in_km(race):
    return race['DistanceInKM']


def get_swim_type(race):
    return race['Swim']


def get_bike_type(race):
    return race['Bike']


def get_run_type(race):
    return race['Run']


def get_tri_type(race):
    race_brand = get_brand(race)

    if race_brand.find('5150') != -1 or race_brand.find('5i50') != -1:
        return TRI_TYPE_OLYMPIC
    elif race_brand.find('70.3') != -1:
        return TRI_TYPE_HALF
    else:
        return TRI_TYPE_FULL


def get_distance_by_tri_type(race):
    tri_type = get_tri_type(race)
    return TRI_TYPE_TO_DISTANCE[tri_type]
