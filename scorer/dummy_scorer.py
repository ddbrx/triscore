#!/usr/bin/env python3
import os

from base import log, utils
from saver.tristats import fs_api, mongo_api, parser

logger = log.setup_logger(__file__)


def get_profile_to_score(results):
    current_score = len(results)
    profile_to_score = {}
    for i, item in enumerate(results):
        profile = parser.get_profile(item)
        profile_to_score[profile] = current_score
        # logger.debug(f'{i}: {profile} {current_score}')
        current_score -= 1
    return profile_to_score


def main():
    api = mongo_api.MongoApi()
    athletes = [athlete for athlete in api.get_top_athletes(limit=10)]
    print(athletes)

    # api = fs_api.FsApi()

    # profile_to_scores = {}
    # max_count = 1

    # # races, races_count = api.get_races(ascending=True)
    # # for i, race in enumerate(races):
    # for i, (race, races_count) in enumerate(api.get_races(ascending=True)):
    #     if i == max_count:
    #         logger.info(f'stopping by max count: {max_count}')
    #         break

    #     race_name = race['RaceName']
    #     logger.info(f'{i + 1}/{races_count}: {race_name}')

    #     race_results = api.get_results_json(race)
    #     parser.fix_profile_country(race_results, parser.get_race_country(race))
    #     profile_to_score = get_profile_to_score(race_results)
    #     for profile, score in profile_to_score.items():
    #         if profile not in profile_to_scores:
    #             profile_to_scores[profile] = []
    #         profile_to_scores[profile].append(score)

    # summaries = []
    # for i, (profile, scores) in enumerate(profile_to_scores.items()):
    #     # logger.info(f'{i + 1}/{len(profile_to_scores)}: {profile}')
    #     summary = {'profile': profile, 'total_races': len(
    #         scores), 'total_score': sum(scores)}
    #     summaries.append(summary)

    # print(summaries)
    # utils.print_dicts(
    #     sorted(summaries, key=lambda item: -item['total_score'])[0:10], lj=50)


if __name__ == '__main__':
    main()
