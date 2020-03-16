def print_dicts(ds, lj=20, filter_keys=[]):
    if len(ds) == 0:
        return

    header = ''
    keys = list(filter(lambda x: x not in filter_keys, ds[0].keys()))
    header = ' '.join([key.ljust(lj) for key in keys])
    print(header)
    for d in ds:
        values = [d[key] for key in keys]
        line = ' '.join([str(value).ljust(lj) for value in values])
        print(line)
