import unidecode
from base import log

logger = log.setup_logger(__file__)


IRONMAN_BRAND = 'IRONMAN'

EVENT_STATUS_DQ = 'DQ'
EVENT_STATUS_DNS = 'DNS'
EVENT_STATUS_DNF = 'DNF'
EVENT_STATUS_FINISH = 'Finish'

GENDER_MALE = 'M'
GENDER_FEMALE = 'F'

SWIM_LEG = 'Swim'
T1_LEG = 'Transition1'
BIKE_LEG = 'Bike'
T2_LEG = 'Transition2'
RUN_LEG = 'Run'
FINISH_LEG = 'Finish'

VR_HALFS = ['VR1']

LEG_NAMES = [SWIM_LEG, T1_LEG, BIKE_LEG, T2_LEG, RUN_LEG, FINISH_LEG]


def get_event_name_replaced(race):
    sub_event = unidecode.unidecode(race['SubEvent'])
    space_replace_items = ['/', ': Triathlon']
    for item in space_replace_items:
        sub_event = sub_event.replace(item, ' ')

    return ' '.join(sub_event.strip().split())


def get_event_name(race):
    return race['Event']


def get_subevent_name(race):
    return race['SubEvent']


def get_subevent_id(race):
    return race['SubEventId']


def get_subevent_type(race):
    return race['SubEventType']


def get_event_date(race):
    return race['Date']


def get_event_brand(race):
    return race['Brand']


def get_results(race):
    return race['data']


def get_age_group(result):
    return result['AgeGroup']


def get_gender(result):
    gender_or_none = result['Contact']['Gender']
    return gender_or_none if gender_or_none else 'M'


def is_male(result):
    return get_gender(result) == GENDER_MALE


def is_female(result):
    return get_gender(result) == GENDER_FEMALE


def get_athlete_name(result):
    return result['Contact']['FullName']


def get_country_iso2(result):
    return result['Country']['ISO2']


def get_contact_id(result):
    return result['ContactId']


def get_finish_status(result, log=False):
    finish_time = get_leg_time(result, FINISH_LEG)
    if finish_time > 0 and finish_time < 99999:
        return EVENT_STATUS_FINISH

    event_status = result['EventStatus']
    if event_status and event_status != EVENT_STATUS_FINISH:
        return event_status

    if log:
        logger.warning(
            f'event status: {event_status} for time: {finish_time}: set as {EVENT_STATUS_DNF}')
    return EVENT_STATUS_DNF


def get_race_year(race_full_name):
    return race_full_name.split()[0]


def is_ironman_series(race_full_name):
    return race_full_name.find(IRONMAN_BRAND) != -1


def get_race_name_no_year(race_full_name):
    brand_index = race_full_name.find(IRONMAN_BRAND)
    assert brand_index != -1, f'ironman brand not found: {race_full_name}'
    return race_full_name[brand_index:]


def get_race_tri_type(race_name):
    assert race_name.find(IRONMAN_BRAND) != -1, f'not an ironman: {race_name}'

    for vr_halfs in VR_HALFS:
        if race_name.find(vr_halfs) != -1:
            return 'vr-half'

    if race_name.find('5150') != -1 or race_name.find('5i50') != -1:
        return 'olympic'
    elif race_name.find('70.3') != -1:
        return 'half'
    else:
        return 'full'


def get_race_tri_tag(race_name):
    race_tri_type = get_race_tri_type(race_name)
    if race_tri_type == 'olympic':
        return '5150'
    elif race_tri_type == 'half':
        return '70.3'
    else:
        return ''


def get_bib_number(result):
    return result['BibNumber']


def is_finished(result):
    return get_finish_status(result) == EVENT_STATUS_FINISH


def get_leg_time(result, leg):
    return result[f'{leg}Time']
