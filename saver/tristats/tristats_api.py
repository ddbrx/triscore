import log
import requests

logger = log.setup_logger(__file__)


TRISTATS_API_URL = 'http://tristats.ru/api'
RACES_URL = f'{TRISTATS_API_URL}/rus/race'
RESULTS_URL = f'{TRISTATS_API_URL}/result'


def load_url(url):
    logger.info(f'loading url {url}')
    r = requests.get(url)
    if r.status_code != 200:
        logger.error(f'GET failed url: {url} code: {r.status_code}')
        return None
    return r.text
