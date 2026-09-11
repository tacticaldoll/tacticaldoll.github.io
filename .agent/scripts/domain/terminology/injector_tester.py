# -*- coding: utf-8 -*-
## Authored by Schema: ../../../schemas/terminology.schema.yaml
## Reference Workflow: ../../../workflows/reanchor-posts.md
## Role: Regression harness for TerminologyInjector.apply_lexicon(mode="anchor_first").
##       Pins three documented re-anchoring gaps as assertions of the CORRECT behavior:
##       they FAIL on the current implementation (reproducing each gap) and turn GREEN
##       once the injector is fixed. A positive idempotency control must stay GREEN throughout.
##
## Convention: mirrors lexicon_tester.py (plain asserts + __main__ runner, no pytest dependency).
## Run: python .agent/scripts/domain/terminology/injector_tester.py

import os
import sys
import io

# UTF-8 stdout so Traditional-Chinese fixtures print correctly on Windows consoles.
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_ROOT = os.path.dirname(os.path.dirname(HERE))          # .agent/scripts
LEXICON_CORE_SCRIPTS = os.path.abspath(                        # .agent/lexicon-core/scripts
    os.path.join(SCRIPTS_ROOT, "..", "lexicon-core", "scripts")
)
for p in (SCRIPTS_ROOT, LEXICON_CORE_SCRIPTS):
    if p not in sys.path:
        sys.path.insert(0, p)

from lexicon import Lexicon
from domain.post.post import HugoPost
from domain.terminology.injector import TerminologyInjector

LEXICON = Lexicon()


def _pick_anchorable_term():
    """Returns a real level<3 ZH term (so anchoring is exercised) from the live lexicon."""
    for zh, level in LEXICON.levels.items():
        if level < 3 and LEXICON.zh_to_ens.get(zh):
            return zh
    raise RuntimeError("No level<3 term available in the lexicon to drive the tests.")


def _pick_l3_term():
    """Returns a real level>=3 (IGNORE_LIST) ZH term that contains no other live term
    as a substring (so the fixture is unambiguous)."""
    for zh, level in LEXICON.levels.items():
        if level >= 3 and 2 <= len(zh) <= 4 and not any(
            k != zh and k in zh for k in LEXICON.mapping
        ):
            return zh
    raise RuntimeError("No clean level>=3 term available to drive the bold-strip test.")


def _reanchor(body):
    post = HugoPost()
    post.body = body
    TerminologyInjector().apply_lexicon(post, LEXICON, mode="anchor_first")
    return post.body


def _preview_of(text):
    """The summary region: everything before the <!--more--> separator."""
    return text.split("<!--more-->", 1)[0] if "<!--more-->" in text else text


# --- Gap 1: author-written annotation blocks must survive --------------------
# An author's `> [!IMPORTANT]` callout carries NO machine anchor markers
# (<!-- term: --> / <!-- anchor: -->). Re-anchoring must not delete it.
def test_gap1_author_important_block_survives():
    term = _pick_anchorable_term()
    body = (
        f"正文提到{term}。\n\n"
        "> [!IMPORTANT]\n"
        "> **作者提醒**：這是人工撰寫的內容警示，並非術語定義框。\n\n"
        "結尾段落。\n"
    )
    out = _reanchor(body)
    assert "作者提醒" in out, (
        "Gap 1: author-authored [!IMPORTANT] block was deleted by re-anchoring "
        "(removal regex over-matches; it should require an anchor/term marker)."
    )


# --- Gap 2: orphan inline anchors of removed/archived terms must be cleared ---
# A term no longer in the lexicon leaves a stale `（EN） <!-- term:Key -->` in the
# body. anchor_first claims a full clean-then-reapply, so the orphan must go.
def test_gap2_orphan_anchor_of_removed_term_is_cleaned():
    orphan_zh = "甲乙丙丁戊己庚辛"   # synthetic: guaranteed absent from the lexicon
    assert orphan_zh not in LEXICON.mapping, "fixture invalid: orphan term must not be a real term"
    assert not any(k in orphan_zh for k in LEXICON.mapping), (
        "fixture invalid: orphan term must not contain any live term as a substring"
    )
    body = (
        f"段落引用了一個已被移除的術語 **{orphan_zh}**（Foo Bar Baz） "
        "<!-- term:ZzObsoleteKey -->，其錨點應被清除。\n"
    )
    out = _reanchor(body)
    assert "<!-- term:ZzObsoleteKey -->" not in out, (
        "Gap 2: orphan inline anchor of a removed term survived "
        "(cleanup is driven by the current term list instead of the anchor marker)."
    )


