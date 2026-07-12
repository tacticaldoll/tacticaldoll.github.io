## Authored by Schema: .agent/schemas/terminology.schema.yaml
## Reference Workflow: .agent/workflows/reanchor-posts.md
## Role: READ-ONLY post health check ("貼文體檢"). Detects fluency/grammar breakage
## around term references that blind text projection (reanchor) and past botched
## find-replace passes leave behind. Writes NOTHING; emits a review report.
##
## Detectors (all mechanical, advisory — the fluency VERDICT is a human/LLM call):
##   orphan_garble  a known dead garble string lingering in prose (e.g. a past
##                  find-replace that swapped an English token for a CJK phrase,
##                  even inside English words: OpenSpec -> Open<phrase>)
##   broken_glue    a CJK char glued directly to a lowercase-latin run, i.e. an
##                  English word split by an injected CJK phrase (規格ialists)
##   cap_glue       a CapitalizedWord glued to a long CJK run (Open<phrase>)
##   odd_bold       a line whose `**` count is odd (broken emphasis nesting)
## Skips fenced code blocks. Orphan list is extensible via --garble.

import os
import re
import sys
import glob
import argparse

scripts_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if scripts_root not in sys.path:
    sys.path.append(scripts_root)

from infra import config
from infra.utils import log_info

REPORT_PATH = os.path.join(config.SCRATCH_DIR, "fluency-report.md")
_CJK = r'一-鿿'
# Dead garble strings to hunt by default. These are NOT current lexicon terms;
# they are residue of past find-replace accidents. Extend with --garble.
DEFAULT_GARBLES = ["具備約束力的規格"]

_BROKEN_GLUE = re.compile(rf'[{_CJK}][a-z]{{2,}}')
_CAP_GLUE = re.compile(rf'[A-Z][a-z]+[{_CJK}]{{4,}}')
_BASES_GLUE = re.compile(rf'[{_CJK}]+bases\b')


def scan_post(path, garbles):
    """Returns list of (line_no, detector, snippet, full_line) for one post body."""
    hits = []
    in_fence = False
    for n, raw in enumerate(open(path, encoding="utf-8"), 1):
        line = raw.rstrip("\n")
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        for g in garbles:
            if g in line:
                hits.append((n, "orphan_garble", g, line))
        for m in _CAP_GLUE.finditer(line):
            hits.append((n, "cap_glue", m.group(), line))
        for m in _BASES_GLUE.finditer(line):
            hits.append((n, "broken_glue", m.group(), line))
        for m in _BROKEN_GLUE.finditer(line):
            # cap_glue / bases already cover their cases; report the rest
            hits.append((n, "broken_glue", m.group(), line))
        # Ignore Python ``**kwargs`` / ``*args`` so they don't read as broken bold.
        bold_stars = line.replace("**kwargs", "").replace("*args", "").count("**")
        if bold_stars % 2 == 1:
            hits.append((n, "odd_bold", "", line))
    return hits


def _iter_posts(slug_filter=None):
    for p in sorted(glob.glob(os.path.join(config.POSTS_DIR, "*", "index.md"))):
        slug = os.path.basename(os.path.dirname(p))
        if slug_filter and slug_filter not in slug:
            continue
        yield slug, p


def main():
    ap = argparse.ArgumentParser(description="Read-only post fluency/garble health check")
    ap.add_argument("--post", help="Limit to posts whose slug contains this substring")
    ap.add_argument("--garble", action="append", default=[],
                    help="Extra dead garble string to hunt (repeatable)")
    args = ap.parse_args()
    garbles = DEFAULT_GARBLES + args.garble

    by_detector = {}
    out = ["# 貼文體檢報告 (Fluency / Garble Scan)", "",
           "> 由 `scan_fluency.py` 唯讀產出。偵測散文中的語法斷裂候選，"
           "已跳過程式碼區塊。判斷由人/LLM 裁決。", ""]
    total_posts = 0
    post_blocks = []
    for slug, path in _iter_posts(args.post):
        hits = scan_post(path, garbles)
        if not hits:
            continue
        total_posts += 1
        post_blocks.append(f"## {slug}（{len(hits)}）")
        for n, det, snip, line in hits:
            by_detector[det] = by_detector.get(det, 0) + 1
            shown = (line[:110] + "…") if len(line) > 110 else line
            tag = f"`{snip}`" if snip else ""
            post_blocks.append(f"- L{n} [{det}] {tag}")
            post_blocks.append(f"  - `{shown}`")

    out.append("## 摘要")
    for det in ("orphan_garble", "cap_glue", "broken_glue", "odd_bold"):
        out.append(f"- {det}: {by_detector.get(det, 0)}")
    out.append(f"- 受影響貼文: {total_posts}")
    out.append("")
    out += post_blocks

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(out))
    log_info(f"Fluency scan: {sum(by_detector.values())} hit(s) across {total_posts} post(s).")
    for det in ("orphan_garble", "cap_glue", "broken_glue", "odd_bold"):
        log_info(f"  {det}: {by_detector.get(det, 0)}")
    log_info(f"Report: {os.path.relpath(REPORT_PATH, config.ROOT_DIR)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
