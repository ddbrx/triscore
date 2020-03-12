def print_dicts(ds, lj=20):
    header = ''
    for d in ds:
        if not header:
            header = ' '.join(x.ljust(lj) for x in d.keys())
            print(header)
        line = ' '.join([str(x).ljust(lj) for x in d.values()])
        print(line)
