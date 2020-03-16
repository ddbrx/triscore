import re
import itertools

MAX_SUB_LENGTH = 3


CYR_TO_EN = {
    'а': ['a'],
    'б': ['b'],
    'в': ['v'],
    'г': ['g'],
    'д': ['d'],
    'е': ['e'],
    'ё': ['e'],
    'ж': ['zh'],
    'з': ['z'],
    'и': ['i'],
    'й': ['j'],
    'к': ['k'],
    'л': ['l'],
    'м': ['m'],
    'н': ['n'],
    'о': ['o'],
    'п': ['p'],
    'р': ['r'],
    'с': ['s'],
    'т': ['t'],
    'у': ['u'],
    'ф': ['f'],
    'х': ['kh'],
    'ц': ['ts'],
    'ч': ['ch'],
    'ш': ['sh'],
    'щ': ['sch'],
    'ъ': [''],
    'ы': ['y'],
    'ь': [''],
    'э': ['e'],
    'ю': ['yu'],
    'я': ['ya'],

    'ай': ['ay', 'ai'],
    'ой': ['oy', 'oi'],
    'уй': ['uy', 'ui'],
    'ей': ['ey', 'ei'],
    'эй': ['ey', 'ei'],
    'ий': ['iy', 'ii'],
    'цю': ['tsu'],

    'лье': ['lie'],
    'льц': ['lts'],
}

CYR_TO_EN_EXCEPTIONS = {
    'ян': ['jan'],
}

EN_TO_CYR = {
    'a': ['а'],
    'b': ['б'],
    'c': ['ц'],
    'd': ['д'],
    'e': ['е'],
    'f': ['ф'],
    'g': ['г'],
    'h': ['х'],
    'i': ['и'],
    'j': ['й'],
    'k': ['к'],
    'l': ['л'],
    'm': ['м'],
    'n': ['н'],
    'o': ['о'],
    'p': ['п'],
    'q': ['к'],
    'r': ['р'],
    's': ['с'],
    't': ['т'],
    'u': ['у'],
    'v': ['в'],
    'w': ['в'],
    'x': ['кс'],
    'y': ['й'],
    'z': ['з'],

    'by': ['бы'],
    'ch': ['ч'],
    'ii': ['ий'],
    'oi': ['ой'],
    'ai': ['ай'],
    'ui': ['уй'],
    'kh': ['х'],
    'ly': ['лы'],
    'ny': ['ний'],
    'py': ['пы'],
    'ry': ['ры'],
    'sh': ['ш'],
    'sy': ['сы'],
    'ts': ['ц'],
    'ty': ['ты'],
    'ya': ['я'],
    'ye': ['е'],
    'yo': ['ё'],
    'yu': ['ю'],
    'zh': ['ж'],

    'ail': ['аил'],
    'lie': ['лье'],
    'lya': ['ля'],
    'sch': ['щ'],
    'sky': ['ский'],
    'rya': ['ря'],
    'ryu': ['рю'],
    'sya': ['ся'],
    'tsy': ['цю'],
    'try': ['трий'],
}

EN_TO_CYR_EXCEPTIONS = {
    'igor': ['игорь'],
    'ilya': ['илья'],
    'jan': ['ян'],
}


def get_translit_options(text):
    if has_cyrillic(text):
        return cyrillic_to_english(text)
    else:
        return english_to_cyrillic(text)


def has_cyrillic(text):
    return bool(re.search('[а-яА-Я]', text))


def cyrillic_to_english(text):
    return _convert_text(text, CYR_TO_EN, CYR_TO_EN_EXCEPTIONS)


def english_to_cyrillic(text):
    return _convert_text(text, EN_TO_CYR, EN_TO_CYR_EXCEPTIONS)


def _convert_text(text, mapping, exceptions):
    options = []
    words = text.lower().split()
    options = map(lambda word: _convert_word(word, mapping, exceptions), words)
    products = itertools.product(*options)
    return list(map(lambda product: ' '.join(product), products))


def _convert_word(word, mapping, exceptions):
    if word in exceptions:
        return exceptions[word]

    results = ['']
    i = 0
    while i < len(word):
        subs = []
        for length in reversed(range(1, 1 + MAX_SUB_LENGTH)):
            subs.append(word[i:i+length])
        found = False

        for sub in subs:
            if sub not in mapping:
                continue

            new_results = []
            for result in results:
                for option in mapping[sub]:
                    new_results.append(result + option)
            results = new_results
            found = True
            i += len(sub)
            break

        if not found:
            results = list(map(lambda result: result + word[i], results))
            i += 1

    return results
