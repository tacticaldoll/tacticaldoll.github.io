## Authored by Schema: .agent/schemas/terminology.schema.yaml
## Reference Workflow: .agent/workflows/consolidate-terminology.md
## Role: Consolidation orchestrator. Validates accumulated draft terms across
## the corpus, quarantines structural/variant noise, demotes over-general terms,
## and promotes the survivors through the managed lexicon flow.
##
## This complements (does not replace) LexiconManager.promote_all_drafts(): the
## final promotion still runs Lexicon.lint() as the terminal gate.

import os
import sys
import json
import argparse

# .agent/scripts (for infra) ------------------------------------------------
scripts_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if scripts_root not in sys.path:
    sys.path.append(scripts_root)
# .agent/lexicon-core/scripts (for lexicon / manager) -----------------------
lexicon_core_scripts = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../lexicon-core/scripts"))
if lexicon_core_scripts not in sys.path:
    sys.path.append(lexicon_core_scripts)

from infra import config
from lexicon import Lexicon, load_json
from manager import LexiconManager, log_info, log_error

import validators as V

REPORT_PATH = os.path.join(config.SCRATCH_DIR, "consolidation-report.md")


# --- Corpus document-frequency ---------------------------------------------
def _post_bodies():
    """Yields the body text (post-frontmatter) of every published post."""
    for root, _dirs, files in os.walk(config.POSTS_DIR):
        if "index.md" in files:
            with open(os.path.join(root, "index.md"), encoding="utf-8") as f:
                content = f.read()
            parts = content.split("+++", 2)
            yield parts[2] if len(parts) >= 3 else content


def compute_df(zh_terms):
    """Returns {zh: number_of_posts_whose_body_contains_zh} and total post count."""
    bodies = list(_post_bodies())
    df = {zh: sum(1 for b in bodies if zh in b) for zh in zh_terms}
    return df, len(bodies)


# --- Classification ---------------------------------------------------------
def classify(terms, existing_zh, df, total_docs):
    """Partitions a {key: item} dict into buckets with reasons.

    Buckets: blocked (1+2, never promote), generic (3, demote to L3),
    review (clean, needs human semantic judgement).
    """
    blocked, generic, review = [], [], []
    for key, item in terms.items():
        zh = item.get("zh", "")
        r = V.check_structural(zh)
        if r:
            blocked.append((key, item, f"① 結構性碎片：{r}"))
            continue
        r = V.check_variant(zh, existing_zh)
        if r:
            blocked.append((key, item, f"② 近義變體：{r}"))
            continue
        r = V.check_generic(zh, df.get(zh, 0), total_docs)
        if r:
            generic.append((key, item, f"③ 過度通用：{r}"))
            continue
        review.append((key, item, "結構乾淨，待人工裁決語意正確性"))
    return blocked, generic, review


def _fmt_bucket(title, rows):
    lines = [f"### {title}（{len(rows)}）", ""]
    if not rows:
        lines.append("（無）")
    for key, item, reason in rows:
        lines.append(f"- **{item.get('zh','')}** `({key})` — {reason}")
        desc = item.get("description", "")
        if desc:
            lines.append(f"  - 描述：{desc}")
    lines.append("")
    return "\n".join(lines)


def write_report(draft_buckets, core_buckets):
    d_blocked, d_generic, d_review = draft_buckets
    c_blocked, c_generic, _ = core_buckets
    out = [
        "# 術語固化複審報告 (Consolidation Review)",
        "",
        "> 由 `consolidate.py --scan` 產出。確定性驗證已濾掉 ①②③；",
        "> 人工**只需裁決下方 DRAFT 的 `REVIEW` 區塊**（否決請自 terminology.draft.json 刪除該條目），再執行 `--apply`。",
        "",
        "## DRAFT（晉升候選，本次 --apply 會處理）",
        "",
        _fmt_bucket("BLOCKED — 將封存，不晉升", d_blocked),
        _fmt_bucket("GENERIC — 將降為 level 3", d_generic),
        _fmt_bucket("REVIEW — 待人工裁決 ④", d_review),
        "## CORE（既有核心庫稽核，唯讀提示；清理需另行再錨定遷移）",
        "",
        _fmt_bucket("既有結構性碎片", c_blocked),
        _fmt_bucket("既有過度通用詞", c_generic),
    ]
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(out))


