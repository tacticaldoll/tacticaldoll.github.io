# -*- coding: utf-8 -*-
## Authored by Schema: ../../../schemas/handoff.posts.schema.yaml
## Reference Workflow: ../../../workflows/reanchor-posts.md
## Role: Round-trip identity harness for HugoPost over the PUBLISHED corpus, plus the
##       unit cases around it. Pins the property every caller of the model depends on:
##       load() then save_to_string() with no modification returns the file
##       byte-for-byte, so re-anchoring can rewrite a body without the front matter
##       paying for it.
##
##       It was written red, and the fix landed before the commit closed — audit_kb.py
##       runs these suites as a GOVERNANCE check, so a suite left failing blocks every
##       commit, not just the one that introduced it.
##
##       build_toml_front_matter() rebuilt the front matter from
##       a parsed dict and dropped every `# term:Key` tag comment — the identity each
##       tag is refreshed by — so all 48 published posts failed. That single loss was
##       why three separate treatments of front matter existed. The model now re-emits
##       the block verbatim when untouched and splices only the tags array when the
##       keyed tags change, and the bypasses are retired.
##
##       Keep this green. A regression here does not announce itself: a lossy save
##       silently strips anchors from every post it touches.
##
## Convention: mirrors injector_tester.py (plain asserts + __main__ runner, no pytest).
## Run: python3 .agent/scripts/domain/post/post_tester.py [--show N]

import os
import re
import sys
import io
import glob
import argparse
import difflib

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_ROOT = os.path.dirname(os.path.dirname(HERE))          # .agent/scripts
if SCRIPTS_ROOT not in sys.path:
    sys.path.insert(0, SCRIPTS_ROOT)

from infra import config
from domain.post.post import HugoPost

_TAG_COMMENT = re.compile(r'#\s*term:\S+')


def round_trip(raw):
    """Parse and re-serialize with no modification. Returns the reassembled text."""
    post = HugoPost()
    post.load(content=raw)
    return post.save_to_string()


def classify(raw, out):
    """Names the loss classes present in one round-trip, for triage."""
    kinds = []
    src_comments = len(_TAG_COMMENT.findall(raw))
    out_comments = len(_TAG_COMMENT.findall(out))
    if src_comments > out_comments:
        kinds.append(f"tag-comments-lost({src_comments}->{out_comments})")
    if raw.startswith("﻿") and not out.startswith("﻿"):
        kinds.append("bom-dropped")
    if raw.rstrip() == out.rstrip() and raw != out:
        kinds.append("trailing-whitespace")
    if not kinds:
        kinds.append("other")
    return kinds


def iter_posts():
    for p in sorted(glob.glob(os.path.join(config.POSTS_DIR, "*", "index.md"))):
        yield os.path.basename(os.path.dirname(p)), p


_FIXTURE = (
    '+++\n'
    'title = "示例標題"\n'
    'draft = false\n'
    'tags = [\n'
    '    "分析論述", # term:AnalyticalEssay\n'
    '    "錯誤表面", # term:ErrorSurface\n'
    '  ]\n'
    '+++\n'
    '\n'
    '正文第一段。\n'
)


def test_body_edit_preserves_front_matter():
    """The reanchor case: only the body changes, so the front matter must come back
    verbatim — tag comments included."""
    post = HugoPost()
    post.load(content=_FIXTURE)
    post.body = post.body.replace("正文第一段。", "正文第一段，已改寫。")
    out = post.save_to_string()
    assert "# term:AnalyticalEssay" in out and "# term:ErrorSurface" in out, (
        "body-only edit dropped the tag comments — the verbatim front matter path did not run"
    )
    assert "已改寫" in out, "body-only edit did not take effect"


def test_keyed_tag_edit_preserves_the_rest():
    """A tag's identity is its `# term:Key`, so a display can be corrected while the key
    stays put. Editing tags must not cost the other front matter fields their formatting
    — that cost is exactly why tag editing lived outside the model as raw-text regex."""
    post = HugoPost()
    post.load(content=_FIXTURE)
    assert post.tag_entries == [("分析論述", "AnalyticalEssay"), ("錯誤表面", "ErrorSurface")], (
        "keyed tags were not parsed out of the verbatim front matter"
    )
    post.set_tag_entries([("分析論述", "AnalyticalEssay"), ("錯誤介面", "ErrorSurface")])
    out = post.save_to_string()
    assert '"錯誤介面", # term:ErrorSurface' in out, "keyed rename lost the display or the key"
    assert '"分析論述", # term:AnalyticalEssay' in out, "an untouched tag lost its comment"
    assert 'title = "示例標題"' in out, "a tag edit damaged another front matter field"
    assert out.endswith("正文第一段。\n"), "a tag edit damaged the body"


