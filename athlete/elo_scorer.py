#!/usr/bin/env python3
import math

from base import log
import race.parser as race_parser
import race.builder as race_builder
import re

logger = log.setup_logger(__file__, debug=False)

START_SCORE = 1500
MIN_GROUP_SIZE = 10
FEMALE_AGE_GROUP_REGEX = re.compile('F\d+-\d+')
MALE_AGE_GROUP_REGEX = re.compile('M\d+-\d+')

class EloScorer:
    def __init__(self, athlete_storage):
        self.athlete_storage = athlete_storage

    def add_race(self, race_info, race_results):
        results_by_group = self.get_results_by_group(race_results)
        all_groups = results_by_group.keys()

        logger.info(f'all groups: {all_groups}')
        female_age_groups = sorted([g for g in all_groups if FEMALE_AGE_GROUP_REGEX.match(g)])
        male_age_groups = sorted([g for g in all_groups if MALE_AGE_GROUP_REGEX.match(g)])
        not_age_groups = [g for g in all_groups if (g not in female_age_groups and g not in male_age_groups)]

        def process_age_group(sorted_age_groups):
            print(f'process age groups: {sorted_age_groups}')
            for i, age_group in enumerate(sorted_age_groups):
                extended_group_results = list(results_by_group[age_group])
                if i > 0:
                    extended_group_results.extend(results_by_group[sorted_age_groups[i - 1]])
                if i + 1 < len(sorted_age_groups):
                    extended_group_results.extend(results_by_group[sorted_age_groups[i + 1]])

                sorted_results = sorted(extended_group_results, key=lambda r: r['t'])
                logger.info(f'age_group: {age_group} actual size: {len(results_by_group[age_group])} extended_size: {len(extended_group_results)}')
                self.process_group(age_group, sorted_results, race_info)

        process_age_group(female_age_groups)
        process_age_group(male_age_groups)
        for group in not_age_groups:
            self.process_group(group, list(results_by_group[group]), race_info)

    def get_results_by_group(self, race_results):
        results_by_group = {}
        for result in race_results:
            age_group = race_parser.get_age_group(result)
            if age_group is None:
                logger.warn('skip None age group')
                continue

            if age_group not in results_by_group:
                results_by_group[age_group] = []
            results_by_group[age_group].append(result)

        return results_by_group

    def process_group(self, age_group, results, race_info):
        result_count = len(results)
        assert result_count > 0, 'emptry age_group: {age_group}'

        logger.info(
            f'process age group: {age_group} size: {result_count}')

        race_name = race_parser.get_race_name(race_info)
        race_date = race_parser.get_race_date(race_info)
        race_type = race_parser.get_race_type(race_info)
        race_country_iso_num = race_parser.get_race_country_iso_num(race_info)

        self.make_new_athletes(results)

        # fastest_time = 999999
        # slowest_time = 0
        prev_finish_time = 0
        not_finished_found = False
        finished_results = []
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
                # fastest_time = min(fastest_time, finish_time)
                # slowest_time = max(slowest_time, finish_time)
                finished_results.append(result)

        # max_time_diff = (slowest_time - fastest_time)

        athlete_ids = list(
            map(lambda r: race_parser.get_athlete_id(r), results))

        score_by_id = self.athlete_storage.get_score_by_id(athlete_ids)
        races_count_by_id = self.athlete_storage.get_race_count_by_id(
            athlete_ids)

        race_type_multiplier = self.get_race_type_multiplier(race_type)

        for i, result in enumerate(results):
            result_age_group = race_parser.get_age_group(result)
            if age_group != result_age_group:
                # skip extended results
                continue

            athlete_id = race_parser.get_athlete_id(result)
            finish_time = race_parser.get_finish_time(result)
            finish_status = race_parser.get_finish_status(result)

            is_started = finish_status != race_builder.FINISH_STATUS_DNS
            is_finished = finish_status == race_builder.FINISH_STATUS_OK

            athlete_score = score_by_id[athlete_id]
            athlete_race_count = races_count_by_id[athlete_id]

            extended_seed_rank = self.get_seed(finished_results, athlete_score, athlete_id, score_by_id)
            extended_age_rank = (i + 1) if is_finished else (len(finished_results) + 1)
            # extended_time_rank = extended_age_rank

            score_delta = 0
            if is_started:
                # if is_finished and max_time_diff > 0:
                #     relative_time = 1. * (finish_time - fastest_time) / max_time_diff
                #     extended_time_rank = 1 + (result_count - 1) * relative_time

                mid_rank = math.sqrt(extended_age_rank * extended_seed_rank)
                need_score = self.get_score_to_rank(finished_results, mid_rank, athlete_id, score_by_id)
                # logger.info(f'mid_rank: {mid_rank} need_score: {need_score}')
                score_delta = round((need_score - athlete_score) * race_type_multiplier)

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
                'c': race_parser.get_result_country_iso_num(result),

                'as': race_parser.get_age_group_size(result),
                'ar': race_parser.get_age_group_rank(result),

                'eas': result_count,
                'ear': extended_age_rank,
                # 'etr': extended_time_rank,
                'esr': extended_seed_rank,

                'ps': athlete_score,
                'da': score_delta,
                'ns': new_score,

                'st': finish_status,
                't': finish_time,
            }

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

            athlete_name = race_parser.get_athlete_name(result)
            logger.debug(f'athlete: {athlete_name} result: {result_section}')
            race_summary.update(result_section)

            self.athlete_storage.add_athlete_race(athlete_id, race_summary)

    def get_seed(self, results, score, athlete_id, score_by_id):
        seed = 1.
        for other_result in results:
            other_athlete_id = race_parser.get_athlete_id(other_result)
            if other_athlete_id == athlete_id:
                continue
            other_score = score_by_id[other_athlete_id]
            seed += self.get_elo_win_probability(other_score, score)

        return seed

    def get_score_to_rank(self, results, rank, athlete_id, score_by_id):
        if len(results) <= 1:
            return score_by_id[athlete_id]

        left = 1
        right = 8000

        while right - left > 1:
            mid = (left + right) / 2.

            if self.get_seed(results, mid, athlete_id, score_by_id) < rank:
                right = mid
            else:
                left = mid

        return left


    def get_race_type_multiplier(self, race_type):
        if race_type.find('supersprint') != -1:
            return 0.0625
        elif race_type.find('sprint') != -1:
            return 0.125
        elif race_type.find('olympic') != -1:
            return 0.25
        elif race_type.find('half') != -1:
            return 0.5
        elif race_type.find('full') != -1:
            return 1.
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

    def get_top_athletes(self, sort_order=-1, limit=0, with_history=False):
        return self.athlete_storage.get_top_athletes(sort_order=sort_order, limit=limit, with_history=with_history)
