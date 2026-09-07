## Authored by Schema: none (infrastructure)
## Reference Workflow: Shared Infrastructure

import os
import json
import re
from infra import config
from infra.utils import strip_report_provenance

class TaxonomyEngine:
    """
    Standalone engine for technical taxonomy classification and validation.
    Follows hierarchical (deep-to-shallow) matching for AI domains.
    """
    def __init__(self, taxonomy_path=None):
        self.taxonomy_path = taxonomy_path or config.TAXONOMY_JSON
        self.data = self._load()
        
    def _load(self):
        if not os.path.exists(self.taxonomy_path):
            import sys
            print(f"[WARNING] TaxonomyEngine: taxonomy file not found at {self.taxonomy_path}. Domain classification will return None.", file=sys.stderr)
            return {}
        try:
            with open(self.taxonomy_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            import sys
            print(f"[WARNING] TaxonomyEngine: failed to load taxonomy: {e}. Domain classification will return None.", file=sys.stderr)
            return {}

    def classify_domain(self, content):
        """
        Classifies the AI domain of a given text content.
        Uses hierarchical matching defined in taxonomy.json.

        Provenance is stripped here rather than by each caller. A report header's
        `**Agent**: Codex VS Code extension ...` contains the substring 'agent',
        a detection keyword for the AI 代理人 domain, and it is identical across
        every report in a session — so classifying raw report text let generation
        metadata pick the domain for all of them. Guarding that at the call sites
        meant every present and future caller had to remember; doing it here makes
        passing raw text harmless instead of policing it.

        Stripping already-clean prose is a no-op, which is what makes handing raw
        text here harmless. It is a no-op because the strip removes those lines only
        when a provenance header block is actually present: a leading H1 is otherwise
        the document's own title and a bold pair is otherwise prose, and both carry
        keywords — the title of a report on boundary governance contains 治理, which
        decides a domain. `audit_kb.py` probes both shapes.
        """
        return self.classify_domain_evidence(content)["domain"]

    # Flags on an evidenced classification. Not verdicts — the answer is already
    # correct — but reasons a human might want to look.
    CONTESTED = "CONTESTED"
    WEAK_WINNER = "WEAK_WINNER"
    SINGLE_HIT = "SINGLE_HIT"

    def classify_domain_evidence(self, content):
        """Returns classify_domain's answer together with the evidence behind it.

        Categories are priority-ordered and the first hit wins. That is deliberate:
        a specific reading should beat a broad one even on a single keyword, which
        is why AI 經濟與社會 precedes AI 代理人. The cost is that the decision is
        silent — a post can hit four categories, or win on one late keyword against
        a rival's four early ones, and nothing says so.

        This reports that without changing it. classify_domain delegates here, so
        the evidence and the answer cannot drift apart.

        Flags: CONTESTED (more than one category hit), WEAK_WINNER (the winner has
        fewer hits than some loser), SINGLE_HIT (the winner rests on one keyword).
        """
        content = strip_report_provenance(content)
        ai_tax = self.data.get("ai_taxonomy", {})
        # No hardcoded fallback: taxonomy.json is the category SSOT, and a copy here
        # would be a second definition free to drift from it — this default listed
        # three categories long after the file held five. With no categories there
        # are no keywords either, so classification correctly yields None.
        categories = ai_tax.get("categories", [])
        detection = ai_tax.get("detection_keywords", {})

        content_lower = content.lower()

        hits = {}
        for category in categories:
            found = []
            for kw in detection.get(category, []):
                pos = content_lower.find(kw.lower())
                if pos >= 0:
                    found.append({"keyword": kw, "position": pos})
            if found:
                found.sort(key=lambda h: h["position"])
                hits[category] = found

        # Priority 1: specifically defined categories in order (Deep -> Shallow).
        # Asymmetric Tagging: None when nothing matched. Do not force an "AI"
        # fallback, which protects pure technical posts (e.g. Linux).
        winner = next((c for c in categories if c in hits), None)

        flags = []
        if winner is not None:
            if len(hits) > 1:
                flags.append(self.CONTESTED)
                strongest_rival = max(len(v) for c, v in hits.items() if c != winner)
                if len(hits[winner]) < strongest_rival:
                    flags.append(self.WEAK_WINNER)
            if len(hits[winner]) == 1:
                flags.append(self.SINGLE_HIT)

        return {"domain": winner, "hits": hits, "flags": flags}

    def save(self):
        """Persists the in-memory taxonomy back to taxonomy.json (utf-8, indent 2)."""
        with open(self.taxonomy_path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)

    def rename_genre_value(self, old_zh, new_zh):
        """Sanctioned in-place edit of a genre's Chinese display value.

        A genre's zh value is shared by every key variant (the spaced 'Analytical Essay'
        and the slug 'analytical-essay' both map to it), so all variants are updated
        together to keep the mapping consistent. Persists immediately. Returns the number
        of key variants updated (0 if the value was not present).
        """
        genres = self.data.get("genres", {})
        hits = [k for k, v in genres.items() if v == old_zh]
        if not hits:
            print(f"[WARN] rename_genre_value: no genre with value '{old_zh}'.")
            return 0
        for k in hits:
            genres[k] = new_zh
        self.save()
        print(f"[OK] Renamed genre '{old_zh}' -> '{new_zh}' across {len(hits)} key(s): {hits}")
        return len(hits)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Taxonomy management / classification test")
    parser.add_argument("--rename-genre", nargs=2, metavar=("OLD_ZH", "NEW_ZH"),
                        help="Rename a genre's zh display value across all key variants")
    args = parser.parse_args()
    engine = TaxonomyEngine()
    if args.rename_genre:
        engine.rename_genre_value(args.rename_genre[0], args.rename_genre[1])
    else:
        test_content = "This post discusses AI Agent and ReAct workflows."
        print(f"Detected: {engine.classify_domain(test_content)}")
