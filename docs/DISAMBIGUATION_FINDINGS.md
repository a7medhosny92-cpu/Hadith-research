# Narrator disambiguation — measurement findings (remote, Ṣaḥīḥayn subset)

A durable record of a remote measurement session: building the pipeline on a Bukhārī+Muslim
subset and quantifying how far the «held» (مشترك) narrators can be resolved **with certainty**,
and what blocks it. Numbers are **indicative** (subset, not the full corpus) and were produced on
an ephemeral container; the **code** is the source of truth, this file is the **reasoning record**.

> TL;DR — The classical triangle (**name + company + ṭabaqa**) is the right model and is what we
> built. But the dominant error is **not** the honestly-held ambiguous cases — it is a class of
> **silent confident MIS-identifications** made by `canon._pick`'s *diffuse token-overlap* (e.g.
> «يونس عن الزهري» → confidently `يونس بن عبيد`, wrong, `ambiguous=False`, unflagged; **more context
> makes it worse**). The fix is to disambiguate by the **specific neighbour's documented roster**
> (شيخ→students / تلميذ→teachers) as a **hard constraint with hold-by-default** — which is both the
> certainty discipline and the «company» method.

## Setup (what was run remotely)
- Books (uploaded): **1284** Bukhārī, **1727** Muslim (chains); **8609** تقريب + **2171** الكاشف
  (grades); **3722** تهذيب الكمال (network). No شروح, no semantic (irrelevant to A).
- Pipeline: parse → index → build_rijal → build_graph → build_rijal → audit (convergent order to
  avoid the one-iteration graph/rijal lag).
- Sizes: **13,565** hadith parsed (**13,538** with isnād); rijal **9,634** entries (+92 seed);
  graph **6,482** nodes / **17,458** links; muhmal subset map **1,403** contexts.
- Caveat: subset ≈ 15% of the user's full corpus; chains are عالية (short) → compressed depth scale.

## Audit baseline (subset, dedup #109 + muhmal #110 active)
**P 0 · W 24 · S 738 · A 6241.**

### The A-count is a misleading metric
A fires on **any** ambiguous match, even when the tied candidates **agree on the grade**. Decomposing
the 6241:
- **1160** are `grade_agreed` — the man is identified and gradable, just multi-matched (often an
  un-collapsed same-man duplicate). **Not real problems.**
- **5081** are genuinely **held** (يُتوقَّف — candidates disagree on grade). **This is the real target.**

2×2 on A (dedup × muhmal): baseline (both off) 5883 → (both on) 6241. **Neither lever lowers A.**
muhmal *raises* A (+~350) by surfacing identified-but-still-ambiguous narrators as honest holds
(consistent with «A rose as confidently-wrong became honest held»); dedup is ≈0 on the subset
(its value is high-frequency duplicates on the **full** corpus).

