"""تمييز المهمل — resolving a bare narrator to his full form from the corpus's own redundancy."""

from __future__ import annotations

from app.rijal.muhmal import build_map, resolve, resolve_chain


def test_resolves_bare_to_the_unique_full_form_in_context():
    chains = [
        ["وكيع", "سفيان الثوري", "الأعمش"],      # full form named in the (وكيع, الأعمش) context
        ["أبو معاوية", "سفيان الثوري", "الأعمش"],  # a different تلميذ → a different context
        ["وكيع", "سفيان", "الأعمش"],              # bare, SAME context as the first
    ]
    m = build_map(chains, min_count=1)
    assert resolve("سفيان", "وكيع", "الأعمش", m) == "سفيان الثوري"
    assert resolve_chain(["وكيع", "سفيان", "الأعمش"], m) == ["وكيع", "سفيان الثوري", "الأعمش"]


def test_rival_full_forms_stay_unresolved():
    # the same (تلميذ, شيخ) names TWO different men fully → genuine homonymy → never fused.
    chains = [
        ["وكيع", "سفيان الثوري", "عمرو"],
        ["وكيع", "سفيان بن عيينة", "عمرو"],
        ["وكيع", "سفيان", "عمرو"],
    ]
    m = build_map(chains, min_count=1)
    assert resolve("سفيان", "وكيع", "عمرو", m) == "سفيان"


def test_noise_forms_are_not_taken_as_the_full():
    # a matn-leak «قتادة يحدث» must not become the resolved name.
    chains = [["شعبة", "قتادة يحدث", "أنس"], ["شعبة", "قتادة", "أنس"]]
    m = build_map(chains, min_count=1)
    assert resolve("قتادة", "شعبة", "أنس", m) == "قتادة"


def test_bare_must_be_a_leading_run_of_the_full():
    chains = [["دلف", "محمد بن جعفر", "ورقاء"], ["دلف", "محمد بن جعفر", "ورقاء"]]
    m = build_map(chains, min_count=1)
    assert resolve("علي", "دلف", "ورقاء", m) == "علي"        # «علي» is not a prefix of «محمد بن جعفر»
    assert resolve("محمد", "دلف", "ورقاء", m) == "محمد بن جعفر"   # «محمد» is
