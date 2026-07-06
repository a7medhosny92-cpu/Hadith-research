"""Normalizzazione robusta per nomi di narratori arabi.

Gestisce varianti ortografiche, kunya, titoli, e forme abbreviate.
"""

import re
from functools import lru_cache

# Mappa di unificazione caratteri arabi
CHAR_MAP = {
    'ة': 'ه',
    'ى': 'ي',
    'ئ': 'ي',
    'ؤ': 'و',
    'أ': 'ا',
    'إ': 'ا',
    'آ': 'ا',
}

# Parole da rimuovere (titoli, onorifici, particelle)
REMOVE_WORDS = {
    'رضي', 'عنه', 'عنها', 'عنهما', 'عنهم',
    'رحمه', 'رحمها', 'رحمهما', 'رحمهم',
    'ت', 'ق', 'ه', 'د',  # abbreviazioni di ترحم/ق/ه/د
    'المعروف', 'الملقب', 'لقبه', 'يعرف',
    'شيخ', 'شيخه', 'تلميذ', 'تلميذه',
    'لا يعرف', 'مجهول', 'لم يرو عنه',
    'ابو', 'ابي', 'ابن', 'بن', 'بنت', 'ابنة',  # relazioni
}

# Frasi di benedizione da rimuovere interamente
BLESSING_PHRASES = {
    'رضي الله عنه',
    'رضي الله عنها',
    'رضي الله عنهما',
    'رضي الله عنهم',
    'رحمه الله',
    'رحمهما الله',
    'رحمهم الله',
}

# Parole di relazione (gestite separatamente)
RELATION_WORDS = {'بن', 'ابن', 'بنت', 'ابنة', 'مولى', 'مولاة', 'حليف', 'حليفة'}

# Kunya patterns
KUNYA_PREFIXES = {'أبو', 'ابو', 'أم', 'ام'}


@lru_cache(maxsize=50000)
def normalize_name(name: str) -> str:
    """
    Normalizza un nome di narratore in forma canonica.

    Esempi:
    - "عبد الله بن عمر بن الخطاب" → "عبدالله عمر الخطاب"
    - "نافع مولى ابن عمر" → "نافع مولى عمر"
    - "أبو هريرة" → "kunya_هريرة"
    - "سفيان ابن سعيد الثوري" → "سفيان سعيد ثوري"
    """
    if not name:
        return ""

    # 1. Unifica caratteri
    result = name
    for old, new in CHAR_MAP.items():
        result = result.replace(old, new)

    # 2. Rimuovi diacritici (tashkeel)
    result = re.sub(r'[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06DC\u06DF-\u06E8\u06EA-\u06ED]', '', result)

    # 3. Rimuovi frasi di benedizione
    for phrase in BLESSING_PHRASES:
        result = result.replace(phrase, '')

    # 4. Rimuovi spazi multipli
    result = re.sub(r'\s+', ' ', result).strip()

    # 5. Gestisci kunya
    tokens = result.split()
    if tokens and tokens[0] in KUNYA_PREFIXES and len(tokens) > 1:
        kunya_name = tokens[1]
        return f"kunya_{kunya_name}"

    # 6. Rimuovi parole di relazione e parole da rimuovere
    clean_tokens = []
    for token in tokens:
        if token in REMOVE_WORDS:
            continue
        clean_tokens.append(token)

    # 7. Unisci token separati che dovrebbero essere uniti (es. "عبد" + "الله" → "عبدالله")
    # Questo accade quando "بن" viene rimosso tra due token
    merged_tokens = []
    i = 0
    while i < len(clean_tokens):
        if i + 1 < len(clean_tokens):
            # Unisci se il primo token è breve (2-3 caratteri) e potrebbe essere parte di un nome composto
            if len(clean_tokens[i]) <= 3 and clean_tokens[i] in ['عبد', 'ابو', 'ام']:
                merged = clean_tokens[i] + clean_tokens[i+1]
                merged_tokens.append(merged)
                i += 2
                continue
        merged_tokens.append(clean_tokens[i])
        i += 1

    return ' '.join(merged_tokens)


