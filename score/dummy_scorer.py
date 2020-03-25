#!/usr/bin/env python3
from base import log, utils
import race.parser as race_parser
from race.api import RaceApi

logger = log.setup_logger(__file__)


def get_profile_to_score(results):
    current_score = len(results)
    profile_to_score = {}
    for i, item in enumerate(results):
        profile = race_parser.get_profile(item)
        profile_to_score[profile] = current_score
        # logger.debug(f'{i}: {profile} {current_score}')
        current_score -= 1
    return profile_to_score


def main():
    race_api = RaceApi()

    profile_to_scores = {}
    max_count = -1

    races = race_api.get_races(starts_with='Ironman', ascending=True)

    race_count = races.count()
    for i, race in enumerate(races):
        if i == max_count:
            logger.info(f'stopping by max count: {max_count}')
            break

        race_name = race_parser.get_race_name(race)
        logger.info(f'{i + 1}/{race_count}: {race_name}')

        race_country = race_parser.get_race_country(race)
        race_results = race_parser.get_race_results(race)
        race_parser.fix_profile_country(race_results, race_country)

        profile_to_score = get_profile_to_score(race_results)
        for profile, score in profile_to_score.items():
            if profile not in profile_to_scores:
                profile_to_scores[profile] = []
            profile_to_scores[profile].append(score)

    summaries = []
    for i, (profile, scores) in enumerate(profile_to_scores.items()):
        # logger.info(f'{i + 1}/{len(profile_to_scores)}: {profile}')
        summary = {'profile': profile, 'total_races': len(
            scores), 'total_score': sum(scores)}
        summaries.append(summary)

    # print(summaries)
    utils.print_dicts(
        sorted(summaries, key=lambda item: -item['total_score'])[0:10], lj=50)


if __name__ == '__main__':
    main()
