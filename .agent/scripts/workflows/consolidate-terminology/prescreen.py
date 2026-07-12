## Authored by Schema: .agent/schemas/terminology.schema.yaml
## Reference Workflow: .agent/workflows/consolidate-terminology.md
## Role: READ-ONLY semantic-prescreen evidence collector. Sits at stage ①.5,
## between the deterministic scan (consolidate.py --scan, stage ①) and the
## mandatory human review gate (stage ②). It writes NOTHING to the lexicon or
## to content/. For every targeted term it assembles two evidence lines an LLM
## reviewer needs to triage semantic correctness:
##   (a) intra-entry coherence smells  (zh fragment, en acronym casing, stray
##       ascii in description, mainland-usage words, desc not referencing zh)
##   (b) real post usage               (literal zh hits + `term:Key`/`anchor:Key`
##       anchor counts + trimmed excerpts pulled from content/posts/)
##
## DESIGN INVARIANT (GUIDE DeterministicTrustBoundary): this script only collects
## deterministic evidence. The semantic VERDICT is produced by the LLM reviewer
## reading prescreen-evidence.json, and remains ADVISORY — the human gate in
## consolidate-terminology stage ② is NOT removed or auto-consumed by --apply.

import os
import re
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
from manager import log_info

EVIDENCE_JSON = os.path.join(config.SCRATCH_DIR, "prescreen-evidence.json")
EVIDENCE_MD = os.path.join(config.SCRATCH_DIR, "prescreen-evidence.md")

# Acronyms that title-casing from the CamelCase key mangles (Ai -> "AI", Bdd -> "BDD").
_ACRONYMS = {
    "Ai": "AI", "Api": "API", "Bdd": "BDD", "Ci": "CI", "Cli": "CLI", "Crud": "CRUD",
    "Ddd": "DDD", "Gof": "GoF", "Ide": "IDE", "Json": "JSON", "Llm": "LLM", "Rfc": "RFC",
    "Sop": "SOP", "Ui": "UI", "Yaml": "YAML",
}
# Grammatical particles a noun-phrase term must never start with (clause fragment).
_ZH_LEADERS = "的與和及之了或而"
# Mainland-usage words with an unambiguous zh-TW form, BEYOND the hard list already
# enforced by Lexicon.lint() via rules.json. Advisory only — surfaced for the human.
_ADVISORY_ZH_TW = {
    "概率": "機率", "元數據": "後設資料", "異步": "非同步", "優化": "最佳化",
    "跟蹤": "追蹤", "語義": "語意", "聲明": "宣告", "編程": "程式設計",
    "正規": "範式(疑)", "優先級": "優先序", "信號": "訊號",
}


def _post_files():
    for root, _dirs, files in os.walk(config.POSTS_DIR):
        if "index.md" in files:
            yield os.path.basename(root), os.path.join(root, "index.md")


def _load_corpus():
    """Returns [(slug, body_text)] — body only, front matter stripped."""
    corpus = []
    for slug, path in _post_files():
        with open(path, encoding="utf-8") as f:
            content = f.read()
        parts = content.split("+++", 2)
        corpus.append((slug, parts[2] if len(parts) >= 3 else content))
    return corpus


def _excerpt(body, needle, width=42):
    i = body.find(needle)
    if i < 0:
        return None
    a, b = max(0, i - width), min(len(body), i + len(needle) + width)
    snip = body[a:b].replace("\n", " ").strip()
    return f"…{snip}…"


def coherence_smells(item):
    """Deterministic intra-entry smells. Returns list of {code, detail}."""
    zh = item.get("zh", "")
    desc = item.get("description", "")
    ens = item.get("en", [])
    out = []
    if zh and zh[0] in _ZH_LEADERS:
        out.append({"code": "zh_fragment", "detail": f"zh 以助詞「{zh[0]}」開頭，疑似切割碎片"})
    for en in ens:
        for tok in re.findall(r"[A-Za-z]+", en):
            if tok in _ACRONYMS:
                out.append({"code": "en_acronym_case",
                            "detail": f"en「{en}」縮寫大小寫疑慮，應為「{_ACRONYMS[tok]}」"})
                break
    if re.search(r"(?<![A-Za-z])(the|a|an|of|is|to)(?![A-Za-z])", desc):
        out.append({"code": "desc_stray_ascii", "detail": "description 夾雜孤立英文虛詞，疑似殘字"})
    for bad, good in _ADVISORY_ZH_TW.items():
        if bad in zh or bad in desc:
            out.append({"code": "zh_tw_usage", "detail": f"含陸用語「{bad}」→建議「{good}」"})
    return out