# --- Gap 3': the summary/preview area must not be anchored --------------------
# Anchors and definition callouts belong AFTER <!--more--> (GUIDE §5.111).
# In anchor_first the <!--more--> is placeholder-ized before split_by_more, so
# preview protection is bypassed and the summary gets anchored.
def test_gap3_preview_area_is_not_anchored():
    term = _pick_anchorable_term()
    body = (
        f"這是前言，提到了{term}這個概念。\n\n"
        "<!--more-->\n\n"
        f"正文第一段再次討論{term}的細節。\n\n"
        "正文第二段做總結。\n"
    )
    out = _reanchor(body)
    assert "<!--more-->" in out, "the <!--more--> separator must be preserved"
    preview = _preview_of(out)
    assert "<!-- term:" not in preview, (
        "Gap 3': summary area was anchored (inline <!-- term --> appears before <!--more-->)."
    )
    assert "[!IMPORTANT]" not in preview, (
        "Gap 3': a terminology definition box was placed before <!--more-->, polluting the summary/RSS."
    )


# --- Gap 4: orphan first-occurrence bold of a de-anchored (L3) term is stripped ---
# When a term is demoted to level 3 (IGNORE_LIST), de-anchoring removes its
# anchor/gloss but historically LEFT the **bold** behind. L3 terms are never
# anchored, so that emphasis is residue and must be cleared — but only when the
# term is a SYMMETRIC standalone **詞**; an L3 word at the edge of a longer author
# bold must not break that span.
def test_gap4_orphan_l3_bold_is_stripped():
    l3 = _pick_l3_term()
    out = _reanchor(f"前段文字**{l3}**後段文字。\n")
    assert f"**{l3}**" not in out, (
        f"Gap 4: standalone **{l3}** (level-3 orphan first-occurrence bold) must be stripped."
    )
    assert l3 in out, "Gap 4: the L3 term text itself must survive (only its bold removed)."
    # L3 term as the leading edge of a longer author bold — must stay intact.
    out2 = _reanchor(f"這是一個**{l3}示例**的說明。\n")
    assert f"**{l3}示例**" in out2, (
        f"Gap 4: '**{l3}示例**' (L3 word as edge of a longer bold) must be preserved, not broken."
    )


# --- Gap 5: an author gloss with no anchor marker must survive de-anchoring -----
# anchor_first's global cleanup consumes an optional （bilingual） suffix whether or
# not an anchor marker follows it. A machine anchor always carries the marker; a bare
# `**詞**（English）` is authored text, and stripping it is what removes the author's
# own gloss — and, inside a callout, what drops the line out of
# rules.json protected_alert_patterns so the next pass anchors it.
def test_gap5_author_gloss_without_marker_survives():
    term = _pick_anchorable_term()
    en = LEXICON.zh_to_ens[term][0]
    body = (
        "前段。\n\n"
        "> [!IMPORTANT]\n"
        f"> **{term}**（{en}）：作者手寫的定義，沒有機器標記。\n\n"
        "後段。\n"
    )
    out = _reanchor(body)
    author_line = next((ln for ln in out.splitlines() if "作者手寫的定義" in ln), "")
    assert author_line, "Gap 5: the author's definition line disappeared entirely"
    assert "<!-- term:" not in author_line and "<!-- anchor:" not in author_line, (
        "Gap 5: the author's callout line acquired a machine marker. Its （bilingual） "
        "gloss is consumed by the global cleanup even with no marker attached, which "
        "drops the line out of protected_alert_patterns and exposes it to anchoring — "
        "and a marker is what makes the removal regex delete the whole callout next pass."
    )
    assert f"（{en}）" in author_line, (
        "Gap 5: the author's （bilingual） gloss was stripped although no anchor marker "
        "followed it; only a marker-terminated suffix is machine output."
    )


# --- Gap 6: re-anchoring must not reorder lines within a block -----------------
# _process_paragraph splits a block into heading/protected lines and everything else,
# then emits the headings FIRST. A heading that followed a paragraph is hoisted in
# front of it and glued to its text.
def test_gap6_line_order_is_preserved():
    term = _pick_anchorable_term()
    body = f"段落提到{term}。\n### 後面的標題\n"
    out = _reanchor(body)
    assert out.index("段落提到") < out.index("### 後面的標題"), (
        "Gap 6: a heading that came after a paragraph was hoisted in front of it."
    )


