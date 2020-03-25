#!/usr/bin/env python3
import json
import os

from base import log, utils
import race.parser as race_parser
from race.api import RaceApi
from score.api import ScoreApi, MockScoreApi
import distribution

logger = log.setup_logger(__file__)

TRISCORE_DB = 'triscore-test'
START_RATING = 1500

race_api = RaceApi()
# score_api = ScoreApi()
score_api = MockScoreApi()


def process_race(race):
    results_by_group = get_results_by_group(race)
    for group, results in results_by_group.items():
        process_group(group, results, race)


def get_results_by_group(race):
    results_by_group = {}

    race_country = race_parser.get_race_country(race)
    race_results = race_parser.get_race_results(race)
    race_parser.fix_profile_country(race_results, race_country)

    for result in race_results:
        group = race_parser.get_group(result)
        if group not in results_by_group:
            results_by_group[group] = []
        results_by_group[group].append(result)
    return results_by_group


def process_group(group, results, race):
    group_size = len(results)
    assert group_size > 0, 'emptry group: {group}'

    # logger.info(f'process group: {group} size: {group_size}')

    sorted_results = sorted(
        results, key=lambda r: race_parser.get_finish_time(r))

    result_by_profile = {race_parser.get_profile(r): r for r in sorted_results}
    make_new_athletes(result_by_profile)

    athletes = list(score_api.get_athletes(
        profiles=list(result_by_profile.keys())))

    old_rating_by_profile = {athlete['profile']: athlete['rating'] for athlete in athletes}
    old_races_by_profile = {athlete['profile']: athlete['races'] for athlete in athletes}

    race_summary_by_profile = {}
    min_time = 9999999
    max_time = 0
    for profile, result in result_by_profile.items():
        rating_before = old_rating_by_profile[profile]
        races_before = old_races_by_profile[profile]
        finish_time = race_parser.get_finish_time(result)
        min_time = min(min_time, finish_time)
        max_time = max(max_time, finish_time)

        race_summary = {
            'index': races_before,
            'date': race_parser.get_race_date(race),
            'name': race_parser.get_race_name(race),
            'type': race_parser.get_race_type(race),
            'group': group,
            'size': group_size,
            'finish': finish_time,
            'splits': {
                'swim': race_parser.get_swim_time(result),
                't1': race_parser.get_t1_time(result),
                'bike': race_parser.get_bike_time(result),
                't2': race_parser.get_t2_time(result),
                'run': race_parser.get_run_time(result),
            },
            'rank': 0.,
            'seed': 0.,
            'rating_delta': 0,
            'rating_before': rating_before,
            'rating_after': 0,
        }
        race_summary_by_profile[profile] = race_summary

    max_time_diff = (max_time - min_time)

    for profile, race_summary in race_summary_by_profile.items():
        finish_time = race_summary['finish']

        rank = 1.
        if max_time_diff > 0:
            time_diff = finish_time - min_time
            rank += 1. * (group_size - 1) * time_diff / max_time_diff

        seed = 1.
        old_rating = old_rating_by_profile[profile]
        old_races = old_races_by_profile[profile]

        for other_profile, _ in race_summary_by_profile.items():
            if other_profile == profile:
                continue
            other_rating = old_rating_by_profile[other_profile]
            seed += get_elo_win_probability(other_rating, old_rating)

        rel_rank = (seed - rank) / (group_size - 1) if group_size > 1 else 0.
        race_type_multiplier = get_race_type_multiplier(race_summary['type'])
        rating_multiplier = get_rating_multiplier(old_rating)

        rating_delta = round(
            rel_rank * race_type_multiplier * rating_multiplier)
        new_rating = old_rating + rating_delta
        new_races = old_races + 1

        race_summary['seed'] = seed
        race_summary['rank'] = rank
        race_summary['rating_delta'] = rating_delta
        race_summary['rating_after'] = new_rating

        score_api.update_athlete(profile, race_summary, new_rating, new_races)


def make_new_athletes(result_by_profile):
    for profile, result in result_by_profile.items():
        if score_api.profile_exists(profile):
            continue

        athlete = {
            'profile': profile,
            'name': race_parser.get_name(result),
            'country': race_parser.get_country(result),
            'gender': race_parser.get_gender(result),
            'races': 0,
            'rating': START_RATING,
            'history': []
        }

        score_api.add_athlete(athlete)


def get_elo_win_probability(ra, rb):
    return 1. / (1. + pow(10., (rb - ra) / 400.))


def get_race_type_multiplier(race_type):
    race_type_to_multiplier = {
        'supersprint': 1.,
        'sprint': 2.,
        'olympic': 4.,
        'half': 8.,
        'full': 16.
    }
    assert race_type in race_type_to_multiplier, f'invalid race type: {race_type}'
    return race_type_to_multiplier[race_type]


def get_rating_multiplier(rating):
    return max(1., 61. - rating / 50.)


def main():
    logger.info('starting tricsore app')

    races = race_api.get_races(starts_with='ironstar', ascending=True)
    # races = race_api.get_races(starts_with='ironman', ascending=True)
    race_count = races.count()
    max_count = -1

    for i, race in enumerate(races):
        if i == max_count:
            logger.info(f'stopping by max count: {max_count}')
            break

        race_name = race_parser.get_race_name(race)
        logger.info(f'{i + 1}/{race_count}: {race_name}')

        process_race(race)

    top_athletes = score_api.get_top_athletes()

    print('distribution')
    distribution.print_distribution(top_athletes)

    print('rating')
    utils.print_dicts(list(top_athletes), lj=30, filter_keys='history')


if __name__ == '__main__':
    main()
