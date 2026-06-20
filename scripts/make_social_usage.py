"""Usage-example + library cards for the support carousel (real case: صحيح البخاري #1،
«إنما الأعمال بالنيات» — its chain, grades, takhrij are textbook-accurate). Reuses the
shaping/layout helpers of scripts.make_social. Run: python -m scripts.make_social_usage
"""
from __future__ import annotations

from scripts.make_social import (
    W, H, BG, CARD, INK, GREEN, GREEN2, GOLD, GOLD2, MUTED, LINE, CREAM2,
    NASKH_B, NASKH_R, KUFI_B, KUFI_R, F, _s, center, right, wrap, tlen,
    base, footer, kicker, heading, star8, ornament, save,
)

SOFT = (246, 242, 233)
OLIVE = (122, 132, 60)
RED = (176, 58, 46)


def panel(d, top, bot, pad=72):
    d.rounded_rectangle((pad, top, W - pad, bot), radius=26, fill=CARD, outline=LINE, width=2)


def tabbar(d, y, active, tabs):
    f = F(NASKH_B, 27)
    x = W - 104
    for t in tabs:
        w = tlen(d, t, f)
        pad = 15
        x0 = int(x - w - 2 * pad)
        on = t == active
        d.rounded_rectangle((x0, y, int(x), y + 44), radius=22,
                            fill=GREEN if on else CREAM2, outline=GREEN if on else LINE, width=2)
        center(d, (x0 + int(x)) // 2, y + 5, t, f, CREAM2 if on else MUTED)
        x = x0 - 13
    d.line((104, y + 64, W - 104, y + 64), fill=LINE, width=2)


def chip(d, xr, ycen, text, bg, fg, size=27):
    f = F(NASKH_B, size)
    w = tlen(d, text, f)
    pad = 16
    h = size + 18
    x0 = int(xr - w - 2 * pad)
    d.rounded_rectangle((x0, int(ycen - h / 2), int(xr), int(ycen + h / 2)), radius=h // 2, fill=bg)
    center(d, (x0 + int(xr)) // 2, int(ycen - h / 2) + 2, text, f, fg)
    return x0


def label(d, y, text):
    """A small gold section label, right-aligned with a short rule under it."""
    right(d, W - 110, y, text, F(NASKH_B, 34), GOLD2)
    return y + 56


# ───────────────────────── 6) search ─────────────────────────
def card_search():
    img, d = base()
    kicker(d, 104, "مثالٌ عمليّ: البحثُ في السنّة")
    heading(d, 196, "ابحثْ بالمعنى لا باللفظِ", 54)
    panel(d, 312, 1196)
    tabbar(d, 348, "بحث", ["تخريج", "راوٍ", "الإسناد", "بحث"])
    # the query bar
    d.rounded_rectangle((118, 452, W - 118, 528), radius=20, fill=SOFT, outline=LINE, width=2)
    star8(d, 168, 490, 13, GREEN)
    right(d, W - 150, 466, "إنّما الأعمالُ بالنيّاتِ", F(NASKH_B, 40), INK)
    # result 1
    d.rounded_rectangle((118, 566, W - 118, 832), radius=20, fill=CREAM2, outline=LINE, width=2)
    chip(d, W - 150, 612, "صحيح · متّفقٌ عليه", GREEN, CREAM2)
    yy = paragraph_box(d, 648, "إنّما الأعمالُ بالنيّاتِ، وإنّما لكلِّ امرئٍ ما نوى، فمن كانت "
                               "هجرتُه إلى اللهِ ورسولِه فهجرتُه إلى اللهِ ورسولِه.",
                       F(NASKH_R, 36), INK)
    star8(d, W - 150, 790, 7, GOLD)
    right(d, W - 172, 770, "صحيح البخاري · بدءُ الوحي · رقم ١", F(NASKH_B, 32), GREEN2)
    # result 2
    d.rounded_rectangle((118, 862, W - 118, 1150), radius=20, fill=CREAM2, outline=LINE, width=2)
    chip(d, W - 150, 908, "صحيح", GREEN, CREAM2)
    paragraph_box(d, 944, "عن عائشةَ رضي اللهُ عنها أنّ النبيَّ ﷺ قال: مَن عمِلَ عملًا ليسَ "
                          "عليه أمرُنا فهو ردٌّ.", F(NASKH_R, 36), INK)
    star8(d, W - 150, 1108, 7, GOLD)
    right(d, W - 172, 1088, "صحيح مسلم · الأقضية · رقم ١٧١٨", F(NASKH_B, 32), GREEN2)
    footer(d)
    return save(img, "6_search")


def paragraph_box(d, y, text, fnt, fill, maxw=W - 320, lh=50):
    for ln in wrap(d, text, fnt, maxw):
        right(d, W - 150, y, ln, fnt, fill)
        y += lh
    return y


# ───────────────────────── 7) isnad verification ─────────────────────────
def card_isnad():
    img, d = base()
    kicker(d, 104, "مثالٌ عمليّ: تحقيقُ الإسناد")
    heading(d, 196, "السندُ راويًا راويًا، ثمّ الحكم", 50)
    panel(d, 312, 1196)
    tabbar(d, 348, "الإسناد", ["تخريج", "راوٍ", "بحث", "الإسناد"])
    chain = [
        ("الحُمَيْديُّ عبدُ اللهِ بنُ الزُّبيرِ", "ثقة حافظ", GREEN),
        ("سفيانُ بنُ عُيَينةَ", "ثقة حافظ إمام", GREEN),
        ("يحيى بنُ سعيدٍ الأنصاريُّ", "ثقة ثبت", GREEN),
        ("محمدُ بنُ إبراهيمَ التيميُّ", "ثقة", GREEN),
        ("علقمةُ بنُ وقّاصٍ الليثيُّ", "ثقة", GREEN),
        ("عمرُ بنُ الخطّابِ", "صحابيّ", GOLD2),
        ("رسولُ اللهِ ﷺ", "", None),
    ]
    y = 442
    step = 84
    nx = W - 130                      # the node dots column (right)
    d.line((nx, y, nx, y + step * (len(chain) - 1)), fill=LINE, width=3)
    for name, grade, col in chain:
        prophet = col is None
        d.ellipse((nx - 11, y - 11, nx + 11, y + 11), fill=GOLD if prophet else GREEN, outline=CARD, width=3)
        right(d, nx - 34, y - 26, name, F(NASKH_B, 38 if prophet else 36), GREEN2 if prophet else INK)
        if grade:
            gw = tlen(d, grade, F(NASKH_B, 27))
            chip(d, 150 + gw + 32, y - 1, grade, CREAM2, GREEN2)
            d.rounded_rectangle((150, y - 23, 150 + gw + 32, y + 23), radius=23, outline=col, width=2)
        y += step
    # verdict banner (no «:» — Kufi lacks the colon glyph; both lines centred with a clear gap)
    d.rounded_rectangle((118, 1000, W - 118, 1168), radius=22, fill=GREEN, outline=GOLD, width=3)
    center(d, W // 2, 1026, "الحكمُ صحيحٌ", F(KUFI_B, 42), CREAM2)
    center(d, W // 2, 1102, "رجالُه كلُّهم ثقاتٌ، والسندُ متّصلٌ", F(NASKH_R, 30), (236, 246, 239))
    footer(d)
    return save(img, "7_isnad")


# ───────────────────────── 8) narrator card ─────────────────────────
def card_narrator():
    img, d = base()
    kicker(d, 104, "مثالٌ عمليّ: بطاقةُ راوٍ")
    heading(d, 196, "كلُّ ما يلزمُ عن الراوي", 52)
    panel(d, 312, 1196)
    tabbar(d, 348, "راوٍ", ["تخريج", "الإسناد", "بحث", "راوٍ"])
    right(d, W - 130, 444, "سفيانُ بنُ عُيَينةَ الهلاليُّ", F(KUFI_B, 48), GREEN2)
    chip(d, W - 130, 564, "ثقة حافظ فقيه إمام", GREEN, CREAM2, size=29)
    right(d, 130 + 252, 552, "ت ١٩٨ هـ · الطبقةُ الثامنة", F(NASKH_B, 29), MUTED)
    y = 628
    right(d, W - 110, y, "شيوخُه", F(NASKH_B, 32), GOLD2)
    y = paragraph_box(d, y + 52, "عمرو بنُ دينارٍ · الزُّهريُّ · أبو الزِّنادِ · يحيى بنُ سعيدٍ الأنصاريُّ · "
                                 "أيّوبُ السَّختيانيُّ", F(NASKH_R, 32), INK, lh=46) + 12
    right(d, W - 110, y, "تلاميذُه", F(NASKH_B, 32), GOLD2)
    y = paragraph_box(d, y + 52, "الشافعيُّ · أحمدُ بنُ حنبلٍ · الحُمَيْديُّ · عليُّ بنُ المدينيِّ · "
                                 "إسحاقُ بنُ راهَوَيْهِ", F(NASKH_R, 32), INK, lh=46) + 12
    right(d, W - 110, y, "أقوالُ الأئمّة", F(NASKH_B, 32), GOLD2)
    y += 52
    for q, who in [("«ما رأيتُ أحدًا أعلمَ بكتابِ اللهِ منه»", "ابنُ المباركِ · تهذيب الكمال"),
                   ("«لولا مالكٌ وسفيانُ لذهبَ علمُ الحجازِ»", "الشافعيُّ · سير أعلام النبلاء")]:
        right(d, W - 150, y, q, F(NASKH_B, 32), INK)
        y += 46
        right(d, W - 170, y, who, F(NASKH_R, 27), GOLD2)
        y += 52
    footer(d)
    return save(img, "8_narrator")


# ───────────────────────── 9) takhrij + illal ─────────────────────────
def card_takhrij():
    img, d = base()
    kicker(d, 104, "مثالٌ عمليّ: التخريجُ وكشفُ العلل")
    heading(d, 196, "اجمعِ الطرقَ، وانظرْ في العلّة", 48)
    panel(d, 312, 1196)
    tabbar(d, 348, "تخريج", ["راوٍ", "الإسناد", "بحث", "تخريج"])
    right(d, W - 150, 456, "«إنّما الأعمالُ بالنيّاتِ»", F(NASKH_B, 44), GREEN2)
    y = 552
    for v, lbl in [("٧", "من كتبِ السنّةِ خرّجَتْه"), ("١", "صحابيٌّ تفرّدَ به"),
                   ("صحيح", "حكمُ الإسنادِ")]:
        right(d, W - 150, y, lbl, F(NASKH_B, 36), INK)
        chip(d, 280, y + 22, v, CREAM2, GREEN2, size=32)
        d.rounded_rectangle((118, y - 8, 280, y + 52), radius=22, outline=GOLD, width=2)
        y += 96
    # illal box
    d.rounded_rectangle((118, y + 6, W - 118, y + 232), radius=22, fill=(250, 244, 230), outline=GOLD, width=2)
    star8(d, W - 156, y + 52, 11, GOLD2)
    right(d, W - 184, y + 30, "إشارةُ تفرّدٍ وغرابة", F(NASKH_B, 38), GOLD2)
    paragraph_box(d, y + 96, "لم يروِه عن النبيِّ ﷺ إلّا عمرُ بنُ الخطّابِ، ثمّ تفرّد به عنه علقمةُ، "
                             "فمحمدُ بنُ إبراهيمَ، فيحيى بنُ سعيدٍ — غريبٌ في أوّلِه مشهورٌ في آخرِه.",
                  F(NASKH_R, 33), INK, maxw=W - 330, lh=50)
    center(d, W // 2, y + 250, "قرينةٌ للنظرِ، لا حُكمٌ نهائيّ", F(NASKH_R, 28), MUTED)
    footer(d)
    return save(img, "9_takhrij")


# ───────────────────────── 10) the books ─────────────────────────
def card_books():
    img, d = base()
    kicker(d, 104, "المصادرُ والكتب")
    heading(d, 196, "أمّهاتُ كتبِ السنّةِ والرجالِ", 50)
    center(d, W // 2, 286, "يقرأُ من المطبوعِ المحقَّقِ، ويوثّقُ كلَّ نقلٍ بكتابِه", F(NASKH_R, 32), MUTED)
    colR_x = W - 130
    colL_x = W // 2 - 60
    y0 = 386

    def col(x, title, items):
        right(d, x, y0, title, F(KUFI_B, 36), GREEN2)
        d.line((x - 300, y0 + 56, x, y0 + 56), fill=GOLD, width=2)
        yy = y0 + 84
        for it in items:
            star8(d, x, yy + 17, 7, GOLD)
            right(d, x - 28, yy, it, F(NASKH_R, 32), INK)
            yy += 52
        return yy

    col(colR_x, "كتبُ السنّةِ", [
        "صحيح البخاري", "صحيح مسلم", "سنن أبي داود", "جامع الترمذي",
        "سنن النسائي", "سنن ابن ماجه", "موطّأ مالك", "مسند أحمد",
        "صحيح ابن خزيمة", "صحيح ابن حبّان", "المستدرك للحاكم", "سنن الدارقطني",
    ])
    col(colL_x, "كتبُ الرجالِ", [
        "تقريب التهذيب", "الكاشف للذهبي", "تهذيب الكمال", "الجرح والتعديل",
        "الإصابة في الصحابة", "الثقات", "لسان الميزان", "ميزان الاعتدال",
        "سير أعلام النبلاء", "تاريخ الإسلام", "أسد الغابة", "الطبقات الكبرى",
    ])
    center(d, W // 2, 1116, "ومعها كبارُ الشروحِ: فتحُ الباري وشرحُ النوويِّ وتحفةُ الأحوذيِّ",
           F(NASKH_R, 29), GOLD2)
    footer(d)
    return save(img, "10_books")


def main():
    out = [card_search(), card_isnad(), card_narrator(), card_takhrij(), card_books()]
    print("done:", len(out), "cards")


if __name__ == "__main__":
    main()
