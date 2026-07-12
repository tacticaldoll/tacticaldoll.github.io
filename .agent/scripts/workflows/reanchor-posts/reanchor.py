## Authored by Schema: .agent/schemas/terminology.schema.yaml
## Reference Workflow: .agent/workflows/reanchor-posts.md
## Role: Idempotent re-anchor migration. Propagates the current core lexicon
## into published post BODIES, reusing the publish pipeline's anchoring engine.
##
## SAFETY: The TOML front matter is preserved VERBATIM (never round-tripped
## through tomllib), because parse drops the `# term:Key` tag comments and a
## re-serialize would destroy all tag anchors. Only the body is rewritten.

import os
import re
import sys
import argparse

# .agent/scripts (for infra, domain) ----------------------------------------
scripts_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if scripts_root not in sys.path:
    sys.path.append(scripts_root)
# .agent/lexicon-core/scripts (for lexicon) ---------------------------------
lexicon_core_scripts = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../lexicon-core/scripts"))
if lexicon_core_scripts not in sys.path:
    sys.path.append(lexicon_core_scripts)

from infra import config
from infra.utils import log_info, log_error
from lexicon import Lexicon
from domain.post.post import HugoPost
from domain.terminology.injector import TerminologyInjector
from domain.terminology.tag_anchor import TagAnchorer

REPORT_PATH = os.path.join(config.SCRATCH_DIR, "reanchor-report.md")

# Splits a post into (verbatim front-matter block incl. both +++, body).
_FM_SPLIT = re.compile(r'^(﻿?\+\+\+[ \t]*\n.*?\n\+\+\+[ \t]*\n)(.*)$', re.DOTALL)


def _count_anchors(text):
    return len(re.findall(r'<!--\s*term:', text)), len(re.findall(r'<!--\s*anchor:', text))


def reanchor_body(body, lexicon):
    """Returns the body with anchors stripped and re-applied from lexicon."""
    tmp = HugoPost()
    tmp.body = body
    TerminologyInjector().apply_lexicon(tmp, lexicon, mode="anchor_first")
    return tmp.body


# --- Pre-write safety gate -------------------------------------------------
# Re-anchoring is a blind text projection: it cannot tell a corrupted result
# from a clean one. Three real corruption classes were observed in practice,
# all when a corrected term's OLD zh lingered in post prose:
#   Bug 1  bold breakage   — `**與語意邊界**` -> `**與**語意邊界**`  (anchor split a **…** span)
#   Bug 2  substring mis-anchor — `**補形狀**` -> `**補**形狀**（Data Shape）` (matched 形狀 mid-word)
#   Bug 3  over-anchoring   — a generic zh (e.g. 歸屬) matching 18 prose spots in one post
# Bugs 1 & 2 share one machine-detectable signature: a line whose `**` count
# becomes odd (broken emphasis nesting). Bug 3 shows as one term gaining many
# anchors in a single post. These detectors gate --apply so corruption is
# surfaced and quarantined instead of silently written.
_TERM_KEY_RE = re.compile(r'<!--\s*term:([A-Za-z0-9_]+)\s*-->')
OVER_ANCHOR_THRESHOLD = 8  # one term gaining >= this many anchors in one post -> suspect over-generic zh


def _odd_bold_lines(text):
    """Count lines whose `**` markers are unbalanced (odd) — i.e. broken bold."""
    return sum(1 for ln in text.splitlines() if ln.count("**") % 2 == 1)


def _terms_by_key(text):
    counts = {}
    for k in _TERM_KEY_RE.findall(text):
        counts[k] = counts.get(k, 0) + 1
    return counts


def diagnose(old_body, new_body):
    """Returns a list of human-readable warning strings for one re-anchored body."""
    warnings = []
    odd_delta = _odd_bold_lines(new_body) - _odd_bold_lines(old_body)
    if odd_delta > 0:
        warnings.append(f"粗體可能斷裂：新增 {odd_delta} 行 `**` 數量不成對"
                        "（錨點疑似插入並破壞 `**…**` 巢狀；常見於舊 zh 仍以散文殘留）")
    before, after = _terms_by_key(old_body), _terms_by_key(new_body)
    for key in sorted(after):
        gain = after[key] - before.get(key, 0)
        if gain >= OVER_ANCHOR_THRESHOLD:
            warnings.append(f"過度錨定：`{key}` 在本篇新增 {gain} 個錨點"
                            "（疑似 zh 過泛，匹配到大量散文）")
    return warnings


