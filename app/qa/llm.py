"""Optional LLM synthesis for /ask — grounded, provider-agnostic via litellm.

Disabled by default. When ``settings.llm_enabled`` is set, /ask hands the retrieved
hadith and شرح to the configured model (local Ollama or any cloud engine) to write a
prose Arabic answer. The prompt is strict: use only the supplied sources, cite the
collection and number, and say "لا أعلم" when they do not answer — so the output
stays verifiable against what was actually retrieved. The sources are returned
alongside the answer regardless.
"""

from __future__ import annotations

from app.qa.answer import Synthesizer

SYSTEM_PROMPT = (
    "أنت مساعد بحثي متخصص في الحديث النبوي. أجب اعتمادًا على المصادر المعطاة فقط، "
    "ولا تستشهد بشيء خارجها. اذكر العزو (اسم الكتاب ورقم الحديث) لكل ما تنقله، "
    "وانقل حكم الحديث كما ورد. وإن كانت المصادر لا تجيب عن السؤال فقل: لا أعلم."
)


def _sources_block(hadith: list[dict], sharh: list[dict]) -> str:
    lines: list[str] = ["# الأحاديث"]
    for h in hadith:
        cite = f"{h.get('collection')} رقم {h.get('number')}"
        grade = f" [الحكم: {h['grade']}]" if h.get("grade") else ""
        lines.append(f"- ({cite}){grade}: {h.get('matn')}")
    if sharh:
        lines.append("\n# الشروح")
        for s in sharh:
            ref = s.get("sharh")
            if s.get("hadith_number"):
                ref += f" (عند الحديث {s['hadith_number']})"
            lines.append(f"- ({ref}): {s.get('excerpt')}")
    return "\n".join(lines)


def build_prompt(question: str, hadith: list[dict], sharh: list[dict]) -> str:
    """The user message: the retrieved sources followed by the question."""
    return f"{_sources_block(hadith, sharh)}\n\n# السؤال\n{question}\n\n# الجواب\n"


def litellm_synthesizer(settings) -> Synthesizer:
    """A Synthesizer that calls the configured model via litellm (lazy import)."""

    def synthesize(question: str, hadith: list[dict], sharh: list[dict]) -> str:
        import litellm  # lazy: optional 'llm' extra

        response = litellm.completion(
            model=settings.llm_model,
            api_base=settings.ollama_api_base or None,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": build_prompt(question, hadith, sharh)},
            ],
            temperature=settings.llm_temperature,
        )
        return response["choices"][0]["message"]["content"].strip()

    return synthesize
