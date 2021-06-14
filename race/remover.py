#!/usr/bin/env python3
import argparse
from base import log
from race.storage import TriscoreStorage

logger = log.setup_logger(__file__, debug=True)


def remove_race(db_name, race_name, race_date):
    race_storage = TriscoreStorage(dbname=db_name)
    try:
        race_storage.remove_race(name=race_name, date=race_date)
    except Exception as exception:
        logger.error(f'exception while removing race: {race_name} {race_date}: {repr(exception)}')


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
