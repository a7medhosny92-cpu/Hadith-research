"""Tests for the تهذيب الكمال (al-Mizzī) prose رجال extractor.

The real book (id 3722) is gitignored/ephemeral, so these exercise the pure parser on crafted —
but realistically vocalised — tarjama bodies. See ``docs/TAHDHIB.md`` for the book study.
"""

from __future__ import annotations

from app.parsing.tahdhib_extract import _muqaddima_skip, parse_entry


def test_parse_entry_reads_books_name_kunya_network_and_verdict():
    body = (
        "خ م ق: عُثْمَانُ بْنُ مُحَمَّدٍ العَبْسِيُّ، أَبُو الحَسَنِ بْنُ أَبِي شَيْبَةَ الكُوفِيُّ. "
        "رَوَى عَن: أَحْمَدَ بْنِ إِسْحَاقَ (م)، وجَرِيرِ بْنِ عَبْدِ الحَمِيدِ. "
        "رَوَى عَنه: البُخَارِيُّ، ومُسْلِمٌ، وابْنُ مَاجَهْ. "
        "قَالَ ابْنُ مَعِينٍ: ثِقَةٌ."
    )
    r = parse_entry(3857, body)
    assert r["books"] == ["خ", "م", "ق"]                          # the rumūz (Six-Books symbols)
    assert r["name"].startswith("عُثْمَانُ بْنُ مُحَمَّدٍ")        # name stops before «رَوَى عَن:»
    assert r["kunya"].startswith("أَبُو الحَسَن")
    assert len(r["shuyukh"]) == 2 and any("أَحْمَد" in s for s in r["shuyukh"])
    assert r["talamidh"] == ["البُخَارِيُّ", "مُسْلِمٌ", "ابْنُ مَاجَهْ"]    # his real students
    assert any("ثِقَة" in v for v in r["verdicts"])               # diacritised grade word matched


def test_parse_entry_handles_the_abbreviated_an_colon_form():
    # minor narrators use «عَن:» / «وعَنه:» (not the full «رَوَى عَن:») — both must open the blocks
    # and the bare chain word «عَنْ فلان» (no colon) must NOT be mistaken for the opener.
    body = "د س: بِشْرُ بْنُ سَحِيمٍ الغِفَارِيُّ، لَهُ صُحْبَةٌ. عَن: النَّبِيِّ ﷺ. وعَنه: عَلِيُّ بْنُ أَبِي طَالِبٍ."
    r = parse_entry(688, body)
    assert r["name"].startswith("بِشْرُ بْنُ سَحِيمٍ")             # the bio did not swallow the name
    assert r["shuyukh"] and r["talamidh"]


def test_parse_entry_rejects_a_too_short_body():
    assert parse_entry(1, "خ م") is None


def test_muqaddima_skip_lands_on_the_dense_rumuz_run():
    # the محقق's ~200-page intro carries non-rumūz numbered points; the dictionary proper is a
    # dense run of rumūz-bearing entries. The skip jumps over the intro to that run.
    assert _muqaddima_skip([True] * 20) == 0                      # all narrators → no skip
    assert 25 <= _muqaddima_skip([False] * 30 + [True] * 20) <= 30   # 30 intro items → skip them
    assert _muqaddima_skip([False] * 5) == 0                      # too short to decide → start at 0
