# -*- coding: utf-8 -*-
## Authored by Schema: ../../../schemas/terminology.schema.yaml
## Reference Workflow: ../../../workflows/reanchor-posts.md
## Role: Regression harness for TagAnchorer (the shared tag-anchoring SSOT). Pins the
##       KEY-DRIVEN reanchor semantics: a tag's identity is its # term:Key, the display is
##       refreshed from the current SSOT, and tags are dropped only on removal/downgrade.
##
## Convention: plain asserts + __main__ runner (mirrors lexicon_tester.py / injector_tester.py).
## Run: python .agent/scripts/domain/terminology/tag_anchor_tester.py

import os
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_ROOT = os.path.dirname(os.path.dirname(HERE))
LEXICON_CORE_SCRIPTS = os.path.abspath(os.path.join(SCRIPTS_ROOT, "..", "lexicon-core", "scripts"))
for p in (SCRIPTS_ROOT, LEXICON_CORE_SCRIPTS):
    if p not in sys.path:
        sys.path.insert(0, p)

from lexicon import Lexicon
from domain.terminology.tag_anchor import TagAnchorer

LEX = Lexicon()
ANCHORER = TagAnchorer(LEX)


def _a_genre_key():
    assert ANCHORER.genre_key_to_zh, "fixture: taxonomy must define genres"
    # prefer a genre whose canonical display we can assert against
    return next(iter(ANCHORER.genre_key_to_zh.items()))  # (key, canonical_zh)


def _a_level_lt3_term():
    for zh, lvl in LEX.levels.items():
        if lvl < 3 and LEX.keys.get(zh):
            return zh, LEX.keys[zh]
    raise RuntimeError("fixture: need a level<3 term with a key")


def _a_level_ge3_term():
    for zh, lvl in LEX.levels.items():
        if lvl >= 3 and LEX.keys.get(zh):
            return zh, LEX.keys[zh]
    return None  # may legitimately not exist


# --- genre: refresh display BY KEY, never drop -------------------------------
def test_genre_display_refreshed_by_key():
    key, canonical = _a_genre_key()
    out = ANCHORER.reanchor_entry("天差地遠的舊顯示值", key)
    assert out is not None, "genre tag must never be dropped"
    assert out == (canonical, key), f"genre display must refresh to taxonomy SSOT, got {out}"


# --- tech term level<3: refresh display BY KEY, keep -------------------------
def test_tech_term_refreshed_by_key():
    zh, key = _a_level_lt3_term()
    canonical = ANCHORER._canonical_term_display(zh)
    out = ANCHORER.reanchor_entry("過時顯示", key)
    assert out == (canonical, key), f"tech tag must refresh to canonical display, got {out}"


# --- downgrade to level>=3: DROP (D2 policy = drop whole tag) -----------------
def test_downgraded_term_dropped():
    t = _a_level_ge3_term()
    if t is None:
        print("       (skipped: no level>=3 term in lexicon)")
        return
    zh, key = t
    out = ANCHORER.reanchor_entry(zh, key)
    assert out is None, f"a tag whose term is level>=3 must be dropped, got {out}"


# --- removed term (key gone from all SSOTs): DROP ----------------------------
def test_removed_key_dropped():
    out = ANCHORER.reanchor_entry("已移除的術語顯示", "ZzDefinitelyRemovedKey12345")
    assert out is None, f"a tag whose key resolves nowhere must be dropped, got {out}"


# --- block: refresh + dedup + drop, with the rest of FM byte-identical -------
def test_tags_block_reanchor():
    gkey, gcanon = _a_genre_key()
    zh, tkey = _a_level_lt3_term()
    fm = (
        "+++\n"
        'title = "保留我"\n'
        "tags = [\n"
        f'    "舊genre顯示", # term:{gkey}\n'
        f'    "舊tech顯示", # term:{tkey}\n'
        f'    "重複genre", # term:{gkey}\n'
        '    "孤兒", # term:ZzRemovedKey99999\n'
        "  ]\n"
        "draft = false\n"
        "+++\n"
    )
    out, stats = ANCHORER.reanchor_tags_block(fm)
    # genre refreshed to canonical, appears exactly once (dedup)
    assert out.count(f"# term:{gkey}") == 1, "duplicate genre key must be merged to one"
    assert f'"{gcanon}", # term:{gkey}' in out, "genre display must be refreshed"
    # orphan dropped
    assert "ZzRemovedKey99999" not in out, "orphan key must be dropped"
    assert stats["dropped"] >= 2, f"expected >=2 drops (dup + orphan), got {stats}"
    # rest of front matter preserved verbatim
    assert 'title = "保留我"' in out and "draft = false" in out, "non-tags FM must be preserved"


# --- idempotency: reanchoring an already-fresh block is a no-op --------------
def test_block_idempotent():
    gkey, _ = _a_genre_key()
    zh, tkey = _a_level_lt3_term()
    fm = (
        "+++\n"
        "tags = [\n"
        f'    "x", # term:{gkey}\n'
        f'    "y", # term:{tkey}\n'
        "  ]\n"
        "+++\n"
    )
    once, _ = ANCHORER.reanchor_tags_block(fm)
    twice, _ = ANCHORER.reanchor_tags_block(once)
    assert once == twice, "reanchoring an already-fresh tags block must be a no-op"


# --- no tags block: untouched ------------------------------------------------
def test_no_tags_block_untouched():
    fm = "+++\ntitle = \"x\"\ndraft = false\n+++\n"
    out, stats = ANCHORER.reanchor_tags_block(fm)
    assert out == fm and stats == {"refreshed": 0, "dropped": 0}


TESTS = [
    ("genre display refreshed by key", test_genre_display_refreshed_by_key),
    ("tech term refreshed by key",     test_tech_term_refreshed_by_key),
    ("downgraded term dropped",        test_downgraded_term_dropped),
    ("removed key dropped",            test_removed_key_dropped),
    ("tags block reanchor",            test_tags_block_reanchor),
    ("block idempotent",               test_block_idempotent),
    ("no tags block untouched",        test_no_tags_block_untouched),
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
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
