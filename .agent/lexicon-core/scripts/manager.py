import os
import json
import sys
import re
from datetime import datetime
from lexicon import Lexicon, load_json

def log_info(message):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] INFO: {message}")

def log_error(message):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] ERROR: {message}", file=sys.stderr)

# Base path relative to this script
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_DB_DIR = os.path.join(BASE_DIR, "databases")

def make_camel_case_key(en_str, zh_str):
    """Generates a clean, alphanumeric CamelCase key from standard English term, falling back to Chinese if needed."""
    if not en_str or en_str == "Unknown":
        key = re.sub(r'[^a-zA-Z0-9]', '', zh_str)
        if not key: raise ValueError(f"Cannot generate key for '{zh_str}'. English translation missing.")
        return key
    # Clean and CamelCase the English string
    words = re.findall(r'[a-zA-Z0-9]+', en_str)
    if not words:
        key = re.sub(r'[^a-zA-Z0-9]', '', zh_str)
        if not key: raise ValueError(f"Cannot generate key for '{zh_str}'. English translation missing.")
        return key
    return "".join(w.capitalize() for w in words)

class LexiconManager:
    """
    Administrative interface for technical terminology.
    Handles replenishment, promotion, and archiving under the CamelCase Key-Value Object schema.
    """
    
    def __init__(self, lexicon=None):
        self.lexicon = lexicon or Lexicon()
        self.core_path = os.path.join(DEFAULT_DB_DIR, "terminology.json")
        self.draft_path = os.path.join(DEFAULT_DB_DIR, "terminology.draft.json")
        self.archive_path = os.path.join(DEFAULT_DB_DIR, "terminology.archive.json")

    def _migrate_to_dict(self, data):
        """Converts a legacy list database structure to the new CamelCase key-value structure."""
        if isinstance(data, dict):
            return data
        temp = {}
        if isinstance(data, list):
            for item in data:
                en_primary = item.get("en", ["Unknown"])[0]
                key = make_camel_case_key(en_primary, item["zh"])
                temp[key] = item
        return temp

    def replenish(self, new_terms):
        """
        Safely appends new terms to the 'draft' tier using CamelCase keys.
        This prevents unvetted terms from entering the Core SSOT.
        """
        if not new_terms: return
        
        draft_raw = load_json(self.draft_path) or {}
        draft_data = self._migrate_to_dict(draft_raw)
        
        added_count = 0
        for item in new_terms:
            zh = item["zh"]
            # Check if it already exists in Core or Draft
            if self.lexicon.lookup(zh):
                continue
            if any(d["zh"] == zh for d in draft_data.values()):
                continue
                
            en_list = item.get("en", ["Unknown"])
            if isinstance(en_list, str): en_list = [en_list]
            
            key = make_camel_case_key(en_list[0], zh)
            
            entry = {
                "zh": zh,
                "en": en_list,
                "description": item.get("description", "TODO: 需人工精煉描述"),
                "forbidden": item.get("forbidden", []),
                "level": item.get("level", 1),
                "source_session": item.get("session_id", "Unknown")
            }
            draft_data[key] = entry
            added_count += 1
            log_info(f"  + Drafted: {zh} ({en_list[0]}) as Key '{key}'")
            
        if added_count > 0:
            with open(self.draft_path, 'w', encoding='utf-8') as f:
                json.dump(draft_data, f, indent=2, ensure_ascii=False)
            log_info(f"SUCCESS: Added {added_count} terms to draft.")
        return added_count

    def promote_all_drafts(self):
        """Promotes all terms from draft to core, maintaining CamelCase key-value structure."""
        draft_raw = load_json(self.draft_path) or {}
        draft_data = self._migrate_to_dict(draft_raw)
        if not draft_data:
            log_info("No drafts to promote.")
            return 0
            
        core_raw = load_json(self.core_path) or {}
        core_data = self._migrate_to_dict(core_raw)
        
        promoted = 0
        for key, item in draft_data.items():
             item.pop("source_session", None)
             core_data[key] = item
             promoted += 1
             
        if promoted > 0:
            # Rebuild dictionary sorted by length of ZH descending for better regex performance later
            sorted_items = sorted(core_data.items(), key=lambda x: len(x[1]['zh']), reverse=True)
            core_data = dict(sorted_items)
            
            # QUALITY GATE: Ensure no placeholders or contradictions enter the SSOT
            if not self.lexicon.lint(list(core_data.values())):
                log_error("Promotion aborted: Safety Linting Failed on the new Core SSOT data.")
                return 0
            
            with open(self.core_path, 'w', encoding='utf-8') as f:
                json.dump(core_data, f, indent=2, ensure_ascii=False)
                
            # Clear draft
            with open(self.draft_path, 'w', encoding='utf-8') as f:
                json.dump({}, f, indent=2)
                
            log_info(f"SUCCESS: Promoted {promoted} terms to Core SSOT.")
            self.lexicon.load(self.core_path) # Refresh lexicon
            
        return promoted

    def add_term(self, zh, en, description, level=1, forbidden=None):
        """Quickly adds a single term to the core database as a CamelCase key (bypassing draft)."""
        core_raw = load_json(self.core_path) or {}
        core_data = self._migrate_to_dict(core_raw)
        
        # Check if exists
        if any(item["zh"] == zh for item in core_data.values()):
            log_info(f"Term '{zh}' already exists in Core.")
            return False
            
        en_list = [en] if isinstance(en, str) else en
        entry = {
            "zh": zh,
            "en": en_list,
            "description": description,
            "forbidden": forbidden or [],
            "level": level
        }
        
        key = make_camel_case_key(en_list[0], zh)
        core_data[key] = entry
        
        # Rebuild dictionary sorted by length of ZH descending
        sorted_items = sorted(core_data.items(), key=lambda x: len(x[1]['zh']), reverse=True)
        core_data = dict(sorted_items)
        
        # QUALITY GATE: Ensure no placeholders or contradictions enter the SSOT
        if not self.lexicon.lint(list(core_data.values())):
            log_error(f"Add aborted: Safety Linting Failed on new term '{zh}'.")
            return False
        
        with open(self.core_path, 'w', encoding='utf-8') as f:
            json.dump(core_data, f, indent=2, ensure_ascii=False)
            
        log_info(f"SUCCESS: Added '{zh}' to Core as Key '{key}'.")
        self.lexicon.load(self.core_path)
        return True

    # --- In-place correction of EXISTING core terms --------------------------
    # Historically LexiconManager could only add/replenish/promote — there was no
    # sanctioned path to fix the zh/description/level of a term already in the SSOT
    # without editing terminology.json by hand (which governance forbids). These
    # methods close that gap. The CamelCase key is the identity and is NOT changed
    # here; a rename is modelled as remove() + add_term().
    EDITABLE_FIELDS = {"zh", "en", "description", "level", "forbidden"}

    def _write_core(self, core_data):
        """Sorts (by zh length desc, for regex perf), persists, and reloads the lexicon."""
        sorted_items = sorted(core_data.items(), key=lambda x: len(x[1]['zh']), reverse=True)
        core_data = dict(sorted_items)
        with open(self.core_path, 'w', encoding='utf-8') as f:
            json.dump(core_data, f, indent=2, ensure_ascii=False)
        self.lexicon.load(self.core_path)
        return core_data

    def apply_corrections(self, corrections):
        """Batch-edits existing core terms by key, then lint-gates and writes ONCE (atomic).

        corrections: {key: {field: new_value, ...}} where field is in EDITABLE_FIELDS.
        Applying all edits before a single lint avoids a half-applied SSOT and lets the
        terminal Lexicon.lint() validate the whole corrected core in one pass. Unknown
        keys are reported and skipped. Returns the number of terms corrected (0 on abort).
        """
        core_data = self._migrate_to_dict(load_json(self.core_path) or {})
        applied, missing = 0, []
        for key, fields in corrections.items():
            if key not in core_data:
                missing.append(key)
                continue
            for f, v in fields.items():
                if f not in self.EDITABLE_FIELDS:
                    log_error(f"  Skipping non-editable field '{f}' on '{key}'.")
                    continue
                if f == "en" and isinstance(v, str):
                    v = [v]
                core_data[key][f] = v
            applied += 1
            log_info(f"  ~ Corrected: {key} <- {fields}")
        if missing:
            log_error(f"  {len(missing)} key(s) not found, skipped: {missing}")
        if applied == 0:
            log_info("No corrections applied.")
            return 0
        # QUALITY GATE: the whole corrected core must pass lint (placeholders,
        # forbidden-word contradictions, zh-TW usage defence line).
        if not self.lexicon.lint(list(core_data.values())):
            log_error("Corrections aborted: Safety Linting Failed on the corrected Core SSOT.")
            return 0
        self._write_core(core_data)
        log_info(f"SUCCESS: Applied {applied} correction(s) to Core.")
        return applied

    def correct_term(self, key, zh=None, en=None, description=None, level=None, forbidden=None):
        """Corrects one existing core term in place (keyed by CamelCase key). Lint-gated."""
        fields = {k: v for k, v in (
            ("zh", zh), ("en", en), ("description", description),
            ("level", level), ("forbidden", forbidden)) if v is not None}
        if not fields:
            log_info("correct_term: nothing to change.")
            return 0
        return self.apply_corrections({key: fields})

    def relevel(self, key, level):
        """Re-classifies an existing term's level (1=core, 2=secondary, 3=generic defence)."""
        return self.correct_term(key, level=level)

    def remove(self, key):
        """Removes an existing term from core, archiving it for traceability. Lint-gated."""
        core_data = self._migrate_to_dict(load_json(self.core_path) or {})
        if key not in core_data:
            log_info(f"Term key '{key}' not in Core. Nothing to remove.")
            return False
        removed = dict(core_data.pop(key))
        removed["archived_reason"] = "removed via LexiconManager.remove"
        arch = load_json(self.archive_path) or {}
        arch[key] = removed
        with open(self.archive_path, 'w', encoding='utf-8') as f:
            json.dump(arch, f, indent=2, ensure_ascii=False)
        if not self.lexicon.lint(list(core_data.values())):
            log_error(f"Remove aborted: Safety Linting Failed after removing '{key}'.")
            return False
        self._write_core(core_data)
        log_info(f"SUCCESS: Removed '{key}' from Core (archived to {os.path.basename(self.archive_path)}).")
        return True


if __name__ == "__main__":
    # Small CLI for management
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        mgr = LexiconManager()
        if cmd == "promote":
            mgr.promote_all_drafts()
        else:
            print(f"Unknown command: {cmd}")
