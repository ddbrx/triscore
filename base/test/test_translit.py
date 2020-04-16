import pytest
from base import translit


def assert_eq(result, expected):
    assert result == expected, f'result: {result} expected: {expected}'


def assert_list_eq(result, expected):
    if isinstance(expected, str):
        expected = [expected]
    assert_eq(sorted(result), sorted(expected))


def en_to_ru(en, expected_ru):
    assert_list_eq(translit.english_to_cyrillic(en), expected_ru)


def ru_to_en(ru, expected_en):
    assert_list_eq(translit.cyrillic_to_english(ru), expected_en)


class TestTranslitWord:
    def test_empty_word(self):
        ru_to_en('', '')
        en_to_ru('', '')

    def test_upper_case(self):
        ru_to_en('СлОвО', 'slovo')
        en_to_ru('sLoVO', 'слово')

    def test_heading_spaces(self):
        ru_to_en('  слово', 'slovo')
        en_to_ru('    slovo', 'слово')

    def test_trailing_spaces(self):
        ru_to_en('слово   ', 'slovo')
        en_to_ru('slovo  ', 'слово')

    def test_heading_and_trailing_spaces(self):
        ru_to_en('     слово   ', 'slovo')
        en_to_ru('   slovo      ', 'слово')

    def test_ey_ei(self):
        ru_to_en('сейбанова', ['seybanova', 'seibanova'])
        en_to_ru('seybanova', 'сейбанова')

    def test_ryn(self):
        ru_to_en('добрынин', 'dobrynin')
        en_to_ru('dobrynin', 'добрынин')

    def test_zh(self):
        ru_to_en('жидков', 'zhidkov')
        en_to_ru('zhidkov', 'жидков')

    def test_ya(self):
        ru_to_en('полянский', ['polyanskii', 'polyanskiy'])
        en_to_ru('polyanskii', 'полянский')
        en_to_ru('polyanskiy', 'полянский')
        en_to_ru('polyansky', 'полянский')

        ru_to_en('ярошенко', ['yaroshenko'])
        en_to_ru('yaroshenko', 'ярошенко')

    def test_ye(self):
        ru_to_en('турбаевский', ['turbaevskii', 'turbaevskiy'])
        en_to_ru('turbaevskii', 'турбаевский')
        en_to_ru('turbaevskiy', 'турбаевский')
        en_to_ru('turbayevskii', 'турбаевский')
        en_to_ru('turbayevskiy', 'турбаевский')

    def test_ts(self):
        ru_to_en('ляцкий', ['lyatskii', 'lyatskiy'])
        en_to_ru('lyatskii', 'ляцкий')
        en_to_ru('lyatskiy', 'ляцкий')

    def test_yu(self):
        ru_to_en('брюханков', 'bryukhankov')
        en_to_ru('bryukhankov', 'брюханков')

    def test_sys(self):
        ru_to_en('сысоев', 'sysoev')
        en_to_ru('sysoev', 'сысоев')

    def test_bys(self):
        ru_to_en('абысова', 'abysova')
        en_to_ru('abysova', 'абысова')

    def test_kh(self):
        ru_to_en('кислухина', 'kislukhina')
        en_to_ru('kisluhina', 'кислухина')
        en_to_ru('kislukhina', 'кислухина')

    def test_gor(self):
        ru_to_en('горбунов', 'gorbunov')
        en_to_ru('gorbunov', 'горбунов')

    def test_ysh(self):
        ru_to_en('малышев', 'malyshev')
        en_to_ru('malyshev', 'малышев')

    def test_tsy(self):
        ru_to_en('грицюк', 'gritsuk')
        en_to_ru('gritsyk', 'грицюк')

    def test_io(self):
        ru_to_en('слепнёв', 'slepnev')
        en_to_ru('slepnev', 'слепнев')

    def test_py(self):
        ru_to_en('пырев', 'pyrev')
        en_to_ru('pyrev', 'пырев')

    def test_ty(self):
        ru_to_en('мартынов', 'martynov')
        en_to_ru('martynov', 'мартынов')


class TestTranslitSentence:
    def test_sentence_with_spaces(self):
        ru_to_en('  длинное предложение с пробелами в начале и конце      ',
                 'dlinnoe predlozhenie s probelami v nachale i kontse')
        en_to_ru('  dlinnoe predlozhenie s probelami v nachale i kontse      ',
                 'длинное предложение с пробелами в начале и конце')

    def test_sentence_with_exception(self):
        ru_to_en('игорь крутой', ['igor krutoi', 'igor krutoy'])
        en_to_ru('igor krutoi', 'игорь крутой')
        en_to_ru('igor krutoy', 'игорь крутой')


class TestTranslitCustomNames:
    def test_jan(self):
        ru_to_en('ян', 'jan')
        en_to_ru('jan', 'ян')

    def test_dmitriy(self):
        ru_to_en('дмитрий', ['dmitrii', 'dmitriy'])
        en_to_ru('dmitrii', 'дмитрий')
        en_to_ru('dmitriy', 'дмитрий')
        en_to_ru('dmitry', 'дмитрий')

    def test_evgeniy(self):
        ru_to_en('евгений', ['evgenii', 'evgeniy'])
        en_to_ru('evgenii', 'евгений')
        en_to_ru('evgeniy', 'евгений')
        en_to_ru('evgeny', 'евгений')

    def test_igor(self):
        ru_to_en('игорь', 'igor')
        en_to_ru('igor', 'игорь')

    def test_mikhail(self):
        ru_to_en('михаил', 'mikhail')
        en_to_ru('mikhail', 'михаил')

    def test_ilya(self):
        ru_to_en('илья', 'ilya')
        en_to_ru('ilya', 'илья')
