#!/usr/bin/env python3
import argparse
import json
import os

from base import log, utils
import race.parser as race_parser
import race.builder as race_builder
from race.storage import RaceStorage
from score.storage import ScoreStorage, MockScoreStorage
import distribution

logger = log.setup_logger(__file__, debug=False)

START_SCORE = 1500
MIN_GROUP_SIZE = 10


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


def get_score_multiplier(rank_delta, score):
    if rank_delta > 0:
        return max(1., 81. - score / 30.)
    else:
        return max(1., -4. + score / 200.)


def get_dnf_multiplier(is_finished, score):
    if is_finished:
        return 1.

    return max(1., score / 500.)


def get_first_time_multiplier(score):
    if score == START_SCORE:
        return 1. / 3

    return 1.


class EloScorer:
    def __init__(self, scores_collection, prod):
        self.score_storage = ScoreStorage(
            collection_name=scores_collection) if prod else MockScoreStorage()

    def add_race(self, race):
        results_by_group = self.get_results_by_group(race)
        for age_group, results in results_by_group.items():
            self.process_group(age_group, results, race)

    def get_results_by_group(self, race):
        results_by_group = {}

        race_results = race_parser.get_race_results(race)
        for result in race_results:
            age_group = race_parser.get_age_group(result)
            if age_group not in results_by_group:
                results_by_group[age_group] = []
            results_by_group[age_group].append(result)

        return results_by_group

    def process_group(self, age_group, results, race):
        real_age_group_size = len(results)
        assert real_age_group_size > 0, 'emptry age_group: {age_group}'

        virtual_age_group_size = real_age_group_size
        if real_age_group_size < MIN_GROUP_SIZE:
            logger.debug(
                f'set age group size {real_age_group_size} to min: {MIN_GROUP_SIZE}')
            virtual_age_group_size = MIN_GROUP_SIZE

        assert virtual_age_group_size > 1, 'invalid virtual age group size'

        logger.debug(
            f'process age group: {age_group} real size: {real_age_group_size} virtual: {virtual_age_group_size}')

        race_name = race_parser.get_race_name(race)
        race_date = race_parser.get_race_date(race)
        race_type = race_parser.get_race_type(race)
        race_fifa_code = race_parser.get_race_fifa_code(race)
        race_type_multiplier = get_race_type_multiplier(race_type)

        self.make_new_athletes(results)

        fastest_time = 99999
        slowest_time = 0
        prev_finish_time = 0
        not_finished_found = False
        for result in results:
            finish_status = race_parser.get_finish_status(result)
            finish_time = race_parser.get_finish_time(result)
            if finish_time == race_builder.MAX_TIME:
                assert finish_status != race_builder.FINISH_STATUS_OK, f'finished status should not be ok: {result}'
                not_finished_found = True
            else:
                assert finish_status == race_builder.FINISH_STATUS_OK, f'finished status should be ok: {result}'
                assert not not_finished_found, 'invalid order of athletes: finished after dnf'
                assert finish_time >= prev_finish_time, \
                    f'descending finish time: {finish_time} prev: {prev_finish_time} result: {result}'

                prev_finish_time = finish_time
                fastest_time = min(fastest_time, finish_time)
                slowest_time = max(slowest_time, finish_time)

        max_time_diff = (slowest_time - fastest_time)

        athlete_ids = list(
            map(lambda r: race_parser.get_athlete_id(r), results))

        score_by_id = self.score_storage.get_score_by_id(athlete_ids)
        races_count_by_id = self.score_storage.get_race_count_by_id(
            athlete_ids)

        for result in results:
            athlete_id = race_parser.get_athlete_id(result)
            finish_time = race_parser.get_finish_time(result)
            finish_status = race_parser.get_finish_status(result)
            is_finished = finish_status == race_builder.FINISH_STATUS_OK

            seed_rank = 1.
            athlete_score = score_by_id[athlete_id]
            athlete_race_count = races_count_by_id[athlete_id]

            for other_result in results:
                other_athlete_id = race_parser.get_athlete_id(other_result)
                if other_athlete_id == athlete_id:
                    continue
                other_score = score_by_id[other_athlete_id]
                seed_rank += get_elo_win_probability(
                    other_score, athlete_score)

            if is_finished and real_age_group_size < virtual_age_group_size:
                vr_group_size_diff = virtual_age_group_size - real_age_group_size
                start_win_prob = get_elo_win_probability(
                    START_SCORE, athlete_score)
                seed_rank += vr_group_size_diff * start_win_prob

            time_rank = race_parser.get_age_group_rank(result)
            if is_finished and max_time_diff > 0:
                time_diff = finish_time - fastest_time
                time_rank = 1 + 1. * (virtual_age_group_size - 1) * \
                    time_diff / max_time_diff

            rank_delta = (seed_rank - time_rank) / (virtual_age_group_size - 1)
            score_multiplier = get_score_multiplier(rank_delta, athlete_score)
            dnf_multiplier = get_dnf_multiplier(is_finished, athlete_score)
            first_time_multiplier = get_first_time_multiplier(athlete_score)

            if not is_finished:
                assert rank_delta <= 0, f'positive delta for DNF result: {result}'

            score_delta = round(
                race_type_multiplier * rank_delta * score_multiplier * dnf_multiplier * first_time_multiplier)

            new_score = athlete_score + score_delta
            new_race_count = athlete_race_count + 1

            race_section = {
                'index': new_race_count,
                'race': race_name,
                'date': race_date,
                'type': race_type,
                'rc': race_fifa_code,
            }

            result_section = {
                'c': race_parser.get_country_fifa_code(result),
                'b': race_parser.get_bib(result),

                'st': finish_status,
                't': finish_time,

                'a': race_parser.get_age_group(result),
                'as': race_parser.get_age_group_size(result),
                'ar': race_parser.get_age_group_rank(result),

                'g': race_parser.get_gender(result),
                'gs': race_parser.get_gender_size(result),
                'gr': race_parser.get_gender_rank(result),

                'os': race_parser.get_overall_size(result),
                'or': race_parser.get_overall_rank(result),

                'legs': race_parser.get_legs(result),

                'tr': time_rank,
                'sr': seed_rank,

                'ps': athlete_score,
                'ns': new_score,
                'da': score_delta
            }

            athlete_name = race_parser.get_athlete_name(result)
            logger.debug(f'athlete: {athlete_name} score: {result_section}')

            race_summary = {}
            race_summary.update(race_section)
            race_summary.update(result_section)

            self.score_storage.add_athlete_race(athlete_id, race_summary)

    def make_new_athletes(self, results):
        for result in results:
            athlete_id = race_parser.get_athlete_id(result)
            if self.score_storage.athlete_exists(athlete_id):
                continue

            athlete = {
                'id': athlete_id,
                'n': race_parser.get_athlete_name(result),
                'g': race_parser.get_gender(result),
                'c': race_parser.get_country_fifa_code(result),
                'a': race_parser.get_age_group(result),
                'p': 0,
                's': START_SCORE,
                'h': []
            }

            self.score_storage.add_athlete(athlete)

    def get_top_athletes(self):
        return self.score_storage.get_top_athletes()


def main():
    logger.info('starting tricsore app')

    parser = argparse.ArgumentParser()
    parser.add_argument('--skip', type=int, default=0)
    parser.add_argument('--limit', type=int, default=0)
    parser.add_argument('--scores-collection', default='scores')
    parser.add_argument('--races-collection', default='races')
    parser.add_argument('--races-db', default='triscore')
    parser.add_argument('--prod', action='store_true')

    args = parser.parse_args()

    elo_scorer = EloScorer(
        scores_collection=args.scores_collection, prod=args.prod)
    race_storage = RaceStorage(
        collection_name=args.races_collection, dbname=args.races_db)

    races = race_storage.get_races(
        skip=args.skip, limit=args.limit, ascending=True)
    race_count = races.count()

    for i, race in enumerate(races):
        race_name = race_parser.get_race_name(race)
        logger.info(f'{i + 1}/{race_count}: {race_name}')
        elo_scorer.add_race(race)

    top_athletes = elo_scorer.get_top_athletes()

    print('distribution')
    distribution.print_distribution(top_athletes)

    # print('score')
    # utils.print_dicts(list(top_athletes), lj=30, filter_keys=[
    #                   'id', 'history', 'gender'])


if __name__ == '__main__':
    main()