def process_post(path, lexicon, tag_anchorer):
    """Computes the re-anchored content for one post without writing.

    Body anchors are re-applied via the injector; the front-matter `tags` block is
    refreshed in place via the shared TagAnchorer (identity = the `# term:Key`). Every
    other byte of the front matter is preserved verbatim.

    Returns dict: {changed, term_delta, anchor_delta, tag_refreshed, tag_dropped,
    new_content} or None on parse failure.
    """
    with open(path, encoding="utf-8") as f:
        original = f.read()
    m = _FM_SPLIT.match(original)
    if not m:
        log_error(f"  [SKIP] No parseable front matter: {os.path.relpath(path, config.POSTS_DIR)}")
        return None
    fm_block, body = m.group(1), m.group(2)

    new_fm_block, tag_stats = tag_anchorer.reanchor_tags_block(fm_block)
    before_t, before_a = _count_anchors(body)
    new_body = reanchor_body(body, lexicon)
    after_t, after_a = _count_anchors(new_body)

    new_content = new_fm_block + new_body
    changed = new_content != original
    return {
        "changed": changed,
        "term_delta": after_t - before_t,
        "anchor_delta": after_a - before_a,
        "tag_refreshed": tag_stats["refreshed"],
        "tag_dropped": tag_stats["dropped"],
        "warnings": diagnose(body, new_body) if changed else [],
        "new_content": new_content,
    }


def _iter_posts(slug_filter=None):
    for root, _dirs, files in os.walk(config.POSTS_DIR):
        if "index.md" in files:
            slug = os.path.basename(root)
            if slug_filter and slug_filter not in slug:
                continue
            yield slug, os.path.join(root, "index.md")


def run(apply, slug_filter, force=False):
    lexicon = Lexicon(config.TERMINOLOGY_JSON)
    tag_anchorer = TagAnchorer(lexicon)
    rows, changed, written, quarantined = [], 0, 0, 0

    for slug, path in sorted(_iter_posts(slug_filter)):
        res = process_post(path, lexicon, tag_anchorer)
        if res is None:
            continue
        if res["changed"]:
            changed += 1
            warnings = res["warnings"]
            rows.append((slug, res["term_delta"], res["anchor_delta"],
                         res["tag_refreshed"], res["tag_dropped"], warnings))
            if apply:
                # SAFETY GATE: a flagged post is quarantined (not written) unless --force,
                # so blind corruption is surfaced for human review instead of shipped.
                if warnings and not force:
                    quarantined += 1
                    log_error(f"  [QUARANTINE] {slug}: {len(warnings)} warning(s); not written. "
                              "Inspect, fix prose, or pass --force.")
                    continue
                with open(path, "w", encoding="utf-8") as f:
                    f.write(res["new_content"])
                written += 1

    _write_report(rows, apply, force)
    mode = "APPLY" if apply else "SCAN (dry-run, no writes)"
    flagged = sum(1 for r in rows if r[5])
    log_info(f"[{mode}] {changed} post(s) would change; {flagged} carry warning(s)."
             + (f" Wrote {written}, quarantined {quarantined}." if apply else ""))
    log_info(f"Report: {os.path.relpath(REPORT_PATH, config.ROOT_DIR)}")
    if not apply and changed:
        log_info("Review the report, then re-run with --apply to write content/.")
    if apply and quarantined:
        log_info("Quarantined posts likely have OLD zh lingering in prose — fix the prose, then re-apply.")
    # Non-zero exit when corruption was detected but not forced through, so callers/CI notice.
    return not (apply and quarantined)


def _write_report(rows, apply, force=False):
    flagged = [r for r in rows if r[5]]
    out = [
        "# 貼文再錨定報告 (Re-anchor " + ("Apply" if apply else "Scan") + ")",
        "",
        f"> {'已套用' if apply else 'Dry-run（未寫入）'}。term = 內文 `<!-- term -->` 錨點，anchor = 定義框，"
        "tag刷新 = 標籤顯示值依鍵刷新數，tag刪除 = 孤兒/降級標籤刪除數。",
        "",
        f"變更貼文數：**{len(rows)}**　|　帶警告：**{len(flagged)}**"
        + ("　（--force 已關閉防線）" if force else ""),
        "",
    ]
    if not rows:
        out.append("（無貼文需變更——術語庫、內文與標籤已一致，冪等 no-op。）")
    else:
        out.append("| 貼文 | term Δ | anchor Δ | tag刷新 | tag刪除 | ⚠ |")
        out.append("|---|---:|---:|---:|---:|:--|")
        for slug, td, ad, tr, tdrop, w in rows:
            out.append(f"| {slug} | {td:+d} | {ad:+d} | {tr} | {tdrop} | {'⚠×'+str(len(w)) if w else ''} |")
    if flagged:
        out += ["", "## ⚠ 安全防線警告（apply 時除非 --force 否則跳過寫入）", ""]
        for slug, _td, _ad, _tr, _tdrop, w in flagged:
            out.append(f"### {slug}")
            for msg in w:
                out.append(f"- {msg}")
            out.append("")
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(out))


def main():
    parser = argparse.ArgumentParser(description="Re-anchor published posts from the current lexicon")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--scan", action="store_true", help="Dry-run: report changes, write nothing (default)")
    group.add_argument("--apply", action="store_true", help="Write re-anchored bodies into content/")
    parser.add_argument("--post", help="Limit to posts whose slug contains this substring")
    parser.add_argument("--force", action="store_true",
                        help="Write even posts that tripped a safety warning (use only after manual inspection)")
    args = parser.parse_args()

    ok = run(apply=args.apply, slug_filter=args.post, force=args.force)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
