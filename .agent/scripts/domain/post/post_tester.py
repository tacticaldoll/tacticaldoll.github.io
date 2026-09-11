# -*- coding: utf-8 -*-
## Authored by Schema: ../../../schemas/handoff.posts.schema.yaml
## Reference Workflow: ../../../workflows/reanchor-posts.md
## Role: Round-trip identity harness for HugoPost over the PUBLISHED corpus.
##       Pins the property every caller of the model needs but none currently has:
##       load() then save_to_string() with no modification must return the file
##       byte-for-byte. It FAILS today — build_toml_front_matter() reconstructs the
##       front matter from a parsed dict, which drops the `# term:Key` tag comments
##       that carry every tag's anchor identity. That loss is exactly why reanchor.py
##       bypasses the model with a regex split and TagAnchorer edits front matter as
##       raw text: three treatments of one region, because the model is lossy.
##
##       This harness is the gate for making the model comment-preserving. It turns
##       GREEN when the model round-trips the real corpus losslessly, and stays green
##       as callers are migrated onto it.
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


def main():
    ap = argparse.ArgumentParser(description="HugoPost round-trip identity over published posts")
    ap.add_argument("--show", type=int, default=3,
                    help="show a unified diff for the first N differing posts (default 3)")
    args = ap.parse_args()

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
