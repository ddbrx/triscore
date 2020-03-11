import argparse
import json
import logging


logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s[] %(message)s",
    datefmt='%Y-%m-%d %H:%M:%S'
)


def get_rating_and_races(j):
    for user in j["users"]:
        yield int(user["rating"]), int(user["races"])


def main():
    logging.disable(logging.DEBUG)

    parser = argparse.ArgumentParser()
    parser.add_argument('--file', required=True)
    args = parser.parse_args()

    logging.info('args: {}'.format(args))

    hist = {}
    race = {}
    with open(args.file) as f:
        j = json.load(f)
        for rating, races in get_rating_and_races(j):
            index = int(rating / 100)
            if index not in hist:
                hist[index] = 0
                race[index] = []
            hist[index] += 1
            race[index].append(races)
    for index, count in hist.items():
        median_races = sorted(race[index])[int(len(race[index]) / 2)]
        print(f'[{index * 100}, {(index + 1)*100}) count: {count} races: {median_races}')


if __name__ == '__main__':
    main()
