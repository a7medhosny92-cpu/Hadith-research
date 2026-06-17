"""Structural عِلّة / شذوذ signals from the gathered طرق (ROADMAP #7).

Beyond the STATED defects (``rulings.extract_illal`` — «أعلّه فلان، الصواب وقفه…»), this DETECTS
candidate defects by comparing the parallel narrations التخريج already gathered for a report:

* **غرابة / تفرّد** — it comes back to a single Companion, or has no متابع at all in the corpus.
* **شذوذ في المتن** — a lone wording (one route, «بمعناه») against a well-attested one (the many).
* **اضطراب** — heavy wording-disagreement from ONE مخرج with no راجح lafẓ.
* **اختلاف الرفع والوقف** — the routes split on reaching the Prophet ﷺ (a classic علّة).

Every signal is a **HINT to investigate** («يُحتمل / يُنظر»), NEVER a verdict — favouring few correct
flags over many noisy ones (the روادك «التخريج» already gives the routes; we only read their shape).
Consumes the dict :func:`app.qa.takhrij.analyze_narrations` returns.
"""

from __future__ import annotations

from app.qa.isnad import analyze_isnad


def _reaches_prophet(narration: dict) -> bool:
    """Is this route مرفوع (reaches the Prophet ﷺ) — vs موقوف/مقطوع (stops at a Companion/تابعي)?
    Read structurally from the chain+matn, no rijal needed."""
    text = f"{narration.get('isnad', '') or ''} {narration.get('matn', '') or ''}".strip()
    return bool(text) and analyze_isnad(text).reaches_prophet


def detect_structural_illal(takhrij: dict, *, check_raf_waqf: bool = True) -> list[dict]:
    """Return a list of structural عِلّة/شذوذ HINTS — ``{type, severity, note}`` — read from the shape
    of the gathered طرق. ``severity`` ∈ ``info`` (a note) / ``warn`` (a likely defect to weigh).
    ``check_raf_waqf=False`` skips the per-route مرفوع/موقوف pass (which parses each chain)."""
    groups = takhrij.get("groups", []) or []
    total = takhrij.get("total", 0)
    companions = takhrij.get("companions", 0)
    named = [g for g in groups if g.get("companion")]
    hints: list[dict] = []

    # 1) غرابة / تفرّد — how many independent مخارج carry it.
    if total == 0:
        hints.append({"type": "تفرّد", "severity": "info",
                      "note": "لم نقف له على متابعٍ في القاعدة — غريبٌ بهذا اللفظ (وقد تكون له طرقٌ خارجها)."})
    elif companions == 1 and named:
        hints.append({"type": "تفرّد", "severity": "info",
                      "note": f"تفرّد به الصحابيُّ {named[0]['companion']} — لم يروه عنه ﷺ في القاعدة "
                              f"صحابيٌّ غيره؛ يُنظر في تفرّده."})

    # 2) شذوذ في المتن — a lone wording (one route, «بمعناه») against a well-attested one (≥3) from the
    #    SAME Companion: the odd wording may be a راوٍ's error (مخالفة الأوثق/الأكثر).
    for g in named:
        variants = g.get("variants", []) or []
        if len(variants) < 2:
            continue
        dominant = max((v.get("count", 0) for v in variants), default=0)
        if dominant >= 3 and any(v.get("count") == 1 and v.get("label") == "بمعناه" for v in variants):
            hints.append({"type": "شذوذ", "severity": "warn",
                          "note": f"لفظٌ تفرّد به راوٍ عن {g['companion']} يخالف روايةَ الأكثر "
                                  f"({dominant} طرق متقاربة) — يُنظر في شذوذه."})

    # 3) اضطراب — ≥3 wordings from one مخرج, none close to the source (all «بمعناه»): no راجح lafẓ.
    for g in named:
        variants = g.get("variants", []) or []
        if len(variants) >= 3 and all(v.get("label") == "بمعناه" for v in variants):
            hints.append({"type": "اضطراب", "severity": "info",
                          "note": f"اختلافٌ كثيرٌ في اللفظ عن {g['companion']} ({len(variants)} صيغ) "
                                  f"دون لفظٍ راجح — يُحتمل الاضطراب."})

    # 4) اختلاف الرفع والوقف — do the routes disagree on reaching the Prophet ﷺ? (conservative: a real
    #    split, ≥2 on the minority side, so a single mis-parse doesn't flag.)
    if check_raf_waqf:
        routes = [n for g in groups for v in (g.get("variants", []) or []) for n in (v.get("narrations", []) or [])]
        if len(routes) >= 4:
            marfu = sum(1 for n in routes if _reaches_prophet(n))
            mawquf = len(routes) - marfu
            if min(marfu, mawquf) >= 2:
                hints.append({"type": "رفع ووقف", "severity": "warn",
                              "note": f"اختلفت الطرق في الرفع والوقف ({marfu} مرفوعة · {mawquf} موقوفة/مقطوعة) "
                                      f"— علّةٌ محتملة يُرجَّح بينها."})
    return hints