def test_tag_splice_is_idempotent():
    """Writing back the same entry set twice must converge — re-anchoring runs
    repeatedly over the published corpus, so a splice that drifts would accumulate."""
    post = HugoPost()
    post.load(content=_FIXTURE)
    post.set_tag_entries(post.tag_entries)
    once = post.save_to_string()
    again = HugoPost()
    again.load(content=once)
    again.set_tag_entries(again.tag_entries)
    assert once == again.save_to_string(), "splicing an unchanged entry set is not a no-op"


def test_no_tags_block_untouched():
    """A post with no keyed tags has nothing to edit. tag_entries must be None rather
    than empty, so a caller cannot mistake 'no tags array' for 'an empty one' and
    write the array away."""
    fm_only = '+++\ntitle = "無標籤"\ndraft = false\n+++\n\n正文。\n'
    post = HugoPost()
    post.load(content=fm_only)
    assert post.tag_entries is None, "a post without keyed tags must report None, not []"
    assert post.save_to_string() == fm_only, "a post without tags must round-trip untouched"


def test_unkeyed_tags_are_refused():
    """An array the model cannot key must be reported as unmanageable, not as an empty
    or partial entry list. Regenerating the array from parsed entries would silently
    drop every tag carrying no `# term:Key`, and an unkeyed tag cannot be looked up to
    decide whether it deserved to survive."""
    single_line = '+++\ntitle = "x"\ntags = ["甲", "乙"]\n+++\n\n正文。\n'
    post = HugoPost()
    post.load(content=single_line)
    assert post.tag_entries is None, "a fully unkeyed tags array must be refused"
    assert post.save_to_string() == single_line, "refusing must still round-trip verbatim"

    partial = ('+++\ntitle = "x"\ntags = [\n'
               '    "甲", # term:K1\n'
               '    "乙"\n'
               '  ]\n+++\n\n正文。\n')
    post2 = HugoPost()
    post2.load(content=partial)
    assert post2.tag_entries is None, (
        "a partially keyed tags array must be refused — keeping only the keyed entry "
        "would drop the other one on write-back"
    )
    assert post2.save_to_string() == partial, "refusing must still round-trip verbatim"


def test_set_title_splices_only_that_line():
    """Correcting a title must not cost the rest of the front matter its formatting or
    its tag comments — the maintenance pass that rewrites a title is the same pass that
    must leave every anchor intact."""
    post = HugoPost()
    post.load(content=_FIXTURE)
    assert post.set_title("改過的標題") is True, "set_title refused a plain title"
    out = post.save_to_string()
    assert 'title = "改過的標題"' in out, "the title was not replaced"
    assert '"分析論述", # term:AnalyticalEssay' in out, "a title edit dropped a tag comment"
    assert "draft = false" in out, "a title edit damaged another field"
    assert out.endswith("正文第一段。\n"), "a title edit damaged the body"
    assert post.save_to_string() == out, "set_title is not stable across repeated saves"


def test_set_scalar_field_reaches_description():
    """Correction has to reach every published scalar field, not just the title. The
    description ships in listings and RSS, and a variant added to the lexicon after
    publication was stranded there until this path existed."""
    fm = ('+++\ntitle = "標題"\ndescription = "描述含舊寫法"\ndraft = false\n'
          'tags = [\n    "分析論述", # term:AnalyticalEssay\n  ]\n+++\n\n正文。\n')
    post = HugoPost()
    post.load(content=fm)
    assert post.set_scalar_field("description", "描述含新寫法") is True
    out = post.save_to_string()
    assert 'description = "描述含新寫法"' in out, "the description was not replaced"
    assert 'title = "標題"' in out, "a description edit damaged the title"
    assert "# term:AnalyticalEssay" in out, "a description edit dropped a tag comment"
    assert out.endswith("正文。\n"), "a description edit damaged the body"


