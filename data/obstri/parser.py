import unidecode
from base import log

logger = log.setup_logger(__file__)


EVENT_STATUS_DQ = 'DQ'
EVENT_STATUS_DNS = 'DNS'
EVENT_STATUS_DNF = 'DNF'
EVENT_STATUS_FINISH = 'Finish'


def get_race_id_name(race):
    return race['r']


def get_race_full_name(race):
    return race['rn']


def get_race_date(race):
    return race['d']


def get_race_year(race):
    return race['y']


def get_race_results(race):
    return race['data']
