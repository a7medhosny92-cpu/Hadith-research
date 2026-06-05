from app.parsing.grading import extract_grade
from app.parsing.hadith_extract import iter_hadith
from app.parsing.html_clean import (
    arabic_digits_to_int,
    clean_body,
    extract_titles,
    remove_footnote_refs,
    split_footnotes,
)
from app.parsing.isnad_matn import split_isnad_matn


# ── html_clean ────────────────────────────────────────────────────────────────
def test_arabic_digits():
    assert arabic_digits_to_int("١٢٣") == 123
    assert arabic_digits_to_int("[٧]") == 7
    assert arabic_digits_to_int("لا") is None


def test_extract_titles_and_clean_body():
    text = "<span data-type='title' id=toc-5>١ - باب النية</span> متن الحديث (^١)"
    # the heading is captured separately …
    assert extract_titles(text) == ["١ - باب النية"]
    # … and removed from the body (along with tags and footnote refs)
    assert clean_body(text) == "متن الحديث"


def test_remove_footnote_refs_keeps_diacritics():
    assert remove_footnote_refs("إِنَّمَا (^١٢) الْأَعْمَالُ") == "إِنَّمَا  الْأَعْمَالُ"


def test_split_footnotes():
    body, foot = split_footnotes("المتن\n_________\n(^١) حاشية")
    assert body.strip() == "المتن"
    assert "حاشية" in foot


# ── isnad / matn ─────────────────────────────────────────────────────────────
def test_split_by_quote():
    text = 'حدثنا فلان، قال: سمعت رسول الله ﷺ يقول: "إنما الأعمال بالنيات"'
    isnad, matn, conf = split_isnad_matn(text)
    assert conf == "quote"
    assert matn == "إنما الأعمال بالنيات"
    assert isnad.startswith("حدثنا فلان")


def test_split_by_phrase_when_no_quote():
    text = "حدثنا فلان، عن عائشة، أنها قالت: كان النبي ﷺ يفعل كذا"
    isnad, matn, conf = split_isnad_matn(text)
    assert conf == "phrase"
    assert matn == "كان النبي ﷺ يفعل كذا"
    assert "عائشة" in isnad


# ── grading ──────────────────────────────────────────────────────────────────
def test_grade_in_context():
    assert extract_grade("... إسناده صحيح على شرط مسلم") == "صحيح"
    assert extract_grade("قال الترمذي: حسن صحيح") == "حسن صحيح"
    assert extract_grade("الحكم: [ضعيف]") == "ضعيف"


def test_no_false_positive_grade():
    # صحيح used as an adjective in the matn, not a ruling
    assert extract_grade("هذا طريق صحيح وواضح للسالكين") is None


# ── end-to-end extraction across pages ───────────────────────────────────────
FIXTURE_PAGES = [
    {
        "pg": 10,
        "meta": {"vol": "1", "page": 100, "headings": []},
        "text": (
            "<span data-type='title' id=toc-5>١ - باب النية</span>\n"
            '• [١] حدثنا الحميدي، قال: حدثنا سفيان، عن عمر، قال: سمعت رسول الله ﷺ '
            'يقول: "إنما الأعمال بالنيات (^١)\n'
            "_________\n(^١) تعليق المحقق."
        ),
    },
    {
        "pg": 11,
        "meta": {"vol": "1", "page": 101, "headings": []},
        "text": (
            'وإنما لكل امرئ ما نوى".\n'
            "• [٢] حدثنا قتيبة، عن عائشة، أنها قالت: كان النبي ﷺ يصلي. إسناده صحيح\n"
            "_________\n* [٢] [التحفة: ١٢٣]"
        ),
    },
]


def test_iter_hadith_end_to_end():
    hadiths = list(iter_hadith(7485, FIXTURE_PAGES))
    assert [h.number for h in hadiths] == [1, 2]

    h1 = hadiths[0]
    assert h1.chapter == "١ - باب النية"
    assert h1.volume == "1" and h1.page == 100  # citation = where it starts
    assert h1.matn_confidence == "quote"
    # matn was reassembled across the page break, footnote text excluded
    assert h1.matn == "إنما الأعمال بالنيات وإنما لكل امرئ ما نوى"
    assert "تعليق" not in h1.text
    assert h1.isnad.startswith("حدثنا الحميدي")

    h2 = hadiths[1]
    assert h2.page == 101
    assert h2.matn_confidence == "phrase"
    assert h2.grade == "صحيح"
    assert "التحفة" not in h2.text  # takhrij note lived in the footnotes, excluded
