## Authored by Schema: none (infrastructure)
## Reference Workflow: Shared Infrastructure

import os
import json
import re
from infra import config

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
        """
        ai_tax = self.data.get("ai_taxonomy", {})
        categories = ai_tax.get("categories", ["AI 代理人 (AI Agent)", "大型語言模型 (LLM)", "AI"])
        detection = ai_tax.get("detection_keywords", {})
        
        content_lower = content.lower()
        
        # Priority 1: Check specifically defined categories in order (Deep -> Shallow)
        for category in categories:
            keywords = detection.get(category, [])
            if any(kw.lower() in content_lower for kw in keywords):
                return category
                
        # Asymmetric Tagging: Return None if no AI keywords are matched.
        # Do not force "AI" fallback, which protects pure technical posts (e.g. Linux).
        return None

    def get_genre_mapping(self):
        """Returns the mapping of slug/English names to Chinese genre names."""
        return self.data.get("genres", {})

    def resolve_genre(self, raw_genre):
        """Maps a raw genre name to its standardized Chinese counterpart."""
        genres = self.get_genre_mapping()
        return genres.get(raw_genre, raw_genre)

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
