# تهذيب الكمال (al-Mizzī) — book study & extractor spec

Empirical study of book **3722 (8,258 entries)** to design a prose رجال extractor (ROADMAP #8).
Goal: full names + **شيوخ/تلاميذ network** + **multi-critic verdicts** → resolve the audit's «مشترك»
(A) homonyms and correct the متروك/كذاب (W) mis-grades.

## Coverage (of 8,258 entries)
- **94%** carry رموز (the Six-Books symbols) · **91%** have «روى عن» (شيوخ) · **89%** «روى عنه» (تلاميذ)
- ~22% an explicit death year (مات/توفي سنة) · ~670 Companions (له صحبة / صحابي)

## Entry format
```
NNNN - رموز :  full name + nasab + nisba + kunya
رَوَى عَن :   شيخ (رموز)، شيخ (رموز)، …
رَوَى عَنه :  تلميذ (رموز)، …
   قال [transmitter] عن [critic]: [verdict]   e.g. «قال أبو طالب عن أحمد: لا بأس به»
   وقال [critic]: [verdict]                     «قال ابن معين: صدوق»، «قال النسائي: ضعيف … ليس بثقة»
مات/توفي سنة [year]
روى له [الكتب الستة] / وروى له الباقون سوى …
```

## رموز vocabulary (book symbols)
خ=Bukhārī · م=Muslim · د=Abū Dāwūd · ت=Tirmidhī · س=Nasāʾī · ق=Ibn Mājah · **ع=all six (الجماعة)** ·
٤=the four Sunan · بخ=Bukhārī (Adab al-mufrad) · خت=Bukhārī taʿlīqan · سي=Nasāʾī (ʿamal al-yawm) ·
مد/قد=Abū Dāwūd (marāsīl/qadar) · عخ · عس · فق · كن · لت · تم · ص · كد · **تمييز** = a man listed only
to disambiguate (NOT one of the Six Books' narrators).
→ **A man with خ or م cannot be متروك/كذاب** — the rumūz alone correct several W-category errors.

## The hard part — editor footnotes — and the clean fix
Footnotes are pervasive: **17,786** «____» blocks and **125,781** «(N)» inline refs (>15 per entry).
They discuss OTHER men, so an unstripped «متروك» in a footnote would poison a ثقة man's grade. BUT
each raw page is laid out «main text  ____  footnotes»: **cut every page at the first «____» run** to
drop the footnotes reliably, then strip inline «(N)» refs. (Validated against the raw page structure.)

## Two block-opener forms (the key gotcha)
Major narrators get the full **«رَوَى عَن:» / «رَوَى عَنه:»**; minor ones get the abbreviated
**«عَن:» / «وعَنه:»**. Both must be recognised, and the **colon is required** — the bare chain word
«عَنْ فلانٍ» (no colon) is NOT a block opener. The whole book is heavily vocalised («رَوَى عَن»), so
every marker regex is diacritic-tolerant (`flexible_word`); grade words are matched diacritic-folded.

## The other gotcha — no `numbers` index, and a ~200-page muqaddima
Book 3722 has **no `indexes.numbers`** (`_first_entry_page` → None), so the whole text — including the
محقق's ~200-page introduction (al-Mizzī's life, his method, a numbered bibliography, praise quotes) —
is scanned. That intro's numbered points reset in short runs and carry no rumūz, while the dictionary
proper is a **dense run of rumūz-bearing entries**: `_muqaddima_skip` jumps to the first window that is
mostly rumūz entries. (Heading pages can't anchor it: the 35 volumes **reset printed-page numbering**,
so `page` is ambiguous without `vol` — see below.)

## ⚠️ Per-volume page numbering (app-wide note)
Many turath books are multi-volume and **restart `page` at 1 each volume**, so a citation needs **`vol`
+ `page`**, never `page` alone (e.g. al-Mustadrak #7514 is ج٨ ص٢٣٠, and printed «204» occurs 35×). The
parsed records already carry `volume`; the app must SHOW it in every citation.

## Extractor spec (as built — `app/parsing/tahdhib_extract.py`)
1. **Footnotes:** per page keep only text *before* the first «____»; strip inline «(N)» refs.
2. **Muqaddima:** skip the intro via the dense-rumūz-run heuristic.
3. **Head:** number + رموز (books) + name (cut at a block opener or a bio word) + kunya.
4. **Network:** شيوخ from «(رَوَى) عَن:», تلاميذ from «(و)(رَوَى) عَنه:» up to «قال/مات/…»; split on «،»,
   strip the trailing «(رموز)» of each name.
5. **Verdicts:** «قال [critic]: [grade]» keeping appraisals that carry a grade word (diacritic-folded).
6. **Death:** «مات/توفي سنة [year]» (al-Mizzī spells years out in words).

## Results (on the real 3722)
~6,870 tarājim; **books 92% · شيوخ 94% · تلاميذ 93% · verdicts 57%**. Verified: عثمان بن أبي شيبة
(3857 · خ م ق — شيوخ 63/تلاميذ 33 incl. البخاري، مسلم، أبو داود), يونس بن محمد (7184 · ع), سفيان الثوري
(2407 · ع · شيوخ 273). The رموز confirm the audit's W-errors are wrong: men in خ/م **cannot** be
متروك/كذاب. Unit tests in `tests/test_tahdhib_extract.py` (pure parser; the book is gitignored).
**Weak spots:** ~14% of names still absorb bio; `death_year` only ~19% (`_death_year` misses
fully-vocalised spelled-out years); verdict phrasing is noisy. تلاميذ truncates on the longest entries.

## Methodology — how this extractor was built, and why
Recorded so the reasoning survives a context reset (and for anyone extending it):

1. **Study first, parse second.** The plan the user chose was «studiati tutto il libro» before writing
   code. We pulled real tarājim with `scripts/sample_source.py 3722 --rijal-sample` (20 curated
   narrators) and read them, so the parser was designed against the *actual* layout — not a guess.
   *Why:* misattribution is the whole risk of this project; a parser built on assumptions silently
   corrupts the rijal network.
2. **Drop footnotes by structure, not by content.** Each raw page is «main text ____ footnotes», and
   the footnotes name OTHER men (17,786 «____» blocks, 125,781 «(N)» refs). We cut every page at its
   first «____» and strip «(N)». *Why:* an unstripped «متروك» in a footnote would poison a ثقة man —
   the exact error class تهذيب is meant to FIX, so we could not risk re-introducing it.
3. **Make every marker diacritic-tolerant — discovered, not assumed.** The first real run extracted 0
   شيوخ and 21%-long names. Tracing a long-name entry showed the cause: the source prints «رَوَى عَن»
   fully vocalised, so the plain `روى عن` regex never matched and the name absorbed the whole bio. Fix:
   build markers with `flexible_word` and fold diacritics before matching grade words.
4. **Find the abbreviated «عَن:» form — by following the failures.** Even after (3), ~600 entries past
   #500 had no شيوخ. Sampling them (`#657, #666, #688…`) revealed minor narrators use «عَن:» / «وعَنه:»,
   not «رَوَى عَن:». Adding those (colon-anchored, to exclude the chain word «عَنْ») took شيوخ 81% → 94%.
5. **Skip the muqaddima by content, after two dead ends.** Page anchors failed (35 volumes reset the
   printed page — the al-Mustadrak lesson again). A «long sequential 1→N run» heuristic also failed: the
   intro contains a *numbered bibliography* that is itself a long run, so the skip landed on
   «كتاب القراءة خلف الإمام». What is unambiguous is **content**: only real tarājim carry rumūz, so we
   skip to the first window that is mostly rumūz-bearing entries.
6. **Validate on known men + aggregate coverage.** Spot-checks on عثمان بن أبي شيبة / يونس بن محمد /
   الثوري (right rumūz, right شيوخ/تلاميذ) plus corpus-wide coverage %s caught each regression (e.g. an
   over-eager name cut, or `_story_start`-style over-reach) before it was accepted.

## Next
Wire it in: (a) integrate the شيوخ/تلاميذ network into `build_graph` so a narrator is identified from
his chain neighbours → resolves the «مشترك» (A) homonyms at verdict time; (b) feed full names + multi-
critic verdicts as a rich rijal source. NOT yet imported by the pipeline (parse skips RIJAL_PROSE_BOOKS).
