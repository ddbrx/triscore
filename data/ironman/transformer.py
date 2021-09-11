#!/usr/bin/env python3
from argparse import ArgumentParser
from base import dt, log
from base.location.resolver import LocationResolver
from data.storage import DataStorage
from data.ironman.parser import constants, race_parser, result_parser
from decimal import *
from pymongo import MongoClient
from race import builder
from race.storage import RaceStorage


logger = log.setup_logger(__file__, debug=False)

country_resolver = LocationResolver()

IRONMAN_EVENT_STATUS_TO_TRISCORE = {
    constants.EVENT_STATUS_DQ: builder.FINISH_STATUS_DQ,
    constants.EVENT_STATUS_DNS: builder.FINISH_STATUS_DNS,
    constants.EVENT_STATUS_DNF: builder.FINISH_STATUS_DNF,
    constants.EVENT_STATUS_FINISH: builder.FINISH_STATUS_OK
}

LEG_IRONMAN_TO_TRISCORE = {
    constants.SWIM_LEG: builder.SWIM_LEG,
    constants.T1_LEG: builder.T1_LEG,
    constants.BIKE_LEG: builder.BIKE_LEG,
    constants.T2_LEG: builder.T2_LEG,
    constants.RUN_LEG: builder.RUN_LEG,
    constants.FINISH_LEG: builder.FINISH_LEG
}


def get_location_info(race):
    country_iso_num = race_parser.get_country_iso_numeric(race)
    continent = race_parser.get_continent(race)
    country = race_parser.get_country(race)
    state = race_parser.get_state_or_province(race)
    city = race_parser.get_city(race)
    return builder.build_location_info(country_iso_num, continent, country, state, city)


def get_distance_info(race):
    total_distance = race_parser.get_distance_in_km(race)
    if total_distance is None:
        total_distance = race_parser.get_distance_by_tri_type(race)

    swim_type = race_parser.get_swim_type(race)
    bike_type = race_parser.get_bike_type(race)
    run_type = race_parser.get_run_type(race)
    return builder.build_distance_info(total_distance, swim_type, bike_type, run_type)


def get_sorted_results(race_results, sort_by):
    return sorted(race_results, key=lambda result: result[sort_by])


def get_stats(race_results):
    total_count = len(race_results)
    success_count = 0
    male_count = 0
    female_count = 0
    for race_result in race_results:
        success_count += result_parser.is_finished(race_result)
        male_count += result_parser.is_male(race_result)
        female_count += result_parser.is_female(race_result)

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

    for leg in constants.LEG_NAMES:
        min_leg_time = {}
        max_leg_time = {}

        age_rank[leg] = {}
        gender_rank[leg] = {}
        overall_rank[leg] = {}

        logger.debug(f'========= LEG: {leg}')

        last_leg_time = 0
        for race_result in get_sorted_results(race_results, sort_by=f'{leg}Time'):
            age = result_parser.get_age_group(race_result)
            gender = result_parser.get_gender(race_result)
            contact_id = result_parser.get_contact_id(race_result)
            leg_time = result_parser.get_leg_time(race_result, leg)

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
            age = result_parser.get_age_group(race_result)
            gender = result_parser.get_gender(race_result)
            contact_id = result_parser.get_contact_id(race_result)
            leg_time = result_parser.get_leg_time(race_result, leg)
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
        contact_id = result_parser.get_contact_id(race_result)
        if contact_id == last_contact_id:
            logger.debug(
                f'filter duplicated result {race_result}')
        else:
            filtered_race_results.append(race_result)

        last_contact_id = contact_id

    duplicates_filtered = len(race_results) - len(filtered_race_results)
    logger.debug(f'filtered {duplicates_filtered} result duplicates')
    return filtered_race_results


def fix_undefined_times(race_results):
    for race_result in race_results:
        logger.debug(race_result)
        athlete_name = result_parser.get_athlete_name(race_result)

        for leg in constants.LEG_NAMES:
            leg_finish_time = int(result_parser.get_leg_time(race_result, leg))

            set_finish_time_as_max = False
            if leg == constants.FINISH_LEG:
                finish_status = result_parser.get_finish_status(race_result)
                set_finish_time_as_max = finish_status != constants.EVENT_STATUS_FINISH

            if set_finish_time_as_max or \
                    leg_finish_time <= 0 or \
                    leg_finish_time > builder.MAX_TIME:
                leg_field = f'{leg}Time'
                logger.debug(
                    f'Fix athlete: {athlete_name} leg: {leg_field} '
                    f'from {leg_finish_time} to {builder.MAX_TIME}: {race_result}')
                race_result[leg_field] = builder.MAX_TIME
    return race_results


