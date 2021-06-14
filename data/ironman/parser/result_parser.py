from base import log
from data.ironman.parser.constants import *


logger = log.setup_logger(__file__)


def get_age_group(result):
    return result['AgeGroup']


def get_gender(result, default='M'):
    contact = result['Contact']
    if not contact:
        return default

    gender = contact['Gender']
    if not gender:
        return default

    return gender


def is_male(result):
    return get_gender(result) == GENDER_MALE


def is_female(result):
    return get_gender(result) == GENDER_FEMALE


def get_athlete_name(result, default=''):
    if not result['Contact']:
        return default
    return result['Contact']['FullName']


def get_country_representing_iso_numeric(result):
    return result["CountryRepresentingISONumeric"]


def get_contact_id(result):
    return result['ContactId']


def get_finish_status(result, log=False):
    finish_time = get_leg_time(result, FINISH_LEG)
    if finish_time > 0 and finish_time < IRONMAN_NOT_FINISHED_TIME:
        return EVENT_STATUS_FINISH

    event_status = result['EventStatus']
    if event_status and event_status != EVENT_STATUS_FINISH:
        return event_status

    if log:
        logger.warning(
            f'event status: {event_status} for time: {finish_time}: set as {EVENT_STATUS_DNF}')
    return EVENT_STATUS_DNF


def get_bib_number(result):
    return result['BibNumber']


def is_finished(result):
    return get_finish_status(result) == EVENT_STATUS_FINISH


def get_leg_time(result, leg):
    return result[f'{leg}Time']
