## Authored by Schema: .agent/schemas/terminology.schema.yaml
## Reference Workflow: .agent/workflows/consolidate-terminology.md
## Role: Pure deterministic validators that complement Lexicon.lint().
##
## Lexicon.lint() already covers: placeholder descriptions, self-contradiction,
## and registered-forbidden-word usage. These validators add the three classes
## lint() does NOT catch, identified by corpus audit:
##   (1) structural fragments  (sentence pieces minted as "terms")
##   (2) near-duplicate variants (e.g. 分析論文 vs canonical 分析論述)
##   (3) over-general terms     (high document-frequency, low navigational value)

import re

# (1) Structural garbage thresholds ------------------------------------------
# CJK + ASCII sentence punctuation: a single term should contain none of these.
_STRUCTURAL_PUNCT = "，。、；：！？「」『』（）(),.;:!?…—"
# Grammatical particles a clause fragment tends to start with.
_SENTENCE_LEADERS = ("是", "而是", "不是", "並非", "也是", "就是", "卻是", "的是", "了")
# Clause markers that should never appear ANYWHERE in a noun-phrase term. The
# copula 是 is a reliable discriminator: corpus audit found every term
# containing it was a sentence fragment, with zero legitimate exceptions.
_CLAUSE_MARKERS = ("是",)
# A zh string at/over this length is almost certainly a phrase, not a term.
MAX_TERM_LEN = 12


def check_structural(zh):
    """(1) Reject sentence fragments. Returns a reason string or None."""
    if not zh or not zh.strip():
        return "空術語"
    if any(p in zh for p in _STRUCTURAL_PUNCT):
        return "含句讀標點（疑似句子片段）"
    for lead in _SENTENCE_LEADERS:
        if zh.startswith(lead):
            return f"以語助詞「{lead}」開頭（疑似句子片段）"
    for marker in _CLAUSE_MARKERS:
        if marker in zh:
            return f"含子句標記「{marker}」（疑似句子片段）"
    if len(zh) >= MAX_TERM_LEN:
        return f"長度 {len(zh)} ≥ {MAX_TERM_LEN}（疑似短語/句子，非單一術語）"
    return None


# (2) Near-duplicate variant detection ---------------------------------------
def _edit_distance(a, b):
    """Standard Levenshtein distance."""
    if a == b:
        return 0
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def check_variant(zh, existing_zh, max_dist=1):
    """(2) Flag terms that are ~1 edit away from an existing core term.

    existing_zh: iterable of canonical zh strings already in the core lexicon.
    Returns a reason string (naming the collision) or None.
    """
    if len(zh) < 3:  # short terms differ legitimately by one char (e.g. 標籤 vs 標記)
        return None
    for other in existing_zh:
        if other == zh or abs(len(other) - len(zh)) > 1:
            continue
        if _edit_distance(zh, other) <= max_dist:
            return f"與既有術語「{other}」編輯距離 ≤ {max_dist}（疑似變體，應合併或登記為 forbidden）"
    return None


# (3) Over-general term detection --------------------------------------------
def check_generic(zh, df_count, total_docs, ratio=0.25, min_docs=8):
    """(3) Flag terms appearing in too large a fraction of the corpus.

    df_count: number of posts whose body contains zh.
    Returns a reason string or None. A hit suggests demotion to level 3.
    """
    if total_docs <= 0:
        return None
    if df_count >= min_docs and (df_count / total_docs) >= ratio:
        pct = df_count / total_docs * 100
        return f"出現於 {df_count}/{total_docs} 篇（{pct:.0f}%），過度通用，建議降為 level 3"
    return None
