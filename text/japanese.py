# Code based on 

import re
import os
import ast
import json
import jaconv
from pykakasi import kakasi,wakati
#from .jp_dictionary import english_dictionary, etc_dictionary

#For Making Kana to English
kakasi = kakasi()
wakati = wakati()


PAD = '_'
EOS = '~'
PUNC = '!\'(),-.:;?'
SPACE = ' '



HIRAGANA = "".join([chr(_) for _ in range(0x3040, 0x309F)])
KATAKANA = "".join([chr(_) for _ in range(0x30A0, 0x30FF)])
VALID_CHARS = HIRAGANA + KATAKANA + PUNC + SPACE
ALL_SYMBOLS = PAD + EOS + VALID_CHARS


quote_checker = """([`"'＂“‘])(.+?)([`"'＂”’])"""


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
#    tokens = list(hangul_to_jamo(text))
    tokens = list()
    for kana in text:
        tokens.append(kana)
    
    i = 0
    
#    while i+1 < len(tokens):
#        if tokens[i+1] == 'ゃ':
#            tokens[i] = tokens[i] + tokens[i+1]
#            del tokens[i+1]
#        elif tokens[i+1] == 'ゅ':
#            tokens[i] = tokens[i] + tokens[i+1]
#            del tokens[i+1]
#        elif tokens[i+1] == 'ょ':
#            tokens[i] = tokens[i] + tokens[i+1]
#            del tokens[i+1]
#        elif tokens[i+1] == 'ぁ':
#            tokens[i] = tokens[i] + tokens[i+1]
#            del tokens[i+1]
#        elif tokens[i+1] == 'ぃ':
#            tokens[i] = tokens[i] + tokens[i+1]
#            del tokens[i+1]
#        elif tokens[i+1] == 'ぅ':
#            tokens[i] = tokens[i] + tokens[i+1]
#            del tokens[i+1]
#        elif tokens[i+1] == 'ぇ':
#            tokens[i] = tokens[i] + tokens[i+1]
#            del tokens[i+1]
#        elif tokens[i+1] == 'ぉ':
#            tokens[i] = tokens[i] + tokens[i+1]
#        elif tokens[i+1] == 'ん':
#            tokens[i] = tokens[i] + tokens[i+1]
#            del tokens[i+1]
#        i = i+1

    
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


#    text = normalize_with_dictionary(text, etc_dictionary)
    text = normalize_english(text)
    text = re.sub('[a-zA-Z]+', normalize_upper, text)

    text = normalize_kanji(text)
    text = normalize_quote(text)

    return text

def normalize_kanji(text):

#    kakasi.setMode("H","a") # default: Hiragana no conversion
    kakasi.setMode("K","a") # default: Katakana no conversion
    kakasi.setMode("J","a") # default: Japanese no conversion
    kakasi.setMode("r","Hepburn") # default: use Hepburn Roman table
    kakasi.setMode("C", True) # add space default: no Separator
    kakasi.setMode("c", False) # capitalize default: no Capitalize
    
    
    text = jaconv.z2h(text, kana=False, digit=True, ascii=True)
    text = jaconv.normalize(text, 'NFKC')
    text = normalize_number(text)
    conv = kakasi.getConverter()
    text = conv.do(text)
    text = text.replace("tsu","t")
    text = re.sub('[-=.#!/?:$}、！。「」・☆●｀]','', text)
    text = jaconv.alphabet2kana(text.lower())
    text = jaconv.kata2hira(text)
    text = jaconv.alphabet2kana(text)
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
        return "".join(upper_to_jpn[char] for char in text)
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

number_checker = "([+-]?\d[\d,]*)[\.]?\d*"

def normalize_number(text):
    text = normalize_with_dictionary(text, unit_to_jpn1)
    text = normalize_with_dictionary(text, unit_to_jpn2)
    text = re.sub(number_checker,
            lambda x: number_to_japanese(x, False), text)
    return text

num_to_jpn1 = [""] + list("一二三四五六七八九")
num_to_jpn2 = [""] + list("万億兆京垓")
num_to_jpn3 = [""] + list("十百千")

count_to_jpn1 = [""] + ["一","二","三","四","五","六","七","八","九"]



def number_to_japanese(num_str, is_count=False):
    if is_count:
        num_str, unit_str = num_str.group(1), num_str.group(2)
    else:
        num_str, unit_str = num_str.group(), ""
    
    num_str = num_str.replace(',', '')
    num = ast.literal_eval(num_str)

    if num == 0:
        return "ゼロ"

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

#Make arabic number to Kanji
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
            jpn += num_to_jpn2[int((size - i) / 4)]

    if is_count:
        if jpn.startswith("一") and len(jpn) > 1:
            jpn = jpn[1:]

    if not is_count and jpn.startswith("一") and len(jpn) > 1:
        jpn = jpn[1:]

    if float_str is not None:
        jpn += "テン "
        jpn += re.sub('\d', lambda x: num_to_jpn[x.group()], float_str)

    if num_str.startswith("+"):
        jpn = "プラス " + jpn
    elif num_str.startswith("-"):
        jpn = "マイナス " + jpn

    return jpn + unit_str

if __name__ == "__main__":
    def test_normalize(text):
        print(text)
        print(tokenize(text))
        print("="*30)

    test_normalize("プロヂューサー！、行ってくるね。美希は美希だから１番可愛いなの、あはっ☆！！")
    test_normalize("ちょっと待ってください、先生。")
    test_normalize("美希の方が十倍、いや、20倍、いや、１００倍好きだよ〜")
    test_normalize("１０回１００回１０００回１００００回１００００００００回")
