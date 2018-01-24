# Code based on 

import re
import os
import ast
import json
import jaconv
from pykakasi import kakasi,wakati
from jamo import hangul_to_jamo, h2j, j2h

kakasi = kakasi()
kakasi.setMode("H","a") # default: Hiragana no conversion
kakasi.setMode("K","a") # default: Katakana no conversion
kakasi.setMode("J","a") # default: Japanese no conversion
kakasi.setMode("r","Hepburn") # default: use Hepburn Roman table
kakasi.setMode("C", True) # add space default: no Separator
kakasi.setMode("c", False) # capitalize default: no Capitalize

wakati = wakati()

#from .jp_dictionary import english_dictionary, etc_dictionary

PAD = '_'
EOS = '~'
PUNC = '!\'(),-.:;?'
SPACE = ' '

JAMO_LEADS = "".join([chr(_) for _ in range(0x1100, 0x1113)])
JAMO_VOWELS = "".join([chr(_) for _ in range(0x1161, 0x1176)])
JAMO_TAILS = "".join([chr(_) for _ in range(0x11A8, 0x11C3)])

VALID_CHARS = JAMO_LEADS + JAMO_VOWELS + JAMO_TAILS + PUNC + SPACE
ALL_SYMBOLS = PAD + EOS + VALID_CHARS

char_to_id = {c: i for i, c in enumerate(ALL_SYMBOLS)}
id_to_char = {i: c for i, c in enumerate(ALL_SYMBOLS)}

quote_checker = """([`"'＂“‘])(.+?)([`"'＂”’])"""

def is_lead(char):
    return char in JAMO_LEADS

def is_vowel(char):
    return char in JAMO_VOWELS

def is_tail(char):
    return char in JAMO_TAILS

def get_mode(char):
    if is_lead(char):
        return 0
    elif is_vowel(char):
        return 1
    elif is_tail(char):
        return 2
    else:
        return -1

def _get_text_from_candidates(candidates):
    if len(candidates) == 0:
        return ""
    elif len(candidates) == 1:
        return _jamo_char_to_hcj(candidates[0])
    else:
        return j2h(**dict(zip(["lead", "vowel", "tail"], candidates)))

def jamo_to_korean(text):
    text = h2j(text)

    idx = 0
    new_text = ""
    candidates = []

    while True:
        if idx >= len(text):
            new_text += _get_text_from_candidates(candidates)
            break

        char = text[idx]
        mode = get_mode(char)

        if mode == 0:
            new_text += _get_text_from_candidates(candidates)
            candidates = [char]
        elif mode == -1:
            new_text += _get_text_from_candidates(candidates)
            new_text += char
            candidates = []
        else:
            candidates.append(char)

        idx += 1
    return new_text

num_to_jpn = {
        '0': 'ゼロ',
        '1': 'いち',
        '2': 'に',
        '3': 'さん',
        '4': 'よん',
        '5': 'ご',
        '6': 'ろく',
        '7': 'しち',
        '8': 'はち',
        '9': 'きゅう',
}

unit_to_jpn1 = {
        '%': 'パーセント',
        'cm': 'センチメートル',
        'mm': 'ミリメートル',
        'km': 'キロメートル',
        'kg': 'キログラム',
}
unit_to_jpn2 = {
        'm': 'メートル',
}

upper_to_jpn = {
        'A': 'エイ',
        'B': 'ビー',
        'C': 'シー',
        'D': 'ディー',
        'E': 'イー',
        'F': 'エフ',
        'G': 'ジー',
        'H': 'エイチ',
        'I': 'アイ',
        'J': 'ジェイ',
        'K': 'ケイ',
        'L': 'エル',
        'M': 'エム',
        'N': 'エヌ',
        'O': 'オー',
        'P': 'ピー',
        'Q': 'キュー',
        'R': 'アール',
        'S': 'エス',
        'T': 'ティー',
        'U': 'ユー',
        'V': 'ヴィー',
        'W': 'ダブリュー',
        'X': 'エックス',
        'Y': 'ワイ',
        'Z': 'ズィー',
}

def compare_sentence_with_jamo(text1, text2):
    return h2j(text1) != h2j(text)

def tokenize(text, as_id=False):
    text = normalize(text)
    tokens = list(hangul_to_jamo(text))

    if as_id:
        return [char_to_id[token] for token in tokens] + [char_to_id[EOS]]
    else:
        return [token for token in tokens] + [EOS]

def tokenizer_fn(iterator):
    return (token for x in iterator for token in tokenize(x, as_id=False))

def normalize(text):
    text = text.strip()

    text = re.sub('\(\d+日\)', '', text)
    text = re.sub('\([⺀-⺙⺛-⻳⼀-⿕!！々〇〡-〩〸-〺〻㐀-䶵一-鿃豈-鶴侮-頻並-龎]+\)', '', text)

    text = normalize_kanji(text)

#    text = normalize_with_dictionary(text, etc_dictionary)
    text = normalize_english(text)
    text = re.sub('[a-zA-Z]+', normalize_upper, text)

    text = normalize_quote(text)
    text = normalize_number(text)

    return text

