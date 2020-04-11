#!/usr/bin/env python3
from decimal import *
import json
from operator import itemgetter
import re
import unidecode

from base import log, utils, translit
from base.location.resolver import LocationResolver

from data.storage import DataStorage
from obstri_matcher import ObstriMatcher
import parser
from race import builder
from race.storage import RaceStorage

logger = log.setup_logger(__file__, debug=False)

country_resolver = LocationResolver()

IRONMAN_EVENT_STATUS_TO_TRISCORE = {
    parser.EVENT_STATUS_DQ: builder.FINISH_STATUS_DQ,
    parser.EVENT_STATUS_DNS: builder.FINISH_STATUS_DNS,
    parser.EVENT_STATUS_DNF: builder.FINISH_STATUS_DNF,
    parser.EVENT_STATUS_FINISH: builder.FINISH_STATUS_OK
}

LEG_IRONMAN_TO_TRISCORE = {
    parser.SWIM_LEG: builder.SWIM_LEG,
    parser.T1_LEG: builder.T1_LEG,
    parser.BIKE_LEG: builder.BIKE_LEG,
    parser.T2_LEG: builder.T2_LEG,
    parser.RUN_LEG: builder.RUN_LEG,
    parser.FINISH_LEG: builder.FINISH_LEG
}


def get_sorted_results(race_results, sort_by):
    return sorted(race_results, key=lambda result: result[sort_by])


def get_stats(race_results):
    total_count = len(race_results)
    success_count = 0
    male_count = 0
    female_count = 0
    for race_result in race_results:
        success_count += parser.is_finished(race_result)
        male_count += parser.is_male(race_result)
        female_count += parser.is_female(race_result)

    return builder.build_stats(
        total=total_count,
        success=success_count,
        male=male_count,
        female=female_count)


