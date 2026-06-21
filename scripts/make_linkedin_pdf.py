"""Assemble the 7 square tech cards (+ an Arabic cover slide) into one LinkedIn document
carousel — data/social/linkedin_carousel.pdf. Pure Arabic (no Latin/tofu); the GitHub link
lives in the post caption, not the image. Run: python -m scripts.make_linkedin_pdf
"""
from __future__ import annotations

from PIL import Image, ImageDraw

from scripts.make_social import GOLD, CREAM2, NASKH_B, NASKH_R, KUFI_B, F, center, star8, tlen

W = H = 1200
DGREEN = (15, 71, 48)
LGOLD = (226, 200, 140)
LIGHT = (240, 233, 216)


def cover():
    img = Image.new("RGB", (W, H), DGREEN)
    d = ImageDraw.Draw(img)
    for yy in range(30, H, 26):
        for xx in range(30, W, 26):
            d.ellipse((xx, yy, xx + 1, yy + 1), fill=(21, 84, 58))
    d.rectangle((42, 42, W - 42, H - 42), outline=GOLD, width=3)
    d.rectangle((54, 54, W - 54, H - 54), outline=(150, 120, 55), width=1)
    # emblem
    star8(d, W // 2, 296, 64, GOLD)
    star8(d, W // 2, 296, 34, DGREEN)
    star8(d, W // 2, 296, 16, GOLD)
    center(d, W // 2, 432, "بحثٌ وتحقيقُ", F(KUFI_B, 84), CREAM2)
    center(d, W // 2, 540, "الحديثِ النبويِّ", F(KUFI_B, 84), CREAM2)
    # ornament rule
    cy = 690
    star8(d, W // 2, cy, 12, GOLD)
    d.line((W // 2 - 250, cy, W // 2 - 30, cy), fill=GOLD, width=2)
    d.line((W // 2 + 30, cy, W // 2 + 250, cy), fill=GOLD, width=2)
    center(d, W // 2, 742, "نظامٌ عربيٌّ ذكيٌّ، مفتوحُ المصدرِ، يعملُ دونَ إنترنت:", F(NASKH_R, 40), LIGHT)
    center(d, W // 2, 812, "للبحثِ في السنّةِ، وتحقيقِ الأسانيدِ، ومعرفةِ الرواةِ، وكشفِ العللِ.", F(NASKH_R, 40), LIGHT)
    # swipe hint + a drawn gold chevron (no arrow glyph → no tofu)
    hint = "اسحبْ لتعرفَ كيف يعملُ"
    fh = F(NASKH_B, 44)
    center(d, W // 2, 952, hint, fh, GOLD)
    cx = W // 2 - tlen(d, hint, fh) // 2 - 40
    d.line((cx, 968, cx - 22, 980), fill=GOLD, width=5)
    d.line((cx, 992, cx - 22, 980), fill=GOLD, width=5)
    center(d, W // 2, 1086, "بالعربيةِ الفصحى · على جهازِك وحدَه", F(NASKH_R, 32), LGOLD)
    return img


def main():
    from fpdf import FPDF

    cover().save("data/social/sq_00_cover.png", "PNG")
    paths = ["data/social/sq_00_cover.png"] + [
        f"data/social/sq_{n}.png" for n in
        ("11_stack", "12_pipeline", "13_tamyiz", "14_rijal", "15_audit", "16_illal", "17_todo")]
    pdf = FPDF(unit="pt", format=(W, H))
    pdf.set_auto_page_break(False)
    for p in paths:
        pdf.add_page()
        pdf.image(p, x=0, y=0, w=W, h=H)
    out = "data/social/linkedin_carousel.pdf"
    pdf.output(out)
    print(f"wrote {out}  ({len(paths)} pages)")


if __name__ == "__main__":
    main()