# --- Gap 7: idempotency with an author definition block present ----------------
# The existing control uses a body with no author callout, so the destructive path
# is untested: once the author's line loses protection it gains a term marker, and
# the removal regex then classifies the whole callout as machine output and deletes
# it — author text included.
def test_gap7_idempotent_with_author_definition_block():
    term = _pick_anchorable_term()
    en = LEXICON.zh_to_ens[term][0]
    body = (
        f"正文提到{term}，需要錨定。\n\n"
        "> [!IMPORTANT]\n"
        f"> **{term}**（{en}）：作者手寫的定義。\n\n"
        "### 後續章節\n\n"
        "結尾。\n"
    )
    once = _reanchor(body)
    twice = _reanchor(once)
    assert "作者手寫的定義" in once, "Gap 7: author definition lost on the first pass"
    assert "作者手寫的定義" in twice, (
        "Gap 7: author definition deleted on the second pass — this is the published-content "
        "data loss that blocks reanchor --apply."
    )
    assert once == twice, "Gap 7: re-anchoring is not idempotent when an author callout exists"


# --- Positive control: idempotency must hold (and keep holding after fixes) ---
def test_control_idempotent_on_clean_body():
    term = _pick_anchorable_term()
    body = (
        f"開頭討論{term}。\n\n"
        f"後段再次提到{term}與其他內容。\n\n"
        "收尾段落。\n"
    )
    once = _reanchor(body)
    twice = _reanchor(once)
    assert once == twice, "control: re-anchoring an already-anchored body must be a no-op"


# --- Gap 8: math spans must not be anchored -----------------------------------
# zh keys are matched by plain substring, so a term inside \text{…} used to get an
# anchor comment injected into the formula — `\text{術語 <!-- term:Foo -->}` — which
# corrupts the LaTeX. BlockProtector guards the assembly path, but reanchor.py calls
# apply_lexicon directly and bypasses it, so the injector needs its own guard.
def test_gap8_math_is_not_anchored():
    term = _pick_anchorable_term()
    display = f"$$\n\\text{{{term}}} = x\n$$"
    inline = f"$\\alpha_{{{term}}}$"
    body = (
        f"正文首次提到{term}，建立首錨。\n\n"
        f"{display}\n\n"
        f"行內公式 {inline} 也必須原樣保留。\n\n"
        f"結尾再次提到{term}。\n"
    )
    out = _reanchor(body)
    assert display in out, (
        "Gap 8: display math was rewritten (an anchor was injected inside $$…$$)."
    )
    assert inline in out, (
        "Gap 8: inline math was rewritten (an anchor was injected inside $…$)."
    )
    assert "<!-- term:" in out, (
        "Gap 8: guard over-reached — prose outside the math spans lost its anchor."
    )


TESTS = [
    ("Gap 1  author [!IMPORTANT] survives", test_gap1_author_important_block_survives),
    ("Gap 2  orphan anchor cleaned",        test_gap2_orphan_anchor_of_removed_term_is_cleaned),
    ("Gap 3' preview not anchored",         test_gap3_preview_area_is_not_anchored),
    ("Gap 4  orphan L3 bold stripped",      test_gap4_orphan_l3_bold_is_stripped),
    ("Gap 5  author gloss survives",        test_gap5_author_gloss_without_marker_survives),
    ("Gap 6  line order preserved",         test_gap6_line_order_is_preserved),
    ("Gap 7  idempotent w/ author block",   test_gap7_idempotent_with_author_definition_block),
    ("Gap 8  math not anchored",            test_gap8_math_is_not_anchored),
    ("control idempotency",                 test_control_idempotent_on_clean_body),
]


def main():
    failures = 0
    for name, fn in TESTS:
        try:
            fn()
            print(f"[PASS] {name}")
        except AssertionError as e:
            failures += 1
            print(f"[FAIL] {name}\n       {e}")
        except Exception as e:
            failures += 1
            print(f"[ERROR] {name}: {type(e).__name__}: {e}")
    print(f"\n{len(TESTS) - failures}/{len(TESTS)} passed.")
    if failures:
        print("Failing tests above reproduce the documented gaps; fix the injector to turn them green.")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
