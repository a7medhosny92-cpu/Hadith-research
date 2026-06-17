"""Structural عِلّة/شذوذ detection from the gathered طرق (ROADMAP #7)."""

from __future__ import annotations

from app.qa.illal import detect_structural_illal


def _group(companion, variants):
    return {"companion": companion, "count": sum(v["count"] for v in variants), "variants": variants}


def _variant(count, label, narrations=None):
    return {"count": count, "label": label, "narrations": narrations or []}


def test_tafarrud_single_companion_is_flagged():
    tak = {"total": 3, "companions": 1,
           "groups": [_group("أبو هريرة", [_variant(3, "بلفظه")])]}
    hints = detect_structural_illal(tak, check_raf_waqf=False)
    assert any(h["type"] == "تفرّد" and "أبو هريرة" in h["note"] for h in hints)


def test_no_parallel_is_gharib():
    hints = detect_structural_illal({"total": 0, "companions": 0, "groups": []}, check_raf_waqf=False)
    assert any(h["type"] == "تفرّد" for h in hints)


def test_lone_bymeaning_wording_against_the_many_is_shudhudh():
    tak = {"total": 5, "companions": 2, "groups": [
        _group("عبد الله بن عمر", [_variant(4, "بلفظه"), _variant(1, "بمعناه")]),
        _group("أنس بن مالك", [_variant(1, "بلفظه")])]}
    hints = detect_structural_illal(tak, check_raf_waqf=False)
    assert any(h["type"] == "شذوذ" for h in hints)
    # a well-attested report with NO lone divergent wording is not flagged شذوذ
    clean = {"total": 4, "companions": 1, "groups": [
        _group("أنس بن مالك", [_variant(4, "بلفظه")])]}
    assert not any(h["type"] == "شذوذ" for h in detect_structural_illal(clean, check_raf_waqf=False))


def test_raf_waqf_split_is_flagged_conservatively():
    marfu = {"isnad": "حدثنا أحمد عن أبي هريرة", "matn": "عن النبي ﷺ قال إنما الأعمال بالنيات"}
    mawquf = {"isnad": "حدثنا أحمد عن عمر بن الخطاب", "matn": "قال عمر إنما الأعمال بالنيات"}
    tak = {"total": 4, "companions": 1, "groups": [
        _group("أبو هريرة", [_variant(2, "بلفظه", [marfu, marfu]),
                              _variant(2, "بمعناه", [mawquf, mawquf])])]}
    hints = detect_structural_illal(tak)
    assert any(h["type"] == "رفع ووقف" for h in hints)
    # all-marfu (no split) → no رفع/وقف hint
    allm = {"total": 4, "companions": 1, "groups": [
        _group("أبو هريرة", [_variant(4, "بلفظه", [marfu, marfu, marfu, marfu])])]}
    assert not any(h["type"] == "رفع ووقف" for h in detect_structural_illal(allm))
