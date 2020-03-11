import log
import os
from fs_api import FsApi
import parser

logger = log.setup_logger_from_file(__file__)


def get_profile_to_score(results, race):
    current_score = len(results)
    profile_to_score = {}
    for i, item in enumerate(results):
        profile = parser.get_profile(item, race)
        profile_to_score[profile] = current_score
        # logger.debug(f'{i}: {profile} {current_score}')
        current_score -= 1
    return profile_to_score


def main():
    api = FsApi()
    races = api.get_races_json(acsending=True)

    score_table = {}
    max_count = 5
    write_csv = False

    for i, race in enumerate(races):
        if i == max_count:
            logger.info(f'stopping by max count: {max_count}')
            break

        race_name = race['RaceName']
        logger.info(f'{i + 1}/{len(races)}: {race_name}')

        race_url = race['RaceUrl']
        race_date = race['Date']
        race_results = api.get_results_json(race_url, race_date)

        race_country = race['RaceCountry']

        profile_to_score = get_profile_to_score(race_results, race)
        for profile, score in profile_to_score.items():
            if profile not in score_table:
                score_table[profile] = []
            score_table[profile].append((race_date, score))

    profile_to_total_score = {}
    for i, value in enumerate(score_table.items()):
        profile, date_score_list = value
        # logger.info(f'{i + 1}/{len(score_table)}: {profile}')
        total_score = 0
        for date, score in date_score_list:
            total_score += score
        profile_to_total_score[profile] = total_score

    if write_csv:
        with open('score_basic.csv', 'w') as f:
            for i, value in enumerate(sorted(profile_to_total_score.items(), key=lambda item: -item[1])):
                profile, total_score = value
                logger.info(f'{i + 1}/{len(profile_to_total_score)}: {profile}')
                f.write(f'{i + 1}\t{profile}\t{total_score}\n')


if __name__ == '__main__':
    main()
