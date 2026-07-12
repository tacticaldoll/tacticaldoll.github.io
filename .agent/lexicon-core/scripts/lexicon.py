import os
import re
import json
import sys

def load_json(path):
    """Safely loads a JSON file with utf-8 encoding."""
    if not os.path.exists(path):
        return None
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"ERROR: Failed to load JSON from {path}: {e}", file=sys.stderr)
        return None

# Base path relative to this script
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_DB_DIR = os.path.join(BASE_DIR, "databases")

class Lexicon:
    """
    [INTERFACE-DRIVEN] Data-centric domain object for technical terminology.
    SSOT: databases/terminology.json (PROTECTED - DO NOT EDIT DIRECTLY).
    
    GOVERNANCE RULE:
    - Agents MUST NOT edit terminology.json directly.
    - Agents MUST use LexiconManager for modifications.
    - Scripts MUST use Lexicon for read-only anchoring and validation.
    """
    
    def __init__(self, json_path=None):
        self.json_path = json_path or os.path.join(DEFAULT_DB_DIR, "terminology.json")
        self.mapping = {}      # ZH -> primary EN
        self.mapping_lower = {} # lowercase ZH -> primary ZH
        self.en_to_zh = {}     # lowercase EN -> correct ZH
        self.en_exact_to_zh = {} # exact EN -> correct ZH (Disambiguation)
        self.zh_to_ens = {}    # ZH -> list of (cased) ENs
        self.forbidden = {}    # Forbidden -> correct ZH
        self.levels = {}       # ZH -> level (1-3)
        self.descriptions = {} # ZH -> desc
        self.keys = {}         # ZH -> CamelCase key
        self.items = []        # Raw items list
        
        # Build-time regex patterns
        self.terms_regex = None
        self.forbidden_regex = None
        
        # Load Global Rules & Taxonomy for validation
        self.rules = load_json(os.path.join(DEFAULT_DB_DIR, "rules.json")) or {}
        self.taxonomy = load_json(os.path.join(DEFAULT_DB_DIR, "taxonomy.json")) or {}
        
        # Load Standard Database
        if os.path.exists(self.json_path):
            self.load(self.json_path)

        # Load Draft Database (Append mode)
        draft_path = os.path.join(DEFAULT_DB_DIR, "terminology.draft.json")
        if os.path.exists(draft_path):
            self.load(draft_path, append=True)

    def load(self, json_path, append=False):
        """Loads terminology from JSON and builds indices/regex."""
        if not os.path.exists(json_path):
            return
        
        data = load_json(json_path)
        if not data: return
        
        # Convert dictionary to items list to maintain backward compatibility
        items_list = []
        if isinstance(data, dict):
            for key, item in data.items():
                item["key"] = key
                items_list.append(item)
        elif isinstance(data, list):
            items_list = data
            
        if append:
            self.items.extend(items_list)
        else:
            self.items = items_list
            self.mapping = {}
            self.mapping_lower = {}
            self.en_to_zh = {}
            self.en_exact_to_zh = {}
            self.zh_to_ens = {}
            self.forbidden = {}
            self.levels = {}
            self.descriptions = {}
            self.keys = {}
        
        def make_camel_case_key(en_str, zh_str):
            if not en_str or en_str == "Unknown":
                key = re.sub(r'[^a-zA-Z0-9]', '', zh_str)
                if not key: raise ValueError(f"Cannot generate key for '{zh_str}'. English translation missing.")
                return key
            words = re.findall(r'[a-zA-Z0-9]+', en_str)
            if not words:
                key = re.sub(r'[^a-zA-Z0-9]', '', zh_str)
                if not key: raise ValueError(f"Cannot generate key for '{zh_str}'. English translation missing.")
                return key
            return "".join(w.capitalize() for w in words)

        for item in items_list:
            zh = item['zh']
            en_list = item['en']
            level = item.get('level', 1)
            self.mapping[zh] = en_list[0]
            self.mapping_lower[zh.lower()] = zh
            self.levels[zh] = level
            self.zh_to_ens[zh] = en_list
            self.descriptions[zh] = item.get('description', '')
            self.keys[zh] = item.get('key') or make_camel_case_key(en_list[0], zh)
            for e in en_list:
                self.en_to_zh[e.lower()] = zh
                self.en_exact_to_zh[e] = zh
            for f_term in item.get('forbidden', []):
                self.forbidden[f_term] = zh

        self._rebuild_regex()

    def lint(self, data=None):
        """Lints terminology for self-contradictions, banned terms, and placeholder descriptions."""
        target_data = data if data is not None else self.items
        forbidden_map = {}
        for item in target_data:
            for forbid in item.get('forbidden', []):
                if forbid not in forbidden_map: forbidden_map[forbid] = []
                forbidden_map[forbid].append(item['zh'])
                
        errors = []
        banned_words = set(forbidden_map.keys())
        placeholder_patterns = ["TODO", "待完善", "PENDING_REFINEMENT", "PENDING_NLP_DIGESTION", "自動萃取術語待校正"]
        # zh-TW maintenance defence line (GUIDE §3.1): mainland-usage words that have an
        # unambiguous Traditional-Chinese equivalent. Physicalised as data in rules.json so
        # the rule is auditable and survives outside this code. Context-dependent words
        # (程序/文檔/對象) are deliberately NOT enforced here — see rules.zh_tw_context_review.
        zh_tw_bad = self.rules.get("zh_tw_forbidden_usage", {})

        for item in target_data:
            zh, desc = item['zh'], item.get('description', '')
            for banned in banned_words:
                if (banned in zh or banned in desc) and banned != zh:
                    errors.append(f"Term '{zh}' uses forbidden word '{banned}' (owned by {forbidden_map[banned]})")
            if zh in forbidden_map:
                errors.append(f"Term '{zh}' is listed as its own forbidden term!")

            # Check for placeholders
            if not desc or any(p in desc for p in placeholder_patterns):
                errors.append(f"Term '{zh}' has missing or placeholder description.")

            # zh-TW usage defence line
            for bad, good in zh_tw_bad.items():
                if bad in zh or bad in desc:
                    errors.append(f"Term '{zh}' uses non-zh-TW word '{bad}' (use '{good}')")

        if errors:
            print("ERROR: Terminology Linting Failed!", file=sys.stderr)
            for err in set(errors): print(f"  - {err}", file=sys.stderr)
            return False
        return True

    def _rebuild_regex(self, scoped_zh=None):
        """Rebuilds internal regex patterns for standard and forbidden terms."""
        # Standard Terms
        target_keys = scoped_zh if scoped_zh is not None else self.mapping.keys()
        
        # Build discovery list: ZH keys + all unique EN aliases
        patterns = []
        for zh in target_keys:
            if zh in self.mapping:
                patterns.append(re.escape(zh))
                # Add English aliases if level < 3 (Primary technical terms)
                if self.levels.get(zh, 1) < 3:
                    for en in self.zh_to_ens.get(zh, []):
                        # Ensure EN alias is long enough or unique (preventing noise)
                        if len(en) > 3 or en.lower() == "react":
                            # Word-boundary the ASCII alias so it never matches INSIDE a
                            # larger English word (e.g. "Spec" must not fire inside
                            # "OpenSpec"/"Specialists"/"specs/"). Substring matching here
                            # was the root cause of systematic prose corruption. CJK zh
                            # above stay boundary-free (\b is meaningless between CJK).
                            patterns.append(r'\b' + re.escape(en) + r'\b')
        
        patterns.sort(key=len, reverse=True)
        
        if patterns:
            # Match: (**)? (pattern) (**)? 
            # We use a non-capturing group for the patterns to keep match group indexing stable
            self.terms_regex = re.compile(r'(\*\*)?(' + '|'.join(patterns) + r')(\*\*)?')
        else:
            self.terms_regex = None
            
        # Forbidden Terms
        if self.forbidden:
            sorted_f = sorted(self.forbidden.keys(), key=len, reverse=True)
            self.forbidden_regex = re.compile('|'.join([re.escape(str(f)) for f in sorted_f]))

    def scoped_copy(self, handoff_data):
        """Returns a copy of the lexicon limited to specific terms for a post."""
        if not handoff_data:
            return self
            
        import copy
        new_lexicon = copy.copy(self)
        # Isolate mutable dictionary states to prevent cross-session contamination
        new_lexicon.mapping = copy.copy(self.mapping)
        new_lexicon.mapping_lower = copy.copy(self.mapping_lower)
        new_lexicon.zh_to_ens = copy.copy(self.zh_to_ens)
        new_lexicon.en_to_zh = copy.copy(self.en_to_zh)
        new_lexicon.en_exact_to_zh = copy.copy(self.en_exact_to_zh)
        new_lexicon.descriptions = copy.copy(self.descriptions)
        new_lexicon.keys = copy.copy(self.keys)
        new_lexicon.levels = copy.copy(self.levels)
        
        term_objects = handoff_data.get("terms", {}).get("locked", [])
        
        scoped_zh = []
        for t in term_objects:
            if isinstance(t, dict) and "zh" in t:
                zh = t["zh"]
                if zh not in new_lexicon.mapping:
                    # Temporary injection for un-released but locked terms
                    en_list = t.get("en", ["Unknown"])
                    if isinstance(en_list, str): en_list = [en_list]
                    new_lexicon.mapping[zh] = en_list[0]
                    new_lexicon.mapping_lower[zh.lower()] = zh
                    new_lexicon.zh_to_ens[zh] = en_list
                    for e in en_list:
                        new_lexicon.en_to_zh[e.lower()] = zh
                        new_lexicon.en_exact_to_zh[e] = zh
                    new_lexicon.descriptions[zh] = t.get("description", "")
                    # Generate CamelCase key for scoped copies
                    key = t.get("key") or "".join(w.capitalize() for w in re.findall(r'[a-zA-Z0-9]+', en_list[0]))
                    if not key: raise ValueError(f"Cannot generate key for '{zh}'. English translation missing.")
                    new_lexicon.keys[zh] = key
                scoped_zh.append(zh)
                new_lexicon.levels[zh] = t.get("level", 1)
            elif isinstance(t, str) and t in new_lexicon.mapping:
                scoped_zh.append(t)

        new_lexicon._rebuild_regex(scoped_zh=scoped_zh)
        return new_lexicon

    def lookup(self, term):
        """Standard lookup interface for ZH or EN terms."""
        # 0. Normalize for lookup
        term_norm = term.strip()
        term_lower = term_norm.lower()

        # 1. Direct Chinese Match (Case-insensitive)
        # 1. Direct Chinese Match (Case-insensitive)
        if term_lower in self.mapping_lower:
            primary_zh = self.mapping_lower[term_lower]
            return {
                "zh": primary_zh,
                "en": self.zh_to_ens.get(primary_zh, []),
                "description": self.descriptions.get(primary_zh, ""),
                "forbidden": [f for f, z in self.forbidden.items() if z == primary_zh],
                "level": self.levels.get(primary_zh, 1),
                "key": self.keys.get(primary_zh),
                "status": "standard"
            }
        
        # 2. Forbidden Match
        if term in self.forbidden:
            correct_zh = self.forbidden[term]
            return {
                "zh": correct_zh,
                "input": term,
                "status": "forbidden",
                "correction": correct_zh,
                "details": self.lookup(correct_zh) if correct_zh in self.mapping else None
            }
            
        # 3. Exact English Match (Disambiguation)
        if term in self.en_exact_to_zh:
            return self.lookup(self.en_exact_to_zh[term])

        # 4. Fallback English Match (Case-insensitive)
        if term_lower in self.en_to_zh:
            return self.lookup(self.en_to_zh[term_lower])
        return None

    def get_correction(self, term):
        """Directly returns the corrected term if forbidden, else the original."""
        return self.forbidden.get(term, term)

    def validate_tags(self, tags):
        """Semantic validation of tags against lexicon and taxonomy."""
        issues = []
        genre_zh = set(self.taxonomy.get("genres", {}).values())
        ai_hierarchy = set(self.taxonomy.get("ai_taxonomy", {}).get("categories", []))

        for i, tag in enumerate(tags):
            if i < 2: continue # Skip first two (Genre/Level) usually
            
            tag_str = tag[0] if isinstance(tag, (tuple, list)) else tag
            if tag_str in genre_zh or tag_str in ai_hierarchy: continue

            # Remove parentheses if present for validation
            clean_tag = re.sub(r'\s*[(（].*?[)）]', '', tag_str).strip()
            res = self.lookup(clean_tag)
            
            if res and res["status"] == "standard":
                level = res.get("level", 1)
                # [RELAXED] We no longer strictly enforce ZH (EN) format in tags
                # This supports the Hybrid Unilingual (ZH Genre / EN Tech) model.
                pass
            
            if self.forbidden_regex and any(f in tag_str for f in self.forbidden.keys()):
                for f, z in self.forbidden.items():
                    if f in tag_str:
                        issues.append(f"Tag '{tag_str}' contains forbidden term '{f}'. Use '{z}'")
        return issues

    def get_minimal_context(self, filter_zh=None):
        """
        [MINIMAL INJECTION] Returns a minimal string representation for Agent context.
        Only contains ZH and basic EN mapping. No descriptions or levels to save tokens.
        """
        items = []
        target_keys = filter_zh if filter_zh is not None else self.mapping.keys()
        for zh in sorted(target_keys):
            if zh in self.mapping:
                items.append(f"{zh}: {self.mapping[zh]}")
        return "\n".join(items) if items else "No terms in context."