def get_ranks_by_legs(race_results, count_by_age_group, count_by_gender):
    age_rank = {}
    gender_rank = {}
    overall_rank = {}

    time_age_rank = {}
    time_gender_rank = {}
    time_overall_rank = {}

    LAST_EQUAL_RANK = '__last_equal_rank'
    LAST_RANK = '__last_rank'
    LAST_TIME = '__last_time'
    total_count = len(race_results)

    for leg in parser.LEG_NAMES:
        min_leg_time = {}
        max_leg_time = {}

        age_rank[leg] = {}
        gender_rank[leg] = {}
        overall_rank[leg] = {}

        logger.debug(f'========= LEG: {leg}')

        last_leg_time = 0
        for i, race_result in enumerate(get_sorted_results(race_results, sort_by=f'{leg}Time')):
            age = parser.get_age_group(race_result)
            gender = parser.get_gender(race_result)
            contact_id = parser.get_contact_id(race_result)
            leg_time = parser.get_leg_time(race_result, leg)
            athlete_name = parser.get_athlete_name(race_result)

            if age not in min_leg_time:
                min_leg_time[age] = builder.MAX_TIME
                max_leg_time[age] = 0

            if gender not in min_leg_time:
                min_leg_time[gender] = builder.MAX_TIME
                max_leg_time[gender] = 0

            if 'overall' not in min_leg_time:
                min_leg_time['overall'] = builder.MAX_TIME
                max_leg_time['overall'] = 0

            min_leg_time[age] = min(min_leg_time[age], leg_time)
            min_leg_time[gender] = min(min_leg_time[gender], leg_time)
            min_leg_time['overall'] = min(min_leg_time['overall'], leg_time)

            assert leg_time >= last_leg_time, f'descending leg time: {leg_time} last: {last_leg_time} result: {race_result}'

            if leg_time != builder.MAX_TIME:
                max_leg_time[age] = max(max_leg_time[age], leg_time)
                max_leg_time[gender] = max(max_leg_time[gender], leg_time)
                max_leg_time['overall'] = max(
                    max_leg_time['overall'], leg_time)

                age_time_key = age + LAST_TIME
                age_rank_key = age + LAST_RANK
                age_equal_rank_key = age + LAST_EQUAL_RANK
                if age_time_key not in age_rank[leg]:
                    age_rank[leg][age_time_key] = 0
                    age_rank[leg][age_rank_key] = 0
                    age_rank[leg][age_equal_rank_key] = 1

                gender_time_key = gender + LAST_TIME
                gender_rank_key = gender + LAST_RANK
                gender_equal_rank_key = gender + LAST_EQUAL_RANK
                if gender_time_key not in gender_rank[leg]:
                    gender_rank[leg][gender_time_key] = 0
                    gender_rank[leg][gender_rank_key] = 0
                    gender_rank[leg][gender_equal_rank_key] = 1

                overall_time_key = 'overall' + LAST_TIME
                overall_rank_key = 'overall' + LAST_RANK
                overall_equal_rank_key = 'overall' + LAST_EQUAL_RANK
                if overall_time_key not in overall_rank[leg]:
                    overall_rank[leg][overall_time_key] = 0
                    overall_rank[leg][overall_rank_key] = 0
                    overall_rank[leg][overall_equal_rank_key] = 1

                if leg_time > age_rank[leg][age_time_key]:
                    age_rank[leg][age_rank_key] += age_rank[leg][age_equal_rank_key]
                    age_rank[leg][age_time_key] = leg_time
                    age_rank[leg][age_equal_rank_key] = 1
                elif leg_time == age_rank[leg][age_time_key]:
                    age_rank[leg][age_equal_rank_key] += 1

                if leg_time > gender_rank[leg][gender_time_key]:
                    gender_rank[leg][gender_rank_key] += gender_rank[leg][gender_equal_rank_key]
                    gender_rank[leg][gender_time_key] = leg_time
                    gender_rank[leg][gender_equal_rank_key] = 1
                elif leg_time == gender_rank[leg][gender_time_key]:
                    gender_rank[leg][gender_equal_rank_key] += 1

                if leg_time > overall_rank[leg][overall_time_key]:
                    overall_rank[leg][overall_rank_key] += overall_rank[leg][overall_equal_rank_key]
                    overall_rank[leg][overall_time_key] = leg_time
                    overall_rank[leg][overall_equal_rank_key] = 1
                elif leg_time == overall_rank[leg][overall_time_key]:
                    overall_rank[leg][overall_equal_rank_key] += 1

                age_rank[leg][contact_id] = age_rank[leg][age_rank_key]
                gender_rank[leg][contact_id] = gender_rank[leg][gender_rank_key]
                overall_rank[leg][contact_id] = overall_rank[leg][overall_rank_key]
            else:
                age_rank[leg][contact_id] = count_by_age_group[age]
                gender_rank[leg][contact_id] = count_by_gender[gender]
                overall_rank[leg][contact_id] = total_count

            last_leg_time = leg_time

        time_age_rank[leg] = {}
        time_gender_rank[leg] = {}
        time_overall_rank[leg] = {}

        for race_result in race_results:
            age = parser.get_age_group(race_result)
            gender = parser.get_gender(race_result)
            contact_id = parser.get_contact_id(race_result)
            leg_time = parser.get_leg_time(race_result, leg)
            if leg_time != builder.MAX_TIME:
                time_age_rank[leg][contact_id] = 1.
                min_age_time = min_leg_time[age]
                max_age_time = max_leg_time[age]
                assert max_age_time != 0, f'invalid max_age_time: {max_age_time}'
                if min_age_time != max_age_time:
                    time_age_rank[leg][contact_id] += \
                        1. * (count_by_age_group[age] - 1) * \
                        (leg_time - min_age_time) / \
                        (max_age_time - min_age_time)

                time_gender_rank[leg][contact_id] = 1.
                min_gender_time = min_leg_time[gender]
                max_gender_time = max_leg_time[gender]
                assert max_gender_time != 0, f'invalid max_gender_time: {max_gender_time}'
                if min_gender_time != max_gender_time:
                    time_gender_rank[leg][contact_id] += \
                        1. * (count_by_gender[gender] - 1) * \
                        (leg_time - min_gender_time) / \
                        (max_gender_time - min_gender_time)

                time_overall_rank[leg][contact_id] = 1.
                min_overall_time = min_leg_time['overall']
                max_overall_time = max_leg_time['overall']
                assert max_overall_time != 0, f'invalid max_overall_time: {max_overall_time}'
                if min_overall_time != max_overall_time:
                    time_overall_rank[leg][contact_id] += \
                        1. * (total_count - 1) * \
                        (leg_time - min_overall_time) / \
                        (max_overall_time - min_overall_time)
            else:
                time_age_rank[leg][contact_id] = count_by_age_group[age]
                time_gender_rank[leg][contact_id] = count_by_gender[gender]
                time_overall_rank[leg][contact_id] = total_count

    return age_rank, gender_rank, overall_rank, time_age_rank, time_gender_rank, time_overall_rank


