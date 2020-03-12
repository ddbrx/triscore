from datetime import datetime


min = datetime.min
max = datetime.max


def now():
    return datetime.now()


def datetime_from_string(str, format='%Y-%m-%dT%H:%M:%S'):
    return datetime.strptime(str, format)


def datetime_to_string(dt, format='%Y-%m-%dT%H:%M:%S'):
    return datetime.strftime(dt, format)
