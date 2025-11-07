import re

import hunspell


def clean_and_extract_words(text: str) -> tuple[list[str], set[str]]:
    """Extract clean words from OCR and convert to base/dictionary forms

    Returns:
    Tuple of (clean_words, ambiguities)
    - clean words: list of base forms
    - ambiguities: list of dicts with word, stems, and chosen stem.
    """

    # Originally "-" was omitted, but that sometimes shows up in real words
    # (кое-что, for example), so I removed it from this regular expression.
    # However, the "|" expression is to recombine words that have been
    # split across different lines.
    text = re.sub(r'[|^_$—\'\",.!?;:«»]|(\-\s)', '', text)

    print(f"after: {text}")
    words = re.findall(r'[а-яё]+', text, re.IGNORECASE)

    h = hunspell.HunSpell(
        "/Users/brendan/Library/spelling/ru_RU.dic",
        "/Users/brendan/Library/spelling/ru_RU.aff",
    )

    seen = set()
    non_words = set()

    for word in words:
        if len(word) <= 1:
            continue

        # All integrations with hunspell are very old and don't automatically
        # handle the bytes -> strings conversion automatically
        stems = [stem.decode('utf-8') if isinstance(stem, bytes) else stem for
            stem in h.stem(word)]
        if len(stems) == 0:
            possible_words = check_common_ocr_errors(word)
            if not possible_words:
                non_words.add(word)
            else:
                stems = list(possible_words)

        for stem in stems:
            if stem not in seen and stem not in non_words:
                seen.add(stem)

    # Do I need to convert to list?
    return list(seen), non_words

# Key assumptions:
# Only one character is misread due to markers indicating stress.
# Accent marks are never given as a word (allows us to check each
# characters like an array without worrying about compound UTF-8 characters).
def check_common_ocr_errors(word: str) -> set[str]:
    common_errors = {
        'б': 'о', # о with an accent mark sometimes gets interpreted as б
        '0': 'о', # sometimes, bold o is interpreted as BIG and therefore a 0
        'О': 'о', # same reason as 0
        'ё': 'е', # stressed е can sometimes be misread as ё
        'й': 'и', # stressed и can sometimes be misread as й
        'э': 'з', # Wow. These look REALLY similar.
        'з': 'э',
        'ж': '', # Sometimes the janky quote mark gets treated as a ж.
        'ф': '',
        'Ф': '', # The "French style" quotes are rendered as an Ф sometimes?!
    }

    h = hunspell.HunSpell(
        "/Users/brendan/Library/spelling/ru_RU.dic",
        "/Users/brendan/Library/spelling/ru_RU.aff",
    )

    possible_words = set()

    for i, char in enumerate(word):
        if char in common_errors:
            replacement_char = common_errors[char]
            suffix = ''
            prefix = ''
            if i > 0:
                prefix = word[:i]
            if i < len(word) - 1:
               suffix = word[i+1:]

            variant = prefix + replacement_char + suffix
            print(f"checking {variant}")
            stems = [stem.decode('utf-8') if isinstance(stem, bytes) else stem for
                     stem in h.stem(variant)]

            for stem in stems:
                possible_words.add(stem)

    return possible_words
