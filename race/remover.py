#!/usr/bin/env python3
import argparse
from base import log
from race.storage import RaceStorage

logger = log.setup_logger(__file__, debug=True)


def remove_race(db_name, race_name, race_date):
    race_storage = RaceStorage(dbname=db_name)
    try:
        if race_storage.remove_race(name=race_name, date=race_date):
            logger.info(f'race {race_name} {race_date} was successully removed')
        else:
            logger.warning(f'failed to remove race: {race_name} {race_date}: {exc}')
    except Exception as exc:
        logger.error(f'exception while removing race: {race_name} {race_date}: {exc}')


def main():
    logger.info('starting remover')

    parser = argparse.ArgumentParser()
    parser.add_argument('--db-name', type=str, default='races-v0-1')
    parser.add_argument('--race-name', type=str)
    parser.add_argument('--race-date', type=str)

    args = parser.parse_args()

    remove_race(args.db_name, args.race_name, args.race_date)



if __name__ == '__main__':
    main()
