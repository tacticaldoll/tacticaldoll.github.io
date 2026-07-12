## Authored by Schema: .agent/schemas/handoff.terms.schema.yaml, .agent/schemas/handoff.posts.schema.yaml
## Reference Spec: .agent/reference/agent-operating-guideline.md
"""Stage 0.5 Handoff refiner.

Promotes high-confidence scanned terms into locked terms, records refinement
telemetry, and halts on missing or placeholder descriptions. This module marks
where NLP completion is required; it must not fabricate semantic descriptions
or mutate the global terminology database directly.
"""

import os
import sys
import json
import re
import argparse

# Add scripts root to path
scripts_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if scripts_root not in sys.path:
    sys.path.append(scripts_root)

from domain.terminology.engine import TerminologyEngine
from infra import config
from infra.utils import log_info, log_error, format_model_id


from infra.telemetry import detect_agent_telemetry, has_version, UNKNOWN_AGENT


class TerminologyRefiner:
    def __init__(self, session_id):
        self.session_id = session_id
        self.scratch_dir = config.get_session_dir(session_id)
        self.terms_handoff_path = os.path.join(self.scratch_dir, "handoff.terms.json")
        self.engine = TerminologyEngine()
        
    def load_terms(self):
        if not os.path.exists(self.terms_handoff_path):
            log_error(f"Terms handoff not found: {self.terms_handoff_path}")
            return None
        with open(self.terms_handoff_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def is_obvious_junk(self, term):
        """Second-pass strict filtering for pseudo-terms and sentence fragments."""
        zh = term.get("zh", "")
        
        # 1. Ends with common non-noun particles/verbs (indicates a fragment)
        # 1. Ends with common non-noun particles/verbs (indicates a fragment)
        if re.search(r'[的|了|在|和|是|有|与|为]$', zh):
            return True
            
        # 2. Starts with numerical counts (e.g., 第一部分, 5个 - specific findings are not terms
        if re.match(r'^([0-9一二三四五六七八九十]|第[一二三四五六七八九十]+)', zh):
            return True

        # 3. Starts with common verbs or transition words used in descriptions
        if re.match(r'^(使用|評估)', zh):
            return True

        # 4. Contains common verb-object structures or junk indicators
        junk_indicators = []
        if any(indicator in zh for indicator in junk_indicators):
            return True
            
        # 5. Too long for a technical term (Standard terms are rarely > 10 chars)
        if len(zh) > 10:
            return True
            
        return False

    def refine_telemetry(self, model_id, agent_name, dry_run=False):
        """Refines and explicitly records the active environment telemetry inside handoff.posts.json."""
        # 1. Model is NLP-Sourced (AI self-declaration)
        formatted_model = format_model_id(model_id) if model_id else "Unknown"
        
        # 2. Agent: explicit self-declaration is authoritative; detection is a
        #    vendor-neutral fallback (UNKNOWN_AGENT when no platform is recognised).
        detected = detect_agent_telemetry()
        if not agent_name:
            formatted_agent = detected
        else:
            formatted_agent = format_model_id(agent_name)
            # Enrich only when the declaration lacks a version AND detection found
            # the SAME platform carrying one. Vendor-neutral: keyed off the
            # declared name's first token, not any hardcoded vendor.
            if (not has_version(formatted_agent)
                    and detected != UNKNOWN_AGENT
                    and formatted_agent.split()[0].lower() in detected.lower()):
                formatted_agent = detected
        # A versionless agent is honest but incomplete; surface it for the gate.
        if formatted_agent != UNKNOWN_AGENT and not has_version(formatted_agent):
            log_info(f"  [TELEMETRY] Agent '{formatted_agent}' has no version number "
                     f"(spec asks for IDE + version). Pass --agent with a version to complete it.")
            
        posts_path = os.path.join(self.scratch_dir, "handoff.posts.json")
        if not os.path.exists(posts_path):
            fallback = os.path.join(config.ROOT_DIR, "handoff.posts.json")
            if os.path.exists(fallback):
                posts_path = fallback
            else:
                log_error(f"Posts handoff not found for telemetry writing: {posts_path}")
                return
                
        try:
            with open(posts_path, 'r', encoding='utf-8') as f:
                posts_data = json.load(f)
        except Exception as e:
            log_error(f"Failed to read posts handoff: {e}")
            return
            
        if "metadata" not in posts_data:
            posts_data["metadata"] = {}
        if "posts" not in posts_data["metadata"]:
            posts_data["metadata"]["posts"] = []
            
        log_info(f"Refining active Telemetry -> Model: '{formatted_model}', Agent: '{formatted_agent}'")
        
        modified = False
        for post in posts_data["metadata"]["posts"]:
            if "ai_info" not in post:
                post["ai_info"] = {}
            if "refinement" not in post["ai_info"]:
                post["ai_info"]["refinement"] = {}
                
            current_model = post["ai_info"]["refinement"].get("model")
            if model_id or not current_model or current_model == "Unknown":
                post["ai_info"]["refinement"]["model"] = formatted_model

            current_agent = post["ai_info"]["refinement"].get("agent")
            if agent_name or not current_agent or current_agent == "Unknown":
                post["ai_info"]["refinement"]["agent"] = formatted_agent
                
            modified = True
        
        posts_data["status"] = "refined"
        modified = True
                
        if modified and not dry_run:
            try:
                with open(posts_path, 'w', encoding='utf-8') as f:
                    json.dump(posts_data, f, indent=4, ensure_ascii=False)
                log_info(f"Successfully recorded refinement telemetry inside handoff.posts.json.")
            except Exception as e:
                log_error(f"Failed to save posts handoff: {e}")

    def refine(self, dry_run=False):
        data = self.load_terms()
        if not data: return False
        
        terms = data.get("terms", {})
        discovered = terms.get("discovered", [])
        locked = terms.get("locked", [])
        
        log_info(f"Refining terms for session {self.session_id}...")
        
        new_locked = []
        purged_count = 0
        promoted_count = 0
        
        # 1. Load originally declared terms for NLP Declaration Immunity bypass
        declared_terms = terms.get("declared", [])
        immune_zh = set()
        for t in declared_terms:
            if isinstance(t, dict) and "zh" in t:
                immune_zh.add(t["zh"])
            elif isinstance(t, str):
                immune_zh.add(t)
        
        # Keep track of existing ZH in locked to avoid duplicates
        locked_zh = {t["zh"] for t in locked}
        
        remaining_discovered = []
        
        # Process Discovered Terms
        for d in discovered:
            # Bypass junk filter if term has NLP declaration immunity
            if d["zh"] in immune_zh:
                pass
            elif self.is_obvious_junk(d):
                log_info(f"  - [PURGE] '{d['zh']}' (Identified as fragment/junk from discovered)")
                purged_count += 1
                continue
            
            # Check if it should be auto-promoted (Bilingual & High Confidence)
            if d.get("confidence") == "high" and d.get("type") in ["bilingual", "tag"]:
                if d["zh"] not in locked_zh:
                    # Sync with global DB if it exists there
                    res = self.engine.lookup(d["zh"])
                    
                    # Defend against KeyError: 'en' for discovered tag-types
                    en_val = d.get("en")
                    if isinstance(en_val, list) and en_val:
                        en_primary = en_val[0]
                    elif isinstance(en_val, str):
                        en_primary = en_val
                    else:
                        en_primary = ""  # Fallback to empty; ZH string is semantically incorrect for EN field
                    
                    locked_item = {
                        "zh": d["zh"],
                        "en": en_primary,
                        "level": 2,
                        "session_id": self.session_id
                    }
                    
                    if res and res["status"] != "forbidden":
                        locked_item["description"] = res.get("description", "")
                        locked_item["level"] = res.get("level", 1)
                        log_info(f"  - [SYNC] '{d['zh']}' (Matched global database)")
                    else:
                        locked_item["description"] = "PENDING_REFINEMENT"
                        log_info(f"  - [LOCK] '{d['zh']}' (Awaiting AI/Manual refinement)")
                    
                    new_locked.append(locked_item)
                    locked_zh.add(d["zh"])
                    promoted_count += 1
                continue
                
            remaining_discovered.append(d)

        # Self-Clean Locked Terms (Remove pseudo-terms that were manually/previously locked)
        final_locked = []
        for l in locked + new_locked:
            # Bypass junk filter if term has NLP declaration immunity
            if l["zh"] in immune_zh:
                if not any(fl["zh"] == l["zh"] for fl in final_locked):
                    final_locked.append(l)
                continue
                
            if self.is_obvious_junk(l):
                log_info(f"  - [PURGE] '{l['zh']}' (Identified as fragment/junk from locked)")
                purged_count += 1
                continue
            # Deduplicate
            if not any(fl["zh"] == l["zh"] for fl in final_locked):
                final_locked.append(l)

        if not dry_run:
            terms["discovered"] = remaining_discovered
            terms["locked"] = final_locked
            with open(self.terms_handoff_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            log_info(f"Refinement complete: {promoted_count} promoted, {purged_count} purged.")
        else:
            log_info(f"Dry run complete: Would promote {promoted_count}, purge {purged_count}.")

        # G0: Term-starvation gate. A real publish batch almost never has zero
        # anchorable terms; an empty locked list usually means the source reports
        # used neither `中文(EN)` / **bold** markup nor a curated series-map, so the
        # scanner found nothing. Flag it so the human declares core terms instead
        # of silently shipping with new flagship terms missing from the lexicon.
        if not final_locked:
            log_info("=" * 54)
            log_info("  [WARNING] 0 locked terms for this handoff.")
            log_info("  The scanner only catches `中文(EN)` / **bold** markup and")
            log_info("  series-map/guide Metadata tags. If the reports use none of")
            log_info("  these, declare core terms in handoff.terms.json 'declared'")
            log_info("  (zh / en / description) before running pipeline.py.")
            log_info("=" * 54)

        # G1: Actionable summary of PENDING_REFINEMENT items requiring manual description
        pending = [l for l in final_locked if l.get("description") == "PENDING_REFINEMENT"]
        if pending:
            log_info("=" * 54)
            log_info(f"  [WARNING] {len(pending)} PENDING terms need description")
            for p in pending:
                log_info(f"     - {p['zh']} (EN: {p.get('en', 'N/A')})")
            log_info("  Please add description before running pipeline.py")
            log_info("=" * 54)

        return True

def main():
    parser = argparse.ArgumentParser(description="Stage 1.5: Terminology Refinement & Junk Purge")
    parser.add_argument("session_id", help="Session ID to refine")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without writing")
    parser.add_argument("--model", help="Active AI Model Selection ID running the refinement")
    parser.add_argument("--agent", help="Active AI Agent Platform running the refinement")
    
    args = parser.parse_args()
    
    refiner = TerminologyRefiner(args.session_id)
    if not refiner.refine(dry_run=args.dry_run):
        log_error("Refinement failed. Skipping telemetry write to prevent inconsistent state.")
        return
    refiner.refine_telemetry(args.model, args.agent, dry_run=args.dry_run)

if __name__ == "__main__":
    main()
