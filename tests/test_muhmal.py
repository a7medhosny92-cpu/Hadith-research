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


def test_shaykh_only_relaxation_resolves_when_the_exact_pair_is_unseen():
    # «يونس» is named fully under شيخ الزهري via two تلاميذ; a THIRD تلميذ cites him bare. The exact
    # (عنبسة, الزهري) pair never carried the full form — but the شيخ alone (الزهري) decides who he is.
    chains = [
        ["مالك", "يونس بن يزيد الأيلي", "الزهري"],
        ["الليث", "يونس بن يزيد الأيلي", "الزهري"],
        ["عنبسة", "يونس", "الزهري"],                   # bare, a تلميذ never seen with the full form
    ]
    m = build_map(chains, min_count=1)
    assert resolve("يونس", "عنبسة", "الزهري", m) == "يونس بن يزيد الأيلي"


def test_relaxation_holds_on_homonymy_under_one_shaykh():
    # two DIFFERENT men share the bare «يونس» under the same شيخ → the شيخ can't decide → held «مشترك».
    chains = [
        ["معمر", "يونس بن يزيد الأيلي", "الزهري"],
        ["عقيل", "يونس بن عبيد البصري", "الزهري"],
        ["صالح", "يونس", "الزهري"],
    ]
    m = build_map(chains, min_count=1)
    assert resolve("يونس", "صالح", "الزهري", m) == "يونس"


def test_relaxation_skips_a_generic_bare_ism_shaykh():
    # a bare common ism as the شيخ («محمد») names many men → it must NOT disambiguate by itself.
    chains = [
        ["هشيم", "خالد بن مهران الحذاء", "محمد"],
        ["وهيب", "خالد", "محمد"],
    ]
    m = build_map(chains, min_count=1)
    assert resolve("خالد", "وهيب", "محمد", m) == "خالد"


def test_exact_pair_takes_precedence_over_the_relaxation():
    # «يونس» is مشترك under الزهري overall (held), but the exact (شعيب, الزهري) pair names him
    # uniquely → the exact context wins over the (held) شيخ-only relaxation.
    chains = [
        ["معمر", "يونس بن يزيد الأيلي", "الزهري"],
        ["شعيب", "يونس بن عبيد البصري", "الزهري"],
        ["شعيب", "يونس بن عبيد البصري", "الزهري"],
        ["شعيب", "يونس", "الزهري"],
    ]
    m = build_map(chains, min_count=1)
    assert resolve("يونس", "شعيب", "الزهري", m) == "يونس بن عبيد البصري"