def transform_ironman_to_triscore(mongo_client, limit, dry_run):
    ironman_races_storage = DataStorage(mongo_client=mongo_client, db_name='ironman', collection_name='races')

    triscore_storage = RaceStorage(mongo_client=mongo_client, db_name='triscore', create_indices=True)

    ironman_races = ironman_races_storage.find(
        where={DataStorage.INVALID_FIELD: False, DataStorage.PROCESSED_FIELD: True},
        sort=[('Date', 1)],
        limit=limit)
    count = ironman_races.count()

    logger.info(f'{count} new races found')

    max_count = -1
    for i, race in enumerate(ironman_races):
        if i == max_count:
            logger.info(f'stopping by max count: {max_count}')
            break

        race_series = race_parser.get_series(race)
        race_date = race_parser.get_date(race)

        if triscore_storage.race_processed(race_series, race_date):
            logger.info(f'skip processed race {race_series} {race_date}')
            continue

        subevent_id = race_parser.get_subevent_id(race)

        logger.info(
            f'{i + 1}/{count} process race series: {race_series} date: {race_date} id: {subevent_id}')

        race_results_storage = DataStorage(mongo_client=mongo_client, db_name='ironman', collection_name=subevent_id)
        race_results = list(race_results_storage.find())
        race_results = filter_result_duplicates(race_results)
        race_results = fix_undefined_times(race_results)

        if triscore_storage.has_race(name=race_series, date=race_date):
            race_written_length = triscore_storage.get_race_length(name=race_series, date=race_date)
            race_new_length = len(race_results)

            logger.warning(
                f'drop existing collection for'
                f' race series: {race_series}'
                f' date: {race_date}'
                f' race_written_length: {race_written_length}'
                f' race_new_length: {race_new_length}')
            triscore_storage.remove_race(name=race_series, date=race_date)

        # Race info
        location_info = get_location_info(race)
        distance_info = get_distance_info(race)
        race_stats = get_stats(race_results)

        race_info = builder.build_race_info(
            name=race_series,
            date=race_date,
            brand=constants.IRONMAN_BRAND,
            tri_type=race_parser.get_tri_type(race),
            location_info=location_info,
            distance_info=distance_info,
            stats=race_stats)
        logger.debug(f'info: {race_info}')


        # Rank by leg
        count_by_age_group = {}
        for race_result in race_results:
            age_group = result_parser.get_age_group(race_result)
            if age_group not in count_by_age_group:
                count_by_age_group[age_group] = 0
            count_by_age_group[age_group] += 1

        count_by_gender = {}
        for race_result in race_results:
            gender = result_parser.get_gender(race_result)
            if gender not in count_by_gender:
                count_by_gender[gender] = 0
            count_by_gender[gender] += 1

        age_rank, gender_rank, overall_rank, time_age_rank, time_gender_rank, time_overall_rank = \
            get_ranks_by_legs(
                race_results, count_by_age_group, count_by_gender)

        def get_legs(race_result):
            legs = {}
            for ironman_leg_name in constants.LEG_NAMES:
                triscore_leg_name = LEG_IRONMAN_TO_TRISCORE[ironman_leg_name]
                contact_id = result_parser.get_contact_id(race_result)
                legs[triscore_leg_name] = builder.build_leg(
                    time=result_parser.get_leg_time(race_result, ironman_leg_name),
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
            athlete_id = result_parser.get_contact_id(result)
            athlete_name = result_parser.get_athlete_name(result)
            country_iso_num = result_parser.get_country_representing_iso_numeric(result)
            bib = result_parser.get_bib_number(result)
            age_group = result_parser.get_age_group(result)
            age_group_size = count_by_age_group[age_group]
            gender = result_parser.get_gender(result)
            gender_size = count_by_gender[gender]
            overall_size = len(race_results)
            finish_status = result_parser.get_finish_status(result, log=True)
            status = IRONMAN_EVENT_STATUS_TO_TRISCORE[finish_status]

            legs = get_legs(result)
            finish_time = legs[builder.FINISH_LEG]['t']
            finish_rank = legs[builder.FINISH_LEG]['or']

            assert finish_time >= last_finish_time, \
                f'descending finish time: {finish_time} last: {last_finish_time}\nresult: {result}\nathlete: {athlete_result}'

            assert finish_rank >= last_finish_rank, \
                f'descending finish rank: {finish_rank} last: {last_finish_rank}\nresult: {result}\nathlete: {athlete_result}'

            athlete_result = builder.build_athlete_result(
                athlete_id=athlete_id,
                athlete_name=athlete_name,
                country_iso_num=country_iso_num,
                bib=bib,
                age_group=age_group,
                age_group_size=age_group_size,
                gender=gender,
                gender_size=gender_size,
                overall_size=overall_size,
                status=status,
                legs=legs)
            logger.debug(f'result: {athlete_result}')
            athlete_results.append(athlete_result)

            last_finish_time = finish_time
            last_finish_rank = finish_rank

        if dry_run:
            logger.info(
                f'DRY_RUN: skip adding race: {race_info} results: {len(athlete_results)}')
        else:
            assert triscore_storage.add_race(
                race_info, athlete_results), f'failed to add race: {race_info}'


def main():
    parser = ArgumentParser()
    parser.add_argument('-d', '--database', default='triscore')
    parser.add_argument('-u', '--username', default='triscore-writer')
    parser.add_argument('-p', '--password', required=True)
    parser.add_argument('-l', '--limit', type=int, default=0)
    parser.add_argument('-t', '--timeout', type=int, default=None)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()

    mongo_client = MongoClient(username=args.username, password=args.password, authSource=args.database)

    while True:
        transform_ironman_to_triscore(mongo_client, args.limit, args.dry_run)
        if not dt.wait(args.timeout):
            break


if __name__ == '__main__':
    main()
