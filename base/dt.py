from datetime import datetime
from dateutil.relativedelta import relativedelta

min = datetime.min
max = datetime.max

DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S'
DATE_FORMAT = '%Y-%m-%d'


def now():
    return datetime.now()


def datetime_from_string(str, format=DATETIME_FORMAT):
    return datetime.strptime(str, format)


def datetime_to_string(dt, format=DATETIME_FORMAT):
    return datetime.strftime(dt, format)


def date_from_string(d, format=DATE_FORMAT):
    return datetime_from_string(d, format)


def date_to_string(d, format=DATE_FORMAT):
    return datetime_to_string(d, format)


def delta(dt, years=0, days=0):
    return dt + relativedelta(years=years, days=days)
