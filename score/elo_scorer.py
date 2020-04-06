#!/usr/bin/env python3
import argparse
import json
import os
import math

from base import log, utils
import race.parser as race_parser
import race.builder as race_builder
from race.storage import RaceStorage
from score.storage import ScoreStorage, MockScoreStorage
import distribution

logger = log.setup_logger(__file__, debug=False)

START_SCORE = 1500
MIN_GROUP_SIZE = 10


DEFAULT_A = 3
DEFAULT_B = 16
DEFAULT_C = 2
DEFAULT_D = 1

A = 0
B = 0
C = 0
D = 0

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
        x = max(2., -score + 3500.)
        return A * math.log(x, B * 0.1)
    else:
        # 1000 -> 1
        # 3000 -> 1 + C
        return max(1., 1 + C * (score - 1000.) / 2000.)


def get_dnf_multiplier(is_finished, score):
    if is_finished:
        return 1.
    # 1000 -> 1
    # 3000 -> 1 + D
    return max(1., 1 + D * (score - 1000.) / 2000.)


def get_first_time_multiplier(score):
    if score == START_SCORE:
        return 1. / 3

    return 1.


class EloScorer:
    def __init__(self, scores_collection, prod):
        self.prod = prod
        self.score_storage = ScoreStorage(
            collection_name=scores_collection) if self.prod else MockScoreStorage()

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

            virtual_seed_rank = 1.
            athlete_score = score_by_id[athlete_id]
            athlete_race_count = races_count_by_id[athlete_id]

            for other_result in results:
                other_athlete_id = race_parser.get_athlete_id(other_result)
                if other_athlete_id == athlete_id:
                    continue
                other_score = score_by_id[other_athlete_id]
                virtual_seed_rank += get_elo_win_probability(
                    other_score, athlete_score)

            if is_finished and real_age_group_size < virtual_age_group_size:
                vr_group_size_diff = virtual_age_group_size - real_age_group_size
                start_win_prob = get_elo_win_probability(
                    START_SCORE, athlete_score)
                virtual_seed_rank += vr_group_size_diff * start_win_prob

            virtual_time_rank = race_parser.get_age_group_rank(result)
            if is_finished and max_time_diff > 0:
                time_diff = finish_time - fastest_time
                virtual_time_rank = 1 + 1. * (virtual_age_group_size - 1) * \
                    time_diff / max_time_diff

            rank_delta = (virtual_seed_rank - virtual_time_rank) / (virtual_age_group_size - 1)
            score_multiplier = get_score_multiplier(rank_delta, athlete_score)
            dnf_multiplier = get_dnf_multiplier(is_finished, athlete_score)
            first_time_multiplier = get_first_time_multiplier(athlete_score)

            if not is_finished:
                assert rank_delta <= 0, f'positive delta for DNF result: {result}'

            score_delta = round(
                race_type_multiplier * rank_delta * score_multiplier * dnf_multiplier * first_time_multiplier)

            new_score = athlete_score + score_delta
            new_race_count = athlete_race_count + 1

            race_summary = {}

            race_section = {
                'index': new_race_count
            }

            if self.prod:
                race_section.update({
                    'race': race_name,
                    'date': race_date,
                    'type': race_type,
                    'rc': race_fifa_code
                })

            race_summary.update(race_section)

            result_section = {
                'a': race_parser.get_age_group(result),
                'ns': new_score,
                'c': race_parser.get_country_fifa_code(result)
            }

            if self.prod:
                result_section.update({
                    'b': race_parser.get_bib(result),

                    'st': finish_status,
                    't': finish_time,
                    'as': race_parser.get_age_group_size(result),
                    'ar': race_parser.get_age_group_rank(result),
                    'tar': race_parser.get_time_age_group_rank(result),

                    'g': race_parser.get_gender(result),
                    'gs': race_parser.get_gender_size(result),
                    'gr': race_parser.get_gender_rank(result),
                    'tgr': race_parser.get_time_gender_rank(result),

                    'os': race_parser.get_overall_size(result),
                    'or': race_parser.get_overall_rank(result),
                    'tor': race_parser.get_time_overall_rank(result),

                    'legs': race_parser.get_legs(result),

                    'vtr': virtual_time_rank,
                    'vsr': virtual_seed_rank,

                    'ps': athlete_score,
                    'da': score_delta
                })
            athlete_name = race_parser.get_athlete_name(result)
            logger.debug(f'athlete: {athlete_name} result: {result_section}')
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
    parser.add_argument('--file', required=True)

    parser.add_argument('--A', type=int, default=DEFAULT_A)
    parser.add_argument('--B', type=int, default=DEFAULT_B)
    parser.add_argument('--C', type=int, default=DEFAULT_C)
    parser.add_argument('--D', type=int, default=DEFAULT_D)

    args = parser.parse_args()
    logger.info(f'args: {args}')

    global A
    global B
    global C
    global D

    A = args.A
    B = args.B
    C = args.C
    D = args.D

    elo_scorer = EloScorer(
        scores_collection=args.scores_collection, prod=args.prod)
    race_storage = RaceStorage(
        collection_name=args.races_collection, dbname=args.races_db)

    races = race_storage.get_races(
        skip=args.skip, limit=args.limit, ascending=True)
    race_count = races.count()


    def print_distribution(i=None):
        top_athletes = elo_scorer.get_top_athletes()
        filename = os.path.basename(args.file) + (f'.{i}' if i else '')

        dir = os.path.join(os.path.dirname(args.file), os.path.splitext(os.path.basename(args.file))[0])
        os.makedirs(dir, exist_ok=True)

        file = os.path.join(dir, filename)
        logger.info(f'flushing stats to {file}')
        with open(file, 'w') as f:
            if i:
                f.write(f'distribution #{i}\n')
            else:
                f.write('distribution total\n')
            for line in distribution.gen_distribution_by_score(top_athletes):
                f.write(line + '\n')

            f.write('top 100\n')
            for line in utils.gen_dicts(list(top_athletes)[0:100], lj=30, filter_keys=['id', 'h', 'g']):
                f.write(line + '\n')

            f.write('last 100\n')
            for line in utils.gen_dicts(list(top_athletes)[-100:], lj=30, filter_keys=['id', 'h', 'g']):
                f.write(line + '\n')

    for i, race in enumerate(races):
        race_date = race_parser.get_race_date(race)
        race_name = race_parser.get_race_name(race)
        logger.info(f'{i + 1}/{race_count}: {race_date} {race_name}')
        elo_scorer.add_race(race)
        if (i + 1) % 100 == 0:
            print_distribution(i + 1)

    print_distribution()


if __name__ == '__main__':
    main()
