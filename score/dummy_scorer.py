#!/usr/bin/env python3
from base import log, utils
import race.parser as race_parser
from race.storage import RaceStorage

logger = log.setup_logger(__file__)


athlete_id_to_name = {}


def get_profile_to_score(results):
    current_score = len(results)
    athlete_id_to_score = {}
    for i, result in enumerate(results):
        athlete_id = race_parser.get_athlete_id(result)
        athlete_name = race_parser.get_athlete_name(result)
        if athlete_id not in athlete_id_to_name:
            athlete_id_to_name[athlete_id] = athlete_name
        else:
            expected_name = athlete_id_to_name[athlete_id]
            assert athlete_name == expected_name,\
                f'athlete name: {athlete_name} expected_name: {expected_name}'

        athlete_id_to_score[athlete_id] = current_score
        # logger.debug(f'{i}: {athlete_id} {current_score}')
        current_score -= 1
    return athlete_id_to_score


def main():
    race_storage = RaceStorage()

    athlete_id_to_scores = {}
    max_count = -1

    races = race_storage.get_races()
    race_count = races.count()

    for i, race in enumerate(races):
        if i == max_count:
            logger.info(f'stopping by max count: {max_count}')
            break

        race_name = race_parser.get_race_name(race)
        logger.info(f'{i + 1}/{race_count}: {race_name}')

        race_results = race_parser.get_race_results(race)

        athlete_id_to_score = get_profile_to_score(race_results)
        for athlete_id, score in athlete_id_to_score.items():
            if athlete_id not in athlete_id_to_scores:
                athlete_id_to_scores[athlete_id] = []
            athlete_id_to_scores[athlete_id].append(score)

    summaries = []
    for i, (athlete_id, scores) in enumerate(athlete_id_to_scores.items()):
        # logger.info(f'{i + 1}/{len(athlete_id_to_scores)}: {athlete_id}')
        summary = {'athlete': athlete_id_to_name[athlete_id], 'total_races': len(
            scores), 'total_score': sum(scores)}
        summaries.append(summary)

    # print(summaries)
    utils.print_dicts(
        sorted(summaries, key=lambda item: -item['total_score']), lj=50)


if __name__ == '__main__':
    main()
