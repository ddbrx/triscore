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


DEFAULT_A = 6
DEFAULT_B = 12
DEFAULT_C = 3
DEFAULT_D = 0

A = 0
B = 0
C = 0
D = 0


def get_elo_win_probability(ra, rb):
    return 1. / (1. + pow(10., (rb - ra) / 400.))


def get_race_type_multiplier(race_type):
    if race_type.find('supersprint') != -1:
        return 0.5
    elif race_type.find('sprint') != -1:
        return 1.
    elif race_type.find('olympic') != -1:
        return 2.
    elif race_type.find('half') != -1:
        return 4.
    elif race_type.find('full') != -1:
        return 8.
    assert False, f'invalid race type: {race_type}'


def get_score_multiplier(rank_delta, score):
    if rank_delta > 0:
        # x = max(2., -score + 3500.)
        # return A * math.log(x, B * 0.1)

        # formula2
        # base = B * 0.1
        # x = max(base, 12 + base - score / 250.)
        # return A * math.log(x, base)

        # formula3 (3000)
        # base = B * 0.1
        # x = max(base, base + 60 - score / 50.)
        # return A * math.log(x, base)

        # # formula4 (2500)
        # base = B * 0.01
        # x = max(base, base + 50 - score / 50.)
        # return min(A, math.log(x, base))

        # formula5 (3000)
        # base = B * 0.01
        # x = max(base, base + 12 - score / 250.)
        # return max(A, math.log(x, base))

        # # formula 7,8,11
        # base = B * 0.1
        # x = max(base, 12 + base - score / 250.)
        # return A * max(4, math.log(x, base))

        # formula 9
        # 1000 -> 50
        # 3000 -> 30
        # return max(1., 60. - score / 100.)

        # formula 10
        # 1000 -> 40
        # 3000 -> 20
        # return max(10., 50. - score / 100.)

        # formula 12
        # 1000 -> 40
        # 3000 -> 20
        # base = B * 0.1
        # x = max(base, 10 + base - score / 350.)
        # return A * max(4, math.log(x, base))

        # # formula 13
        # # 1000 -> 40
        # # 3000 -> 20
        # base = B * 0.1
        # x = max(base, 10 + base - score / 400.)
        # return A * max(4, math.log(x, base))

        # # formula 15
        # # 1000 -> 47
        # # 3000 -> 30
        # base = B * 0.1
        # x = max(base, 10 + base - score / 400.)
        # return A * max(6, math.log(x, base))

        # formula 16,17,18
        # 1000 -> 47
        # 3000 -> 30
        base = B * 0.1
        x = max(base, 10 + base - score / 500.)
        return A * math.log(x, base)
    else:
        # 1000 -> 1
        # 3000 -> 1 + C
        # return max(1., 1 + C * (score - 1000.) / 2000.)

        # formula6 (negative simmetric to f5)
        # base = B * 0.01
        # x = max(base, base + 12 - (4000 - score) / 250.)
        # return max(C, min(50, math.log(x, base)))

        # # formula7,8,11
        # base = B * 0.1
        # x = max(base, 12 + base - (4000 - score) / 250.)
        # return C * math.log(x, base)

        # formula 9,10
        # 1000 -> 5
        # 3000 -> 10
        # return min(10, 2.5 + score / 400.)

        # # formula 12
        # base = B * 0.1
        # x = max(base, 10 + base - (4000 - score) / 350.)
        # return C * math.log(x, base)

        # # formula 13,14,15
        # base = B * 0.1
        # x = max(base, 10 + base - (4000 - score) / 400.)
        # return C * math.log(x, base)

        # # formula 16
        # base = B * 0.1
        # x = max(base, 10 + base - (4000 - score) / 500.)
        # return C * math.log(x, base)

        # formula 18
        base = B * 0.1
        x = max(base, 10 + base - (4000 - score) / 400.)
        return C * math.log(x, base)


def get_finish_multiplier(rank_delta, finish_status, score):
    if finish_status == 'ok':
        if rank_delta >= 0:
            return 1.2
        else:
            return 0.8
    elif finish_status == 'DNS':
        return 0.
    return 1.


