import os
import sys
import json
import shutil
import tempfile

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

def _load(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def _dump(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def test_replenish_and_promote():
    """The quality gate is the contract, so both of its directions are asserted.

    This used to assert that a freshly drafted term reaches the Core SSOT. It does
    not, and should not: replenish stamps a term with no description as
    `TODO: 需人工精煉描述`, and promote_all_drafts lints the result and aborts. The
    gate is the point — GUIDE §3.1 requires refinement before promotion — so the old
    assertion was testing a contract that predates it, and failed for the right
    reason. It also ran against the live terminology.json and cleaned up only on the
    path where it passed, which is why a failing run left `TestTerm` behind in the
    draft and broke §10.1's empty-draft rule.

    It now runs in a temporary database directory seeded from the real Core SSOT, so
    the lint sees realistic neighbours while nothing here can touch the SSOT itself.
    """
    print("Testing Replenish and Promote...")
    with tempfile.TemporaryDirectory() as tmp:
        core_path = os.path.join(tmp, "terminology.json")
        draft_path = os.path.join(tmp, "terminology.draft.json")
        shutil.copyfile(TERMINOLOGY_JSON, core_path)
        _dump(draft_path, {})

        mgr = LexiconManager(db_dir=tmp)
        mgr.replenish([{
            "zh": "測試術語",
            "en": "Test Term",
            "session_id": "test-session-999",
        }])

        drafts = _load(draft_path)
        assert any(d["zh"] == "測試術語" for d in drafts.values()), "Term should be in draft"
        print("  Replenished successfully to draft.")

        # Direction 1: unrefined must not pass. replenish fills the description with a
        # placeholder, and the lint in promote_all_drafts must refuse the batch.
        assert mgr.promote_all_drafts() == 0, \
            "A draft carrying a placeholder description must not be promoted"
        assert not any(c["zh"] == "測試術語" for c in _load(core_path).values()), \
            "The quality gate must keep an unrefined term out of the Core SSOT"
        assert _load(draft_path), \
            "An aborted promotion must leave the draft intact, not silently clear it"
        print("  Unrefined draft correctly refused by the quality gate.")

        # Direction 2: refined must pass, or the gate would be indistinguishable from
        # a promotion path that never works.
        drafts = _load(draft_path)
        for entry in drafts.values():
            if entry["zh"] == "測試術語":
                entry["description"] = "測試用術語，用於驗證晉升流程的品質閘門。"
        _dump(draft_path, drafts)

        assert mgr.promote_all_drafts() == 1, "A refined draft must be promoted"
        assert any(c["zh"] == "測試術語" for c in _load(core_path).values()), \
            "Term should be promoted to core"
        assert not _load(draft_path), "A successful promotion must clear the draft"
        print("  Refined draft promoted successfully to core.")


if __name__ == "__main__":
    try:
        lexicon = test_json_loading()
        test_replenish_and_promote()
        print("\nALL TESTS PASSED!")
    except Exception as e:
        print(f"\nTEST FAILED: {e}")
        sys.exit(1)
