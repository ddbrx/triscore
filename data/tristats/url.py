TRISTATS_API_URL = 'http://tristats.ru/api'
TRISTATS_RACES_URL = f'{TRISTATS_API_URL}/rus/race'
TRISTATS_RESULTS_URL = f'{TRISTATS_API_URL}/result'


def get_results_url(race_url):
    return TRISTATS_RESULTS_URL + race_url
