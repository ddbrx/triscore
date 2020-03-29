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


def get_subsentences(sentence):
    words = sentence.strip().split()
    subsentences = []
    for length in reversed(range(1, len(words) + 1)):
        for i in range(0, len(words) + 1 - length):
            subsentences.append(' '.join(words[i:i + length]))
    return subsentences
