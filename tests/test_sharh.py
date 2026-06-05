"""Tests for sharh (commentary) extraction and hadith linking."""

from __future__ import annotations

from app.parsing.sharh_extract import SHARH_TO_BASE, iter_sharh

# By-number edition (like فتح الباري): a `numbers` index maps hadith → page.
NUMBER_BOOK = {
    "book_id": 1673,  # فتح الباري → base صحيح البخاري (1284)
    "name": "فتح الباري",
    "indexes": {"numbers": {"1": 2, "2": 4}},
    "pages": [
        {"pg": 2, "meta": {"page": 495}, "text": "قوله إنما الأعمال بالنيات شرحه"},
        {"pg": 3, "meta": {"page": 496}, "text": "تتمة شرح الحديث الأول"},
        {"pg": 4, "meta": {"page": 497}, "text": "قوله من كذب علي شرحه"},
        {"pg": 5, "meta": {"page": 498}, "text": "تتمة شرح الحديث الثاني"},
    ],
}

# By-chapter edition (like شرح النووي): no `numbers`, headings drive the split.
CHAPTER_BOOK = {
    "book_id": 1711,  # شرح النووي → base صحيح مسلم (1727)
    "name": "شرح النووي",
    "indexes": {"headings": ["باب الإيمان", "باب الصلاة"]},
    "pages": [
        {"pg": 1, "meta": {"page": 10},
         "text": '<span data-type="title" id=toc-1>باب الإيمان</span>\nشرح الإيمان هنا'},
        {"pg": 2, "meta": {"page": 11}, "text": "تتمة شرح الإيمان"},
        {"pg": 3, "meta": {"page": 12},
         "text": '<span data-type="title" id=toc-2>باب الصلاة</span>\nشرح الصلاة هنا'},
    ],
}


def test_sharh_to_base_mapping():
    assert SHARH_TO_BASE[1673] == 1284   # Fath al-Bari explains Bukhari
    assert SHARH_TO_BASE[1711] == 1727   # Nawawi explains Muslim


def test_by_number_links_to_hadith():
    passages = list(iter_sharh(1673, "فتح الباري", NUMBER_BOOK["pages"], NUMBER_BOOK["indexes"]))
    assert [p.hadith_number for p in passages] == [1, 2]
    first = passages[0]
    assert first.base_id == 1284 and first.base_name == "صحيح البخاري"
    assert first.page == 495                       # printed page of the anchor
    assert "تتمة شرح الحديث الأول" in first.text    # page span concatenated
    assert "الثاني" not in first.text              # stops before the next hadith


def test_by_chapter_splits_on_headings():
    passages = list(iter_sharh(1711, "شرح النووي", CHAPTER_BOOK["pages"], CHAPTER_BOOK["indexes"]))
    assert [p.chapter for p in passages] == ["باب الإيمان", "باب الصلاة"]
    assert all(p.hadith_number is None for p in passages)
    first = passages[0]
    assert first.base_name == "صحيح مسلم"
    assert "تتمة شرح الإيمان" in first.text
    assert first.page == 10