def filter_result_duplicates(race_results):
    last_contact_id = ''
    filtered_race_results = []
    for race_result in sorted(race_results, key=lambda result: (result['ContactId'], -result['FinishTime'])):
        contact_id = parser.get_contact_id(race_result)
        if contact_id == last_contact_id:
            logger.debug(
                f'filter duplicated result {race_result}')
        else:
            filtered_race_results.append(race_result)

        last_contact_id = contact_id

    duplicates_filtered = len(race_results) - len(filtered_race_results)
    logger.info(f'filtered {duplicates_filtered} result duplicates')
    return filtered_race_results


def fix_undefined_times(race_results):
    for race_result in race_results:
        for leg in parser.LEG_NAMES:
            athlete_name = parser.get_athlete_name(race_result)
            leg_finish_time = int(parser.get_leg_time(race_result, leg))

            set_finish_time_as_max = False
            if leg == parser.FINISH_LEG:
                finish_status = parser.get_finish_status(race_result)
                set_finish_time_as_max = finish_status != parser.EVENT_STATUS_FINISH

            if set_finish_time_as_max or \
                    leg_finish_time <= 0 or \
                    leg_finish_time > builder.MAX_TIME:
                leg_field = f'{leg}Time'
                logger.debug(
                    f'Fix {athlete_name} {leg_field} '
                    f'from {leg_finish_time} to {builder.MAX_TIME}: {race_result}')
                race_result[leg_field] = builder.MAX_TIME
    return race_results


