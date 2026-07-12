## Authored by Schema: .agent/schemas/terminology.schema.yaml
## Reference Workflow: .agent/workflows/consolidate-terminology.md
## Role: Apply human-approved corrections to EXISTING core terms via the
## sanctioned LexiconManager.apply_corrections() path (key = identity, lint-gated,
## atomic). Reads a corrections-draft (the human review surface) and consumes ONLY
## entries whose `decision == "approve"`. This is the in-place sibling of the
## draft→promote intake flow: draft = new-term intake; corrections-draft = fixing
## terms already in the SSOT. Per consolidate-terminology.md §"Existing Pollution",
## applying a correction is a destructive change to published consistency, so the
## next step is ALWAYS reanchor.py --scan (this script prints that reminder).

import os
import sys
import json
import argparse

scripts_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if scripts_root not in sys.path:
    sys.path.append(scripts_root)
lexicon_core_scripts = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../lexicon-core/scripts"))
if lexicon_core_scripts not in sys.path:
    sys.path.append(lexicon_core_scripts)

from infra import config
from lexicon import Lexicon, load_json
from manager import LexiconManager, log_info, log_error

CORRECTIONS_PATH = os.path.join(config.SCRATCH_DIR, "terminology.corrections.json")
REPORT_PATH = os.path.join(config.SCRATCH_DIR, "corrections-report.md")
_APPROVE = {"approve", "approved", "yes", "true"}
_FIELDS = LexiconManager.EDITABLE_FIELDS


def _load_corrections():
    data = load_json(CORRECTIONS_PATH)
    if not data:
        return {}
    # Drop the human-facing _meta block and any _-prefixed key.
    return {k: v for k, v in data.items() if not k.startswith("_")}


def _approved(corrections):
    """Returns {key: {field: value}} for approved entries with a usable `after`."""
    out, skipped = {}, []
    for key, rec in corrections.items():
        decision = str(rec.get("decision", "pending")).strip().lower()
        after = rec.get("after")
        if decision not in _APPROVE:
            skipped.append((key, f"decision={decision}"))
            continue
        if not after:
            skipped.append((key, "approved but `after` is empty/null"))
            continue
        fields = {f: v for f, v in after.items() if f in _FIELDS}
        bad = [f for f in after if f not in _FIELDS]
        if bad:
            log_error(f"  {key}: ignoring non-editable field(s) {bad}")
        if fields:
            out[key] = fields
        else:
            skipped.append((key, "no editable fields in `after`"))
    return out, skipped


def _write_report(core, corrections, approved, skipped, applied, lint_ok, mode):
    lines = [
        f"# 術語修正報告 (Corrections {'Apply' if mode=='apply' else 'Scan'})",
        "",
        f"> 來源：`{os.path.relpath(CORRECTIONS_PATH, config.ROOT_DIR)}`。"
        f"{'已套用。' if mode=='apply' else 'Dry-run（未寫入 SSOT）。'} 僅取 decision=approve。",
        "",
        f"候選 {len(corrections)} 條 | 核准 {len(approved)} 條 | 跳過 {len(skipped)} 條 | "
        f"lint：{'PASS' if lint_ok else 'FAIL'}",
        "",
        "## 核准並" + ("套用" if mode == "apply" else "預備套用") + "的變更",
        "",
    ]
    if approved:
        lines.append("| Key | 欄位 | before | after |")
        lines.append("|---|---|---|---|")
        for key, fields in approved.items():
            for f, v in fields.items():
                before = core.descriptions.get(core.mapping_lower.get(key, ""), "") if f == "description" else ""
                # before value pulled live from current core by key
                cur = _current_value(core, key, f)
                lines.append(f"| {key} | {f} | {cur} | {v} |")
    else:
        lines.append("（無核准項）")
    lines += ["", "## 跳過", ""]
    if skipped:
        for key, why in skipped:
            lines.append(f"- `{key}` — {why}")
    else:
        lines.append("（無）")
    if mode == "scan":
        lines += ["", "---", "確認無誤後執行 `correct.py --apply`，再 `reanchor.py --scan`。"]
    else:
        lines += ["", "---",
                  f"已套用 {applied} 條至 core。**下一步必做**：`python3 .agent/scripts/workflows/reanchor-posts/reanchor.py --scan` 評估貼文回貼影響。"]
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def _current_value(core, key, field):
    """Live value of `field` for the core term identified by CamelCase key."""
    # key -> zh
    zh = next((z for z, k in core.keys.items() if k == key), None)
    if zh is None:
        return "(key 不存在)"
    if field == "zh":
        return zh
    if field == "description":
        return core.descriptions.get(zh, "")
    if field == "en":
        return "/".join(core.zh_to_ens.get(zh, []))
    if field == "level":
        return str(core.levels.get(zh, ""))
    return ""


def run(mode):
    corrections = _load_corrections()
    if not corrections:
        log_info(f"No corrections found in {os.path.relpath(CORRECTIONS_PATH, config.ROOT_DIR)}.")
        return True
    core = Lexicon(config.TERMINOLOGY_JSON)
    approved, skipped = _approved(corrections)

    # Validate keys exist; move unknowns to skipped.
    known_keys = set(core.keys.values())
    for key in list(approved):
        if key not in known_keys:
            skipped.append((key, "key 不在 core(可能已改名/移除)"))
            approved.pop(key)

    log_info(f"Corrections: {len(corrections)} candidate(s), {len(approved)} approved, {len(skipped)} skipped.")

    applied, lint_ok = 0, True
    if mode == "apply":
        if not approved:
            log_info("Nothing approved to apply.")
        else:
            mgr = LexiconManager(lexicon=core)
            applied = mgr.apply_corrections(approved)  # lint-gated, atomic
            lint_ok = applied > 0
            if applied == 0:
                log_error("apply_corrections returned 0 (lint failed or no-op). Core unchanged.")
    else:
        # Dry-run: simulate the corrected core and lint it, write nothing.
        if approved:
            core_data = {k: dict(v) for k, v in
                         {core.keys[z]: {"zh": z, "en": core.zh_to_ens[z],
                                         "description": core.descriptions[z],
                                         "forbidden": [f for f, zz in core.forbidden.items() if zz == z],
                                         "level": core.levels[z]}
                          for z in core.mapping.keys()}.items()}
            for key, fields in approved.items():
                for f, v in fields.items():
                    core_data[key][f] = ([v] if f == "en" and isinstance(v, str) else v)
            lint_ok = core.lint(list(core_data.values()))
            log_info(f"  Dry-run lint on corrected core: {'PASS' if lint_ok else 'FAIL'}")

    _write_report(core, corrections, approved, skipped, applied, lint_ok, mode)
    log_info(f"Report: {os.path.relpath(REPORT_PATH, config.ROOT_DIR)}")
    if mode == "apply" and applied:
        log_info("NEXT: run reanchor-posts/reanchor.py --scan to assess post re-anchoring.")
    return lint_ok


def main():
    parser = argparse.ArgumentParser(description="Apply human-approved corrections to existing core terms")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--scan", action="store_true", help="Dry-run: validate + lint-simulate, write nothing (default)")
    group.add_argument("--apply", action="store_true", help="Apply approved corrections to core via LexiconManager")
    args = parser.parse_args()
    ok = run("apply" if args.apply else "scan")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
