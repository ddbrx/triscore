#!/usr/bin/env python3
import math

from base import log
import race.parser as race_parser
import race.builder as race_builder

logger = log.setup_logger(__file__, debug=False)

START_SCORE = 1500
MIN_GROUP_SIZE = 10


class EloScorer:
    def __init__(self, athlete_storage, A, B, C):
        self.athlete_storage = athlete_storage
        self.A = A
        self.B = B
        self.C = C

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
        race_country_iso_num = race_parser.get_race_country_iso_num(race_info)

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

        score_by_id = self.athlete_storage.get_score_by_id(athlete_ids)
        races_count_by_id = self.athlete_storage.get_race_count_by_id(
            athlete_ids)

        race_type_multiplier = self.get_race_type_multiplier(race_type)

        for result in results:
            athlete_id = race_parser.get_athlete_id(result)
            finish_time = race_parser.get_finish_time(result)
            finish_status = race_parser.get_finish_status(result)
            is_finished = finish_status == race_builder.FINISH_STATUS_OK

            virtual_seed_rank = 1.
            # ARE YOU SURE HERE NOT TIME AGE GROUP RANK?
            virtual_time_rank = race_parser.get_age_group_rank(result)

            athlete_score = score_by_id[athlete_id]
            athlete_race_count = races_count_by_id[athlete_id]

            for other_result in results:
                other_athlete_id = race_parser.get_athlete_id(other_result)
                if other_athlete_id == athlete_id:
                    continue
                other_score = score_by_id[other_athlete_id]
                virtual_seed_rank += self.get_elo_win_probability(
                    other_score, athlete_score)

            if is_finished:
                if real_age_group_size < virtual_age_group_size:
                    vr_group_size_diff = virtual_age_group_size - real_age_group_size
                    start_win_prob = self.get_elo_win_probability(
                        START_SCORE, athlete_score)
                    virtual_seed_rank += vr_group_size_diff * start_win_prob

                if max_time_diff > 0:
                    time_diff = finish_time - fastest_time
                    # here real_age_group_size is important
                    virtual_time_rank = 1 + 1. * (real_age_group_size - 1) * \
                        time_diff / max_time_diff

            rank_delta = (virtual_seed_rank - virtual_time_rank) / \
                (virtual_age_group_size - 1)
            score_multiplier = self.get_score_multiplier(rank_delta, athlete_score)
            finish_multiplier = self.get_finish_multiplier(
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
                'type': race_type,
                'race': race_name,
                'date': race_date,
                'rc': race_country_iso_num
            }

            race_summary.update(race_section)

            result_section = {
                'a': race_parser.get_age_group(result),
                'ns': new_score,
                'c': race_parser.get_result_country_iso_num(result),

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

            # if self.prod:
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
            # else:
            #     result_section.update({
            #         'vrd': rank_delta,
            #         'race_m': race_type_multiplier,
            #         'score_m': score_multiplier,
            #         'dnf_m': finish_multiplier
            #     })

            athlete_name = race_parser.get_athlete_name(result)
            logger.debug(f'athlete: {athlete_name} result: {result_section}')
            race_summary.update(result_section)

            self.athlete_storage.add_athlete_race(athlete_id, race_summary)

    def get_score_multiplier(self, rank_delta, score):
        if rank_delta > 0:
            base = self.B * 0.1
            x = max(base, 10 + base - score / 500.)
            return self.A * math.log(x, base)
        else:
            base = self.B * 0.1
            x = max(base, 10 + base - (4000 - score) / 400.)
            return self.C * math.log(x, base)

    def get_finish_multiplier(self, rank_delta, finish_status, score):
        if finish_status == 'ok':
            if rank_delta >= 0:
                return 1.2
            else:
                return 0.8
        elif finish_status == 'DNS':
            return 0.
        return 1.

    def get_race_type_multiplier(self, race_type):
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

    def get_elo_win_probability(self, ra, rb):
        return 1. / (1. + pow(10., (rb - ra) / 400.))


    def make_new_athletes(self, results):
        for result in results:
            athlete_id = race_parser.get_athlete_id(result)
            if self.athlete_storage.athlete_exists(athlete_id):
                continue

            athlete = {
                'id': athlete_id,
                'n': race_parser.get_athlete_name(result),
                'g': race_parser.get_gender(result),
                'c': race_parser.get_result_country_iso_num(result),
                'a': race_parser.get_age_group(result),
                'p': 0,
                's': START_SCORE,
                'h': []
            }

            self.athlete_storage.add_athlete(athlete)

    def get_top_athletes(self):
        return self.athlete_storage.get_top_athletes()