def normalize_kanji(text):
    text = jaconv.z2h(text, kana=False, digit=True, ascii=True)
    print(text)
    text = jaconv.normalize(text, 'NFKC')
    conv = kakasi.getConverter()
    text = conv.do(text)
    m = re.match('\w+', text)
    text = m.group()
    print(text)
    text = jaconv.alphabet2kana(text.lower())
    text = jaconv.kata2hira(text)
    text = jaconv.alphabet2kana(text)
    print(text)
    return text


def normalize_with_dictionary(text, dic):
    if any(key in text for key in dic.keys()):
        pattern = re.compile('|'.join(re.escape(key) for key in dic.keys()))
        return pattern.sub(lambda x: dic[x.group()], text)
    else:
        return text

def normalize_english(text):
    def fn(m):
        word = m.group()
        if word in english_dictionary:
            return english_dictionary.get(word)
        else:
            return word

    text = re.sub("([A-Za-z]+)", fn, text)
    return text

def normalize_upper(text):
    text = text.group(0)

    if all([char.isupper() for char in text]):
        return "".join(upper_to_kor[char] for char in text)
    else:
        return text

def normalize_quote(text):
    def fn(found_text):
        from nltk import sent_tokenize # NLTK doesn't along with multiprocessing

        found_text = found_text.group()
        unquoted_text = found_text[1:-1]

        sentences = sent_tokenize(unquoted_text)
        return " ".join(["'{}'".format(sent) for sent in sentences])

    return re.sub(quote_checker, fn, text)

number_checker = "([+-]?!\d[\d,]*)[\.]?\d*"
count_checker = "(時|名|가지|歳|匹|포기|송이|수|톨|통|점|개|벌|척|채|다발|그루|자루|줄|켤레|그릇|잔|마디|상자|사람|곡|병|판)"

def normalize_number(text):
    text = normalize_with_dictionary(text, unit_to_jpn1)
    text = normalize_with_dictionary(text, unit_to_jpn2)
    text = re.sub(number_checker + count_checker,
            lambda x: number_to_japanese(x, True), text)
    text = re.sub(number_checker,
            lambda x: number_to_japanese(x, False), text)
    return text

num_to_kor1 = [""] + list("일이삼사오육칠팔구")
num_to_kor2 = [""] + list("만억조경해")
num_to_kor3 = [""] + list("십백천")

#count_to_kor1 = [""] + ["하나","둘","셋","넷","다섯","여섯","일곱","여덟","아홉"]
count_to_jpn1 = [""] + ["한","두","세","네","다섯","여섯","일곱","여덟","아홉"]

count_tenth_dict = {
        "십": "열",
        "두십": "스물",
        "세십": "서른",
        "네십": "마흔",
        "다섯십": "쉰",
        "여섯십": "예순",
        "일곱십": "일흔",
        "여덟십": "여든",
        "아홉십": "아흔",
}



def number_to_japanese(num_str, is_count=False):
    if is_count:
        num_str, unit_str = num_str.group(1), num_str.group(2)
    else:
        num_str, unit_str = num_str.group(), ""
    
    num_str = num_str.replace(',', '')
    num = ast.literal_eval(num_str)

    if num == 0:
        return "영"

    check_float = num_str.split('.')
    if len(check_float) == 2:
        digit_str, float_str = check_float
    elif len(check_float) >= 3:
        raise Exception(" [!] Wrong number format")
    else:
        digit_str, float_str = check_float[0], None

    if is_count and float_str is not None:
        raise Exception(" [!] `is_count` and float number does not fit each other")

    digit = int(digit_str)

    if digit_str.startswith("-"):
        digit, digit_str = abs(digit), str(abs(digit))

    jpn = ""
    size = len(str(digit))
    tmp = []

    for i, v in enumerate(digit_str, start=1):
        v = int(v)

        if v != 0:
            if is_count:
                tmp += count_to_jpn1[v]
            else:
                tmp += num_to_jpn1[v]

            tmp += num_to_jpn3[(size - i) % 4]

        if (size - i) % 4 == 0 and len(tmp) != 0:
            jpn += "".join(tmp)
            tmp = []
            jpn += num_to_kor2[int((size - i) / 4)]

    if is_count:
        if jpn.startswith("한") and len(kor) > 1:
            jpn = jpn[1:]

        if any(word in jpn for word in count_tenth_dict):
            jpn = re.sub(
                    '|'.join(count_tenth_dict.keys()),
                    lambda x: count_tenth_dict[x.group()], jpn)

    if not is_count and jpn.startswith("일") and len(jpn) > 1:
        jpn = jpn[1:]

    if float_str is not None:
        jpn += "テン "
        jpn += re.sub('\d', lambda x: num_to_jpn[x.group()], float_str)

    if num_str.startswith("+"):
        jpn = "プラス " + jpn
    elif num_str.startswith("-"):
        jpn = "マイナス " + jpn

    return kor + unit_str

if __name__ == "__main__":
    def test_normalize(text):
        print(text)
        print(normalize(text))
        print("="*30)

    test_normalize("美希は美希だから１番可愛いなの！！")