## How far the signals resolve the 5081 «held» (each measured)
| signal | coverage | death-year-free? | resolved (held) |
|---|---|---|---|
| **death-year** (generational window) | 52% have distinct deaths | ✗ | ~917 *(noisy; some spurious)* |
| **ṭabaqa from chain depth** (the corpus-internal idea) | 1057 narrators get a ṭabaqa | ✓ | 206–406 *(48–131 new beyond death-year)* |
| **explicit طبقة in تقريب** (Ibn Ḥajar's 12 layers) | **88.4%** (7806/8827) | ✓ | the coverage unlock |
| **company** (شيوخ+تلاميذ rosters, both sides) | — | ✓ | **1580** |
| **company + ṭabaqa (union)** | — | ✓ | **2698 = 53%** of held; **1216** without any death-year |

The classical rule is literally **«يُميَّز المهمل بشيخه وتلميذه وطبقته»** — distinguish by teacher,
student, generation. The three signals = that triangle.

## The certainty findings (the important, humbling part)
1. **Heuristic «picks» disagree.** Where company *and* ṭabaqa both fire (709 cases), they pick the
   **same man only 72 times (~10%)**. Soft «closest/highest» scoring is a **noisy guess**, not
   certainty. The «53% resolved» was each signal guessing independently; they do **not** concur.
2. **Documentary resolution is clean but tiny here.** Using تهذيب's روى عن/عنه as the sole judge
   (a candidate is confirmed iff تهذيب lists the actual شيخ among his teachers / تلميذ among his
   students): of 5081 held, only **460** have any candidate with a تهذيب roster, and only **52** are
   uniquely confirmed. On the full corpus + complete تهذيب this grows, but on the subset it is small.
3. **THE KEY BUG — silent confident mis-identification (`canon._pick`).** For «… عن يونس عن الزهري …»:
   - the right man **يونس بن يزيد الأيلي IS among the 26 candidates** (not a candidate-generation bug);
   - `canon.canonical("يونس", clean-context)` → keeps **«يونس»** (held — correct);
   - but with the **full noisy chain context**, `_pick` finds a **spurious unique winner**:
     **`يونس بن عبيد`** (a Baṣran who narrates from الحسن, **not** from الزهري), with
     **`ambiguous=False`** → confident and **wrong**, and **unflagged** (يونس بن عبيد is ثقة → no W;
     not ambiguous → no A).
   - **Paradox: more context → worse**, because `_pick` scores by *diffuse token overlap* of company,
     and a wrong candidate's company accidentally overlaps more. These **silent mis-identifications**
     are more dangerous than honest holds, and the whole W/S/A audit misses them.
4. Full-corpus muhmal map (user-uploaded, **11,827** contexts vs the subset's 1,403) swapped in →
   audit A **6241 → 6177 (−64)**: modest, confirming the bottleneck is **not** muhmal coverage but the
   rijal-DB / `_pick` quality downstream. (The full map *does* contain `(…, الزهري) → يونس بن يزيد الأيلي`,
   but the exact `(تلميذ, شيخ)` pair of the failing chain wasn't mapped — the **شيخ-only relaxation**
   would catch it.)

## Conclusion & the fix
- **Certainty must be documentary or by hard elimination, never heuristic scoring.** Assert an
  identity only when a source confirms it (تهذيب روى عن/عنه, the corpus naming him in full = muhmal,
  or al-Ghassānī) **or** when hard constraints leave exactly one possible man; otherwise **hold**.
- **The single highest-leverage change: rewrite `app/rijal/canon.py::_pick`.** Replace diffuse
  token-overlap with **specific-neighbour evidence**: among the candidates, keep those documented to
  narrate **from the actual شيخ** and/or **to the actual تلميذ** (graph edge `link_weight`, and/or
  تهذيب roster). Pick **only** a unique survivor; else keep the surface form (held). This:
  (a) eliminates the silent mis-identifications (يونس no longer becomes يونس بن عبيد);
  (b) enforces certainty-by-elimination; (c) **is** the user's «look at the maestro and his students»
  method, both sides.
- **The real bottleneck is data, not method:** complete the candidate sets and the تهذيب/طبقة
  extraction, and re-measure on the **full corpus** where muhmal-explicit (the most certain signal)
  scales ~9×. Recover **al-Ghassānī's «تقييد المهمل»** (hand-resolved muhmal of the **Ṣaḥīḥayn** — our
  exact subset) as the gold standard to measure **precision**, not coverage.

## The literature (the science behind this)
- Umbrella (where the rule lives): **مقدمة ابن الصلاح**; **فتح المغيث — السخاوي** (most detailed on
  المهمل and distinguishing by شيخ/تلميذ); **تدريب الراوي — السيوطي**; **نزهة النظر — ابن حجر**.
- Same name → different men: **«المتفق والمفترق» — الخطيب البغدادي**.
- Dedicated to the muhmal: **«تقييد المهمل وتمييز المشكل» — أبو علي الغسّاني الجيّاني** (on the Ṣaḥīḥayn);
  **«المكمل في بيان المهمل» — الخطيب**.
- Generations: **الطبقات الكبرى — ابن سعد**; the 12 طبقات in **تقريب التهذيب**.
- Network + grades: **تهذيب الكمال — المزي** (روى عن/عنه); **الجرح والتعديل — ابن أبي حاتم**.
- Modern computational peers (to evaluate, not copy): **Itqan** (open narrator DB + disambiguation
  rules), **AR-Sanad 280K** (narrator-disambiguation dataset), **SPADE on Bukhārī** (narrator-network
  mining).

## Next steps
1. **Rewrite `canon._pick`** to neighbour-specific hard evidence + hold-by-default; re-measure the
   silent-mis-identification rate and the held resolution (precision-first).
2. Re-run on the **full corpus** on the user's machine; report the true W/S/A.
3. Acquire **al-Ghassānī** as the precision gold; complete تهذيب/طبقة extraction.
