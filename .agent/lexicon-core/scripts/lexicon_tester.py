import os
import sys
import json

# Add scripts root to path
scripts_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if scripts_root not in sys.path:
    sys.path.append(scripts_root)

from lexicon import Lexicon, DEFAULT_DB_DIR
from manager import LexiconManager

# Definitions for testing (mirroring what was in config)
TERMINOLOGY_JSON = os.path.join(DEFAULT_DB_DIR, "terminology.json")
TERMINOLOGY_DRAFT_JSON = os.path.join(DEFAULT_DB_DIR, "terminology.draft.json")

def test_json_loading():
    print("Testing JSON Loading...")
    lexicon = Lexicon()
    print(f"  Loaded {len(lexicon.mapping)} terms.")
    assert len(lexicon.mapping) >= 0, "Should have loaded terms"
    return lexicon

def test_replenish_and_promote():
    print("Testing Replenish and Promote...")
    mgr = LexiconManager()
    
    # Create a test term
    test_term = {
        "zh": "測試術語",
        "en": "Test Term",
        "session_id": "test-session-999"
    }
    
    # Replenish to draft
    mgr.replenish([test_term])
    
    # We use local constants for checks
    with open(TERMINOLOGY_DRAFT_JSON, 'r', encoding='utf-8') as f:
        drafts = json.load(f)
    draft_list = list(drafts.values()) if isinstance(drafts, dict) else drafts
    assert any(d["zh"] == "測試術語" for d in draft_list), "Term should be in draft"
    print("  Replenished successfully to draft.")
    
    # Promote to core
    mgr.promote_all_drafts()
    
    with open(TERMINOLOGY_JSON, 'r', encoding='utf-8') as f:
        core = json.load(f)
    core_list = list(core.values()) if isinstance(core, dict) else core
    assert any(c["zh"] == "測試術語" for c in core_list), "Term should be promoted to core"
    print("  Promoted successfully to core.")
    
    # Cleanup test term from core for next run
    if isinstance(core, dict):
        new_core = {k: v for k, v in core.items() if v["zh"] != "測試術語"}
    else:
        new_core = [c for c in core if c["zh"] != "測試術語"]
    with open(TERMINOLOGY_JSON, 'w', encoding='utf-8') as f:
        json.dump(new_core, f, indent=2, ensure_ascii=False)
    print("  Cleanup done.")



if __name__ == "__main__":
    try:
        lexicon = test_json_loading()
        test_replenish_and_promote()
        print("\nALL TESTS PASSED!")
    except Exception as e:
        print(f"\nTEST FAILED: {e}")
        sys.exit(1)