def test_set_title_refuses_escaping():
    """A title carrying a quote or a backslash would need TOML escaping. Nothing in the
    corpus has ever carried one, so the guard is cheaper than an escaping routine that
    nothing exercises — and a wrong escape corrupts the whole front matter block."""
    post = HugoPost()
    post.load(content=_FIXTURE)
    assert post.set_title('帶"引號"的標題') is False, "a title needing escaping must be refused"
    assert post.set_title("帶\\反斜線的標題") is False, "a title with a backslash must be refused"
    assert post.save_to_string() == _FIXTURE, "a refused title edit must leave the post untouched"


def test_metadata_edit_still_rebuilds():
    """The boundary of the fix: once metadata is mutated the verbatim prefix is stale,
    so save must fall back to rebuilding rather than re-emitting the old front matter."""
    post = HugoPost()
    post.load(content=_FIXTURE)
    post.metadata["title"] = "改過的標題"
    out = post.save_to_string()
    assert "改過的標題" in out, (
        "metadata edit was ignored — a stale verbatim front matter was re-emitted"
    )
    assert "示例標題" not in out, "the old title survived a metadata edit"


def main():
    ap = argparse.ArgumentParser(description="HugoPost round-trip identity over published posts")
    ap.add_argument("--show", type=int, default=3,
                    help="show a unified diff for the first N differing posts (default 3)")
    args = ap.parse_args()

    for name, fn in (("body-only edit preserves front matter", test_body_edit_preserves_front_matter),
                     ("keyed tag edit preserves the rest",     test_keyed_tag_edit_preserves_the_rest),
                     ("tag splice is idempotent",              test_tag_splice_is_idempotent),
                     ("no tags block untouched",               test_no_tags_block_untouched),
                     ("unkeyed tags are refused",              test_unkeyed_tags_are_refused),
                     ("set_title splices only that line",      test_set_title_splices_only_that_line),
                     ("set_scalar_field reaches description",  test_set_scalar_field_reaches_description),
                     ("set_title refuses escaping",            test_set_title_refuses_escaping),
                     ("metadata edit still rebuilds",          test_metadata_edit_still_rebuilds)):
        fn()
        print(f"[PASS] {name}")
    print()

    total = 0
    differing = []
    by_kind = {}

    for slug, path in iter_posts():
        total += 1
        raw = open(path, encoding="utf-8").read()
        try:
            out = round_trip(raw)
        except Exception as e:
            differing.append((slug, raw, "", [f"raised:{type(e).__name__}"]))
            by_kind["raised"] = by_kind.get("raised", 0) + 1
            continue
        if raw != out:
            kinds = classify(raw, out)
            differing.append((slug, raw, out, kinds))
            for k in kinds:
                head = k.split("(")[0]
                by_kind[head] = by_kind.get(head, 0) + 1

    print(f"published posts scanned: {total}")
    print(f"round-trip identical:    {total - len(differing)}")
    print(f"round-trip DIFFERING:    {len(differing)}")
    if by_kind:
        print("\nloss classes:")
        for k in sorted(by_kind):
            print(f"  {k}: {by_kind[k]}")

    for slug, raw, out, kinds in differing[:args.show]:
        print(f"\n--- {slug}  [{', '.join(kinds)}] ---")
        diff = difflib.unified_diff(
            raw.splitlines(), out.splitlines(),
            fromfile="on-disk", tofile="round-tripped", lineterm="", n=1,
        )
        for i, line in enumerate(diff):
            if i > 24:
                print("  …")
                break
            print(f"  {line}")

    if differing:
        print(f"\n{len(differing)}/{total} posts do not survive a no-op round trip.")
        print("The model is lossy; callers bypass it for that reason. "
              "Make the front matter model comment-preserving to turn this green.")
    else:
        print(f"\n{total}/{total} posts survive a no-op round trip byte-for-byte.")

    assert not differing, (
        f"round-trip identity failed on {len(differing)}/{total} published posts"
    )


if __name__ == "__main__":
    try:
        main()
    except AssertionError as e:
        print(f"\n[FAIL] {e}")
        sys.exit(1)
    sys.exit(0)