def publish_ironman_data(start_index, limit, dry_run):
    ironman_data = DataStorage(collection_name='ironman', indices=['SubEvent'])
    race_storage = RaceStorage()

    obstri_matcher = ObstriMatcher()

    ironman_races = ironman_data.find(
        sort=[('SubEvent', 1)], skip=start_index, limit=limit)
    count = ironman_races.count()

    obstri_not_matched_races = []
    max_count = -1
    for i, race in enumerate(ironman_races):
        if i == max_count:
            logger.info(f'stopping by max count: {max_count}')
            break

        race_full_name = parser.get_event_name(race)

        logger.info(
            f'{start_index + i + 1}/{count}: process race {race_full_name}')

        if parser.is_invalid_race(race):
            logger.info(f'skip invalid race: {race_full_name}')
            continue

        if not parser.is_ironman_series(race_full_name):
            logger.info(f'skip not ironman series race: {race_full_name}')
            continue

        obstri_race = obstri_matcher.find_race(race_full_name)
        if not obstri_race:
            logger.warning(
                f'No obstri race found: SKIP RACE {race_full_name}')
            obstri_not_matched_races.append(race_full_name)
            continue

        race_date = obstri_race['d']
        race_name_no_year = parser.get_race_name_no_year(race_full_name)

        race_results = parser.get_results(race)
        race_results = filter_result_duplicates(race_results)
        race_results = fix_undefined_times(race_results)

        if race_storage.has_race(name=race_name_no_year, date=race_date):
            race_written_length = race_storage.get_race_length(
                name=race_name_no_year, date=race_date)
            race_new_length = len(race_results)

            if race_new_length != race_written_length:
                logger.info(
                    f'drop existing collection for race {race_full_name}'
                    f' race_new_length: {race_new_length}'
                    f' race_written_length: {race_written_length}')
                race_storage.remove_race(
                    name=race_name_no_year, date=race_date)
            else:
                logger.warning(
                    f'skip adding race {race_full_name}: collection exist')
                continue

        race_location_full_name = ''
        race_distance_info = {}
        obstri_info_race = obstri_matcher.find_race_info(obstri_race)
        if obstri_info_race:
            race_location_full_name = obstri_info_race['c']
            obstri_race_info_str = obstri_info_race['info'] if 'info' in obstri_info_race else None
            if obstri_race_info_str:
                obstri_race_info = json.loads(obstri_race_info_str)
                race_distance_info = builder.build_distance_info(
                    swim_distance=obstri_race_info['swim']['distance'],
                    swim_type=obstri_race_info['swim']['type'],
                    swim_elevation=obstri_race_info['swim']['elevationGain'],
                    bike_distance=obstri_race_info['bike']['distance'],
                    bike_score=obstri_race_info['bike']['score'],
                    bike_elevation=obstri_race_info['bike']['elevationGain'],
                    run_distance=obstri_race_info['run']['distance'],
                    run_score=obstri_race_info['run']['score'],
                    run_elevation=obstri_race_info['run']['elevationGain']
                )
        else:
            logger.warning(
                f'No obstri info race found race: {race_full_name}')

        race_location_desc = race_location_full_name.split(',')[-1].strip()
        race_country = country_resolver.try_to_deduce_country(
            race_location_desc)
        race_location_info = builder.build_location_info(
            description=race_location_full_name, country=race_country)

        # Stats
        stats = get_stats(race_results)

        # Race info
        race_tri_type = parser.get_race_tri_type(race_full_name)
        race_info = builder.build_race_info(
            name=race_name_no_year,
            date=race_date,
            location_info=race_location_info,
            brand=parser.IRONMAN_BRAND,
            tri_type=race_tri_type,
            stats=stats,
            distance_info=race_distance_info)

        # Rank by leg
        count_by_age_group = {}
        for race_result in race_results:
            age_group = parser.get_age_group(race_result)
            if age_group not in count_by_age_group:
                count_by_age_group[age_group] = 0
            count_by_age_group[age_group] += 1

        count_by_gender = {}
        for race_result in race_results:
            gender = parser.get_gender(race_result)
            if gender not in count_by_gender:
                count_by_gender[gender] = 0
            count_by_gender[gender] += 1

        age_rank, gender_rank, overall_rank, time_age_rank, time_gender_rank, time_overall_rank = \
            get_ranks_by_legs(
                race_results, count_by_age_group, count_by_gender)

        def get_legs(race_result):
            legs = {}
            for ironman_leg_name in parser.LEG_NAMES:
                triscore_leg_name = LEG_IRONMAN_TO_TRISCORE[ironman_leg_name]
                contact_id = parser.get_contact_id(race_result)
                legs[triscore_leg_name] = builder.build_leg(
                    time=parser.get_leg_time(race_result, ironman_leg_name),
                    age_rank=age_rank[ironman_leg_name][contact_id],
                    gender_rank=gender_rank[ironman_leg_name][contact_id],
                    overall_rank=overall_rank[ironman_leg_name][contact_id],
                    time_age_rank=time_age_rank[ironman_leg_name][contact_id],
                    time_gender_rank=time_gender_rank[ironman_leg_name][contact_id],
                    time_overall_rank=time_overall_rank[ironman_leg_name][contact_id],
                )
            return legs

        # Construct athlete results
        athlete_results = []
        last_finish_time = 0
        last_finish_rank = 0
        for i, result in enumerate(
            sorted(race_results,
                   key=lambda result: (
                       result['FinishTime'],
                       result['SwimTime'],
                       result['Transition1Time'],
                       result['BikeTime'],
                       result['Transition2Time'],
                       result['RunTime']))):
            country_iso2_code = parser.get_country_iso2(result)
            country = country_resolver.get_country_by_iso2_code_or_none(
                country_iso2_code)
            country_fifa_code = country['fifa'] if country else ''

            athlete_id = parser.get_contact_id(result)
            bib = parser.get_bib_number(result)

            age_group = parser.get_age_group(result)
            age_group_size = count_by_age_group[age_group]

            gender = parser.get_gender(result)
            gender_size = count_by_gender[gender]

            overall_size = len(race_results)

            finish_status = parser.get_finish_status(result, log=True)
            status = IRONMAN_EVENT_STATUS_TO_TRISCORE[finish_status]

            legs = get_legs(result)
            finish_time = legs[builder.FINISH_LEG]['t']

            athlete_name = parser.get_athlete_name(result)
            finish_rank = legs[builder.FINISH_LEG]['or']

            assert finish_time >= last_finish_time, \
                f'descending finish time: {finish_time} last: {last_finish_time}\nresult: {result}\nathlete: {athlete_result}'

            assert finish_rank >= last_finish_rank, \
                f'descending finish rank: {finish_rank} last: {last_finish_rank}\nresult: {result}\nathlete: {athlete_result}'

            athlete_result = builder.build_athlete_result(
                athlete_id=athlete_id,
                athlete_name=athlete_name,
                country_fifa_code=country_fifa_code,
                bib=bib,
                age_group=age_group,
                age_group_size=age_group_size,
                gender=gender,
                gender_size=gender_size,
                overall_size=overall_size,
                status=status,
                legs=legs)
            athlete_results.append(athlete_result)

            last_finish_time = finish_time
            last_finish_rank = finish_rank

        if dry_run:
            logger.info(
                f'DRY_RUN: skip adding race: {race_info} results: {len(athlete_results)}')
        else:
            assert race_storage.add_race(
                race_info, athlete_results), f'failed to add race: {race_info}'

    logger.info(f'obstri not matched {len(obstri_not_matched_races)} races')
    for i, race in enumerate(obstri_not_matched_races):
        logger.info(f'{i + 1}: {race}')


def main():
    start_index = 0
    limit = 0
    dry_run = False

    publish_ironman_data(start_index, limit, dry_run)


if __name__ == '__main__':
    main()