# --- Modes ------------------------------------------------------------------
def run_scan():
    core = Lexicon(config.TERMINOLOGY_JSON)
    existing_zh = list(core.mapping.keys())
    draft = load_json(config.TERMINOLOGY_DRAFT_JSON) or {}
    core_terms = {core.keys.get(zh, zh): {"zh": zh} for zh in existing_zh}

    # df over the union of zh strings we may flag
    df, total = compute_df(set(existing_zh) | {i.get("zh", "") for i in draft.values()})

    draft_buckets = classify(draft, existing_zh, df, total)
    # for core audit, compare core against itself excluding self (variant check
    # would always self-match), so only run structural + generic on core.
    core_blocked, core_generic = [], []
    for key, item in core_terms.items():
        zh = item["zh"]
        r = V.check_structural(zh)
        if r:
            core_blocked.append((key, item, f"① {r}"))
            continue
        r = V.check_generic(zh, df.get(zh, 0), total)
        if r:
            core_generic.append((key, item, f"③ {r}"))
    core_buckets = (core_blocked, core_generic, [])

    write_report(draft_buckets, core_buckets)

    d_blocked, d_generic, d_review = draft_buckets
    log_info(f"Scanned {len(draft)} draft term(s) against {total} post(s).")
    log_info(f"  DRAFT: blocked={len(d_blocked)} generic={len(d_generic)} review={len(d_review)}")
    log_info(f"  CORE audit (read-only): structural={len(core_blocked)} generic={len(core_generic)}")
    log_info(f"Report written to {os.path.relpath(REPORT_PATH, config.ROOT_DIR)}")
    log_info("Review the report, prune terminology.draft.json, then run --apply.")
    return True


def _archive(items):
    """Moves blocked items into terminology.archive.json (append, keyed)."""
    if not items:
        return
    arch = load_json(config.TERMINOLOGY_ARCHIVE_JSON) or {}
    for key, item, reason in items:
        rec = dict(item)
        rec["archived_reason"] = reason
        arch[key] = rec
    with open(config.TERMINOLOGY_ARCHIVE_JSON, "w", encoding="utf-8") as f:
        json.dump(arch, f, indent=2, ensure_ascii=False)
    log_info(f"Archived {len(items)} blocked term(s) to {os.path.basename(config.TERMINOLOGY_ARCHIVE_JSON)}.")


def run_apply():
    core = Lexicon(config.TERMINOLOGY_JSON)
    existing_zh = list(core.mapping.keys())
    draft = load_json(config.TERMINOLOGY_DRAFT_JSON) or {}
    if not draft:
        log_info("Draft is empty. Nothing to consolidate.")
        return True

    df, total = compute_df({i.get("zh", "") for i in draft.values()})
    blocked, generic, review = classify(draft, existing_zh, df, total)

    # 1. Quarantine blocked (1+2): archive + drop from draft.
    _archive(blocked)
    for key, _item, _r in blocked:
        draft.pop(key, None)

    # 2. Demote generic (3) to level 3 in place.
    for key, _item, _r in generic:
        if key in draft:
            draft[key]["level"] = 3
            log_info(f"  Demoted to L3: {draft[key].get('zh','')} ({key})")

    # 3. Persist the pruned/adjusted draft, then delegate promotion.
    with open(config.TERMINOLOGY_DRAFT_JSON, "w", encoding="utf-8") as f:
        json.dump(draft, f, indent=2, ensure_ascii=False)
    log_info(f"Promoting {len(draft)} surviving draft term(s) "
             f"(blocked={len(blocked)}, demoted={len(generic)}, review-kept={len(review)}).")

    mgr = LexiconManager()
    promoted = mgr.promote_all_drafts()  # runs Lexicon.lint() as terminal gate
    log_info(f"Consolidation complete. Promoted {promoted} term(s) to core.")
    return True


def main():
    parser = argparse.ArgumentParser(description="Terminology Consolidation (validate -> review -> promote)")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--scan", action="store_true", help="Dry-run: validate and write review report (default)")
    group.add_argument("--apply", action="store_true", help="Quarantine/demote, then promote survivors")
    args = parser.parse_args()

    ok = run_apply() if args.apply else run_scan()
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