def gather(targets, corpus):
    rows = []
    for key, item in targets:
        zh = item.get("zh", "")
        usage = {"zh_hits": 0, "term_anchors": 0, "anchor_defs": 0, "excerpts": []}
        term_pat = re.compile(r"<!--\s*term:%s\s*-->" % re.escape(key))
        anchor_pat = re.compile(r"<!--\s*anchor:%s\s*-->" % re.escape(key))
        for slug, body in corpus:
            if zh and zh in body:
                usage["zh_hits"] += 1
                if len(usage["excerpts"]) < 3:
                    ex = _excerpt(body, zh)
                    if ex:
                        usage["excerpts"].append({"post": slug, "text": ex})
            usage["term_anchors"] += len(term_pat.findall(body))
            usage["anchor_defs"] += len(anchor_pat.findall(body))
        rows.append({
            "key": key,
            "zh": zh,
            "en": item.get("en", []),
            "level": item.get("level"),
            "description": item.get("description", ""),
            "smells": coherence_smells(item),
            "usage": usage,
        })
    return rows


def _resolve_targets(core, keys_arg, smelly_only):
    by_key = {core.keys.get(zh, zh): {"zh": zh, "en": core.zh_to_ens.get(zh, []),
              "level": core.levels.get(zh), "description": core.descriptions.get(zh, "")}
              for zh in core.mapping.keys()}
    if keys_arg:
        wanted = [k.strip() for k in keys_arg.split(",") if k.strip()]
        missing = [k for k in wanted if k not in by_key]
        if missing:
            log_info(f"  [warn] keys not found in core: {missing}")
        return [(k, by_key[k]) for k in wanted if k in by_key]
    targets = list(by_key.items())
    if smelly_only:
        targets = [(k, it) for k, it in targets if coherence_smells(it)]
    return targets


def write_evidence(rows):
    with open(EVIDENCE_JSON, "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2, ensure_ascii=False)

    md = [
        "# 術語語意預審證據 (AI Pre-screen Evidence)",
        "",
        "> 由 `prescreen.py` 唯讀產出，供 **AI 顧問性預審**使用。",
        "> 本檔僅含確定性證據；語意裁決由 LLM 閱讀後產出，且**仍為 advisory**——",
        "> 人工複審閘門（consolidate 階段二）不被取代、不被 `--apply` 自動消費。",
        "",
        f"目標術語數：**{len(rows)}**　|　語料：{len(list(_post_files()))} 篇貼文",
        "",
    ]
    for r in rows:
        u = r["usage"]
        md.append(f"## `{r['key']}` — 「{r['zh']}」 (L{r['level']}) / {'/'.join(r['en'])}")
        md.append(f"- 描述：{r['description']}")
        if r["smells"]:
            md.append("- **自洽 smells**：")
            for s in r["smells"]:
                md.append(f"  - `{s['code']}` — {s['detail']}")
        else:
            md.append("- 自洽 smells：（無）")
        md.append(f"- 貼文用法：zh 命中 {u['zh_hits']} 篇 | term 錨點 {u['term_anchors']} | 定義框 {u['anchor_defs']}")
        for ex in u["excerpts"]:
            md.append(f"  - `{ex['post']}`：{ex['text']}")
        md.append("")
    with open(EVIDENCE_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(md))


def main():
    parser = argparse.ArgumentParser(
        description="Read-only semantic pre-screen evidence collector (stage ①.5)")
    parser.add_argument("--keys", help="Comma-separated core keys to target (default: all core)")
    parser.add_argument("--smelly-only", action="store_true",
                        help="When scanning all core, emit only entries with ≥1 deterministic smell")
    args = parser.parse_args()

    core = Lexicon(config.TERMINOLOGY_JSON)
    targets = _resolve_targets(core, args.keys, args.smelly_only)
    if not targets:
        log_info("No target terms resolved. Nothing to collect.")
        return 0
    corpus = _load_corpus()
    rows = gather(targets, corpus)
    write_evidence(rows)
    smelly = sum(1 for r in rows if r["smells"])
    log_info(f"Collected evidence for {len(rows)} term(s); {smelly} carry deterministic smells.")
    log_info(f"  JSON: {os.path.relpath(EVIDENCE_JSON, config.ROOT_DIR)}")
    log_info(f"  MD:   {os.path.relpath(EVIDENCE_MD, config.ROOT_DIR)}")
    log_info("Hand the evidence to the LLM reviewer; verdicts stay advisory, human gate unchanged.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
