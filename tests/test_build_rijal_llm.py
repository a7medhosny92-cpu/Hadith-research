"""Tests for the LLM-assisted build tool — the pure, no-LLM guardrails: faithfulness validation,
the chain-suspicion heuristic, and the cache. (The LLM call itself is exercised on the user's
machine with their engine; here we prove that an unfaithful answer can never slip through.)"""

from __future__ import annotations

from scripts.build_rijal_llm import (
    Cache, chain_is_suspicious, validate_chain, validate_rijal,
)

_RIJAL_SRC = ("مالك بن أنس الأصبحي أبو عبد الله الإمام عن نافع والزهري "
              "وعنه ابن مهدي وابن القاسم توفي سنة تسع وسبعين ومائة")


def test_validate_rijal_keeps_faithful_record_with_network():
    rec = validate_rijal(
        {"name": "مالك بن أنس", "kunya": "أبو عبد الله", "grade_word": "الإمام",
         "death_year": 179, "shuyukh": ["نافع", "الزهري"], "talamidh": ["ابن مهدي", "ابن القاسم"]},
        _RIJAL_SRC,
    )
    assert rec is not None
    assert rec["category"] == "ثقة"                       # «الإمام» → ثقة
    assert rec["shuyukh"] == ["نافع", "الزهري"]           # «الزهري» kept despite source «والزهري»
    assert rec["talamidh"] == ["ابن مهدي", "ابن القاسم"]
    assert rec["source_text"] == _RIJAL_SRC               # the proof is kept alongside


def test_validate_rijal_rejects_invented_grade():
    # «كذاب» does not occur in the tarjama → an invented verdict, must be refused (→ keep the regex)
    assert validate_rijal({"name": "مالك", "grade_word": "كذاب"}, _RIJAL_SRC) is None
    # invented company is dropped, not kept
    rec = validate_rijal({"name": "مالك", "grade_word": "ثقة" if False else None,
                          "shuyukh": ["شعبة بن الحجاج"]}, _RIJAL_SRC)
    assert rec is not None and rec["shuyukh"] == []       # شعبة isn't in the source → dropped
    assert validate_rijal({"name": "", "grade_word": "ثقة"}, _RIJAL_SRC) is None


_CHAIN = "حدثنا قتيبة حدثنا مالك عن نافع عن ابن عمر قال قال رسول الله إنما الأعمال بالنيات"


def test_validate_chain_requires_verbatim_reconstruction():
    good = validate_chain(
        {"isnad": "حدثنا قتيبة حدثنا مالك عن نافع عن ابن عمر",
         "matn": "قال قال رسول الله إنما الأعمال بالنيات",
         "narrators": ["قتيبة", "مالك", "نافع", "ابن عمر"]}, _CHAIN)
    assert good is not None and good["narrators"][-1] == "ابن عمر"
    # a word ADDED to the isnad → reconstruction differs → rejected
    assert validate_chain(
        {"isnad": "حدثنا قتيبة حدثنا مالك الإمام عن نافع عن ابن عمر",
         "matn": "قال قال رسول الله إنما الأعمال بالنيات", "narrators": ["قتيبة"]}, _CHAIN) is None
    # a word LOST from the matn → rejected
    assert validate_chain(
        {"isnad": "حدثنا قتيبة حدثنا مالك عن نافع عن ابن عمر",
         "matn": "إنما الأعمال بالنيات", "narrators": ["قتيبة"]}, _CHAIN) is None
    # a "narrator" not present in the isnad is dropped (and if none remain → rejected)
    assert validate_chain(
        {"isnad": "حدثنا قتيبة حدثنا مالك عن نافع عن ابن عمر",
         "matn": "قال قال رسول الله إنما الأعمال بالنيات", "narrators": ["شعبة"]}, _CHAIN) is None


def test_chain_suspicion_targets_only_the_broken_ones():
    assert not chain_is_suspicious(
        "حدثنا قتيبة عن مالك عن نافع عن ابن عمر عن النبي صلى الله عليه وسلم")   # clean → regex
    assert chain_is_suspicious("عن عائشة جاءت امرأة رفاعة فقالت كنت عند رفاعة")  # matn leak
    assert chain_is_suspicious("عن ابن عباس في قوله تعالى ﴿لا تحرك به لسانك﴾")   # verse leak
    assert chain_is_suspicious("وَ")                                            # 0 narrators


def test_cache_roundtrip_and_deterministic_key(tmp_path):
    c = Cache(tmp_path / "c.db")
    k1 = Cache.key("rijal", "نص")
    assert k1 == Cache.key("rijal", "نص") and k1 != Cache.key("chains", "نص")
    assert c.get(k1) is None
    c.put(k1, {"a": 1})
    assert c.get(k1) == {"a": 1}