class EloScorer:
    def __init__(self, scores_collection, prod):
        self.prod = prod
        self.score_storage = ScoreStorage(
            collection_name=scores_collection, create_indices=True) if self.prod else MockScoreStorage()

    def add_race(self, race_info, race_results):
        results_by_group = self.get_results_by_group(race_results)
        for age_group, results in results_by_group.items():
            self.process_group(age_group, results, race_info)

    def get_results_by_group(self, race_results):
        results_by_group = {}
        for result in race_results:
            age_group = race_parser.get_age_group(result)
            if age_group not in results_by_group:
                results_by_group[age_group] = []
            results_by_group[age_group].append(result)

        return results_by_group

    def process_group(self, age_group, results, race_info):
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

        race_name = race_parser.get_race_name(race_info)
        race_date = race_parser.get_race_date(race_info)
        race_type = race_parser.get_race_type(race_info)
        race_fifa_code = race_parser.get_race_fifa_code(race_info)

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
                assert not not_finished_found, f'invalid order of athletes: finished after dnf: {result}'
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

        race_type_multiplier = get_race_type_multiplier(race_type)

        for result in results:
            athlete_id = race_parser.get_athlete_id(result)
            finish_time = race_parser.get_finish_time(result)
            finish_status = race_parser.get_finish_status(result)
            is_finished = finish_status == race_builder.FINISH_STATUS_OK

            virtual_seed_rank = 1.
            virtual_time_rank = race_parser.get_age_group_rank(result)

            athlete_score = score_by_id[athlete_id]
            athlete_race_count = races_count_by_id[athlete_id]

            for other_result in results:
                other_athlete_id = race_parser.get_athlete_id(other_result)
                if other_athlete_id == athlete_id:
                    continue
                other_score = score_by_id[other_athlete_id]
                virtual_seed_rank += get_elo_win_probability(
                    other_score, athlete_score)

            if is_finished:
                if real_age_group_size < virtual_age_group_size:
                    vr_group_size_diff = virtual_age_group_size - real_age_group_size
                    start_win_prob = get_elo_win_probability(
                        START_SCORE, athlete_score)
                    virtual_seed_rank += vr_group_size_diff * start_win_prob

                if max_time_diff > 0:
                    time_diff = finish_time - fastest_time
                    # here real_age_group_size is important
                    virtual_time_rank = 1 + 1. * (real_age_group_size - 1) * \
                        time_diff / max_time_diff

            rank_delta = (virtual_seed_rank - virtual_time_rank) / \
                (virtual_age_group_size - 1)
            score_multiplier = get_score_multiplier(rank_delta, athlete_score)
            finish_multiplier = get_finish_multiplier(
                rank_delta, finish_status, athlete_score)

            if not is_finished:
                assert rank_delta <= 0, f'positive delta for DNF result: {result}'

            score_delta = round(
                rank_delta * race_type_multiplier * score_multiplier * finish_multiplier)

            new_score = athlete_score + score_delta
            new_race_count = athlete_race_count + 1

            race_summary = {}

            race_section = {
                'index': new_race_count,
                'type': race_type
            }

            if self.prod:
                race_section.update({
                    'race': race_name,
                    'date': race_date,
                    'rc': race_fifa_code
                })
            race_summary.update(race_section)

            result_section = {
                'a': race_parser.get_age_group(result),
                'ns': new_score,
                'c': race_parser.get_country_fifa_code(result),

                'as': race_parser.get_age_group_size(result),
                'ar': race_parser.get_age_group_rank(result),
                'tar': race_parser.get_time_age_group_rank(result),

                'vtr': virtual_time_rank,
                'vsr': virtual_seed_rank,

                'ps': athlete_score,
                'da': score_delta,

                'st': finish_status,
                't': finish_time,
            }

            if self.prod:
                result_section.update({
                    'b': race_parser.get_bib(result),

                    'g': race_parser.get_gender(result),
                    'gs': race_parser.get_gender_size(result),
                    'gr': race_parser.get_gender_rank(result),
                    'tgr': race_parser.get_time_gender_rank(result),

                    'os': race_parser.get_overall_size(result),
                    'or': race_parser.get_overall_rank(result),
                    'tor': race_parser.get_time_overall_rank(result),

                    'legs': race_parser.get_legs(result)
                })
            else:
                result_section.update({
                    'vrd': rank_delta,
                    'race_m': race_type_multiplier,
                    'score_m': score_multiplier,
                    'dnf_m': finish_multiplier
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
    parser.add_argument('--prod', action='store_true')
    parser.add_argument('--log-file', required=True)

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
    race_storage = RaceStorage()

    races = race_storage.get_races(
        skip=args.skip, limit=args.limit, batch_size=10)
    race_count = races.count()

    def print_distribution(index=None):
        top_athletes = elo_scorer.get_top_athletes()
        filename = os.path.basename(
            args.log_file) + (f'.{index}' if index else '')

        dir = os.path.join(os.path.dirname(args.log_file),
                           os.path.splitext(os.path.basename(args.log_file))[0])
        os.makedirs(dir, exist_ok=True)

        file = os.path.join(dir, filename)
        logger.info(f'flushing stats to {file}')
        with open(file, 'w') as f:
            if index:
                f.write(f'distribution #{index}\n')
            else:
                f.write('distribution total\n')

            for line in distribution.gen_chunks_distribution(top_athletes):
                f.write(line + '\n')

            f.write('\n----\n')

            for line in distribution.gen_distribution_by_score(top_athletes):
                f.write(line + '\n')

            f.write('top 100\n')
            top_100_athletes = list(top_athletes)[0:100]
            for i, line in enumerate(utils.gen_dicts(top_100_athletes, lj=30, filter_keys=['id', 'h', 'g'])):
                f.write(line + '\n')
                if i == 0:
                    continue

                for hline in utils.gen_dicts(list(top_100_athletes[i - 1]['h']), lj=10):
                    f.write(hline + '\n')

            f.write('last 100\n')
            last_100_athletes = list(top_athletes)[-100:]
            for i, line in enumerate(utils.gen_dicts(last_100_athletes, lj=30, filter_keys=['id', 'h', 'g'])):
                f.write(line + '\n')
                if i == 0:
                    continue

                for hline in utils.gen_dicts(list(last_100_athletes[i - 1]['h']), lj=10):
                    f.write(hline + '\n')

    for i, race_info in enumerate(races):
        race_date = race_parser.get_race_date(race_info)
        race_name = race_parser.get_race_name(race_info)
        logger.info(f'{i + 1}/{race_count}: {race_date} {race_name}')

        if args.prod and race_parser.get_race_processed(race_info):
            logger.info(f'skip processed race')
        else:
            race_results = race_storage.get_race_results(
                race_name=race_name, race_date=race_date)
            elo_scorer.add_race(race_info, race_results)

        if not args.prod and (i + 1) % 100 == 0:
            print_distribution(i + 1)

    print_distribution()


if __name__ == '__main__':
    main()