@lru_cache(maxsize=50000)
def normalize_for_network(name: str) -> str:
    """
    Normalizzazione specifica per il network شيوخ/تلاميذ.
    Più aggressiva: rimuove anche nisba e titoli.
    """
    base = normalize_name(name)

    # Rimuovi nisba (attributi geografici/tribali)
    nisba_patterns = [
        r'\b(?:ال)?(?:مكي|مدني|بصري|كوفي|دمشقي|حمصي|مصري|فارسي|عراقي|حجازي|قرشي|عدوي|ثوري|زهري|اموي|عباسي|هاشمي|انصاري|اسدي|تيمي|مخزومي|جمحي|سهمي|فهري|عامري|ازدي|ثقفي|بجلي|خزاعي|تميمي|مخزومي|قرشي|عدوي|انصاري)\b',
    ]
    for pattern in nisba_patterns:
        base = re.sub(pattern, '', base, flags=re.IGNORECASE)

    return re.sub(r'\s+', ' ', base).strip()


def get_name_variants(name: str) -> list[str]:
    """
    Restituisce tutte le varianti plausibili di un nome.
    Utile per fuzzy matching.
    """
    variants = set()
    normalized = normalize_name(name)
    variants.add(normalized)

    # Aggiungi varianti con token uniti (es. "عبد" + "الله" → "عبدالله")
    tokens = normalized.split()
    for i in range(len(tokens) - 1):
        merged = tokens[:i] + [tokens[i] + tokens[i+1]] + tokens[i+2:]
        variants.add(' '.join(merged))

    # Aggiungi varianti con token separati (es. "عبدالله" → "عبد الله")
    for i, token in enumerate(tokens):
        if len(token) > 4:  # solo token lunghi
            # Semplice euristica: prova a separare dopo 3 caratteri
            for split_pos in range(2, len(token) - 1):
                part1 = token[:split_pos]
                part2 = token[split_pos:]
                if len(part1) >= 2 and len(part2) >= 2:
                    separated = tokens[:i] + [part1, part2] + tokens[i+1:]
                    variants.add(' '.join(separated))

    return list(variants)


def fuzzy_match_score(name1: str, name2: str) -> float:
    """
    Calcola score di similarità tra due nomi normalizzati.
    Restituisce float tra 0.0 e 1.0 usando Jaccard similarity.
    """
    n1 = set(normalize_name(name1).split())
    n2 = set(normalize_name(name2).split())

    if not n1 or not n2:
        return 0.0

    intersection = n1 & n2
    union = n1 | n2

    # Jaccard similarity
    return len(intersection) / len(union) if union else 0.0


@lru_cache(maxsize=50000)
def fuzzy_match_score_cached(name1: str, name2: str) -> float:
    """
    Versione cached di fuzzy_match_score per performance.
    """
    return fuzzy_match_score(name1, name2)


def fuzzy_match_score_with_variants(name1: str, name2: str) -> float:
    """
    Calcola score di similarità considerando anche varianti dei nomi.
    Restituisce il massimo score trovato tra tutte le combinazioni.
    """
    variants1 = get_name_variants(name1)
    variants2 = get_name_variants(name2)

    max_score = 0.0
    for v1 in variants1:
        for v2 in variants2:
            score = fuzzy_match_score_cached(v1, v2)
            max_score = max(max_score, score)

    return max_score


if __name__ == "__main__":
    # Test
    test_names = [
        "عبد الله بن عمر بن الخطاب",
        "عبدالله بن عمر",
        "نافع مولى ابن عمر",
        "نافع مولى عمر",
        "أبو هريرة",
        "سفيان ابن سعيد الثوري",
    ]

    print("=== TEST NORMALIZZAZIONE ===")
    for name in test_names:
        normalized = normalize_name(name)
        network_norm = normalize_for_network(name)
        print(f"Nome: {name}")
        print(f"  Normalizzato: {normalized}")
        print(f"  Network: {network_norm}")
        print()

    print("=== TEST FUZZY MATCH ===")
    pairs = [
        ("عبد الله بن عمر", "عبدالله عمر"),
        ("نافع مولى ابن عمر", "نافع مولى عمر"),
        ("سفيان الثوري", "سفيان بن سعيد"),
    ]

    for n1, n2 in pairs:
        score = fuzzy_match_score(n1, n2)
        score_variants = fuzzy_match_score_with_variants(n1, n2)
        print(f"'{n1}' vs '{n2}'")
        print(f"  Score base: {score:.3f}")
        print(f"  Score con varianti: {score_variants:.3f}")
        print()
