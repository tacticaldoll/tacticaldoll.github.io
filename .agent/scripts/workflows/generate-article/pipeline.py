## Authored by Schema: .agent/schemas/handoff.posts.schema.yaml, .agent/schemas/handoff.terms.schema.yaml
## Reference Spec: .agent/reference/agent-operating-guideline.md
"""Publish pipeline consumer.

Consumes refined Handoff JSON as the publishing SSOT, generates Hugo posts,
anchors locked terminology, runs safety audits, and replenishes/promotes
terminology through the managed lexicon flow. This module does not perform NLP
extraction or revise handoff intent after the human-reviewed freeze point.
"""

import os
import sys
import subprocess
import json
import re
import argparse

from datetime import datetime

# Add scripts root to path
scripts_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if scripts_root not in sys.path:
    sys.path.append(scripts_root)

from infra import config
from infra.utils import log_info, log_error, format_model_id

from domain.post.post import HugoPost
from domain.post.assembler import PostAssembler
from domain.post.orchestrator import PostOrchestrator
from lexicon import Lexicon
from manager import LexiconManager

class ProductionPipeline:
    def __init__(self, session_id):
        self.session_id = session_id
        self.scratch_dir = config.get_session_dir(session_id)
        self.posts_handoff_path = os.path.join(self.scratch_dir, "handoff.posts.json")
        self.terms_handoff_path = os.path.join(self.scratch_dir, "handoff.terms.json")
        self.python_exe = sys.executable

    def load_handoff(self, load_terms=True):
        # Load posts metadata (primary)
        load_path = self.posts_handoff_path
        
        if not os.path.exists(load_path):
            log_error(f"Handoff (Posts) not found for session {self.session_id}. Please run /init-handoff first.")
            sys.exit(1)
            
        with open(load_path, 'r', encoding='utf-8') as f:
            handoff = json.load(f)
            
        # Optionally merge terms if they are in a separate file
        if load_terms and os.path.exists(self.terms_handoff_path):
            try:
                with open(self.terms_handoff_path, 'r', encoding='utf-8') as f:
                    terms_data = json.load(f)
                    handoff["terms"] = terms_data.get("terms", {})
            except Exception as e:
                log_error(f"Failed to merge terms from {self.terms_handoff_path}: {e}")
                sys.exit(1)
                
        return handoff

    def run_command(self, cmd_args):
        log_info(f"Executing: {' '.join(cmd_args)}")
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        result = subprocess.run(cmd_args, capture_output=True, text=True, env=env, encoding='utf-8', errors='replace')
        if result.returncode != 0:
            log_error(f"Command failed: {result.stderr}")
            return False
        else:
            lines = result.stdout.splitlines()
            for line in lines[-2:]:
                 print(f"    {line}")
            return True

    def run_baseline(self):
        handoff = self.load_handoff()
        # load_handoff() calls sys.exit(1) if missing; no None check needed.
        
        is_series = handoff["metadata"]["is_series"]
        
        for idx, post in enumerate(handoff["metadata"]["posts"], 1):
            report_file = os.path.join(self.scratch_dir, post["report_rel"])
            seq_part = f"-{idx:02d}" if is_series else ""
            post_dir = os.path.join(config.POSTS_DIR, f"gen-{self.session_id}{seq_part}--{post['slug']}")
            
            log_info(f">>> Baseline Generator: {post['slug']}")
            # Centralized SSOT: Pass individual post metadata to baseline script via a temp file to avoid Windows command argument encoding issues
            meta_temp_path = os.path.join(self.scratch_dir, f"meta_temp_{post['slug']}.json")
            with open(meta_temp_path, 'w', encoding='utf-8') as f:
                json.dump(post, f, indent=4, ensure_ascii=False)
            
            success = self.run_command([self.python_exe, ".agent/scripts/workflows/generate-article/baseline.py", report_file, post_dir, "--meta", meta_temp_path])
            
            # Clean up temp file
            if os.path.exists(meta_temp_path):
                os.remove(meta_temp_path)
                
            if not success:
                return False
        
        return True

    def run_finish(self):
        handoff = self.load_handoff(load_terms=True)
        # load_handoff() calls sys.exit(1) if missing; no None check needed.

        # Check status state machine
        status = handoff.get("status", "initiated")
        if status != "refined":
            log_error(f"State Machine Violation: Session status is '{status}', but must be 'refined' to run Stage 2 pipeline.")
            log_error("Please run refine_handoff.py first to refine terminology and transition state.")
            return False

        log_info(f"--- Pipeline Mode: Finish/NLP Atomic ({self.session_id}) ---")
        
        # [GATE] Strict Integrity Check: Ensure all locked terms and metadata are refined
        locked_terms = handoff.get("terms", {}).get("locked", [])
        invalid_elements = []
        
        # 1. Check Terms
        forbidden_patterns = ["TODO", "待完善", "PENDING_NLP_DIGESTION", "PENDING_REFINEMENT", "期待您的進一步指示"]
        for l in locked_terms:
            if any(p in l.get("description", "") for p in forbidden_patterns):
                invalid_elements.append(f"術語: {l['zh']} (描述包含未解析之 AI 預設字串)")
        
        # 2. Check for unhandled discovered terms (Warning only, or strict if required)
        discovered_high = [d for d in handoff.get("terms", {}).get("discovered", []) if d.get("confidence") == "high"]
        if discovered_high:
            unhandled = [d["zh"] for d in discovered_high if not any(l["zh"] == d["zh"] for l in locked_terms)]
            if unhandled:
                log_info(f"  [QUALITY INFO] Unhandled discovered terms: {', '.join(unhandled)}")
                log_info("  (These terms will not be injected.)")

        # 3. Check Posts Metadata
        for p in handoff.get("metadata", {}).get("posts", []):
            if any(p_str in p.get("description", "") for p_str in forbidden_patterns):
                invalid_elements.append(f"Invalid Description (Post: {p['slug']})")
            tag_forbidden = ["TODO", "待完善", "PENDING_REFINEMENT"]
            if any(any(p_str in tag for p_str in tag_forbidden) for tag in p.get("tags", [])):
                invalid_elements.append(f"Invalid Tags (Post: {p['slug']})")
        
        if invalid_elements:
            log_error("Validation failed. Please resolve:")
            log_error("  - " + "\n  - ".join(invalid_elements))
            return False


        lexicon = Lexicon(config.TERMINOLOGY_JSON)
        
        # If we have a scoped handoff, use it to speed up regex and focus anchoring
        if os.path.exists(self.terms_handoff_path):
            try:
                with open(self.terms_handoff_path, 'r', encoding='utf-8') as f:
                    terms_data = json.load(f)
                    lexicon = lexicon.scoped_copy(terms_data)
                    log_info("  (Using Scoped Lexicon for Anchoring)")
            except Exception as e:
                log_error(f"Failed to scope lexicon: {e}")

        is_series = handoff["metadata"]["is_series"]
        all_success = True

        for idx, post_meta in enumerate(handoff["metadata"]["posts"], 1):
            if post_meta.get("status") == "verified":
                log_info(f"  [SKIP] Post {post_meta['slug']} already verified and saved in a previous run.")
                continue
                
            seq_part = f"-{idx:02d}" if is_series else ""
            post_dir = os.path.join(config.POSTS_DIR, f"gen-{self.session_id}{seq_part}--{post_meta['slug']}")
            target_post_path = os.path.join(post_dir, "index.md")
            source_report_path = os.path.join(self.scratch_dir, post_meta["report_rel"])
            
            if not os.path.exists(target_post_path):
                log_error(f"Target post not found at {target_post_path}. Baseline may have failed — aborting.")
                return False

            log_info(f">>> Finishing: {post_meta['slug']}")
            
            # 1. Load through Domain Entity (Pure Markdown Body)
            post = HugoPost(target_post_path)
            
            # 1.5. Inject TOML Frontmatter Metadata
            post = (PostAssembler(post)
                    .with_base_meta(post_meta, handoff.get("metadata"))
                    .with_author(os.path.join(config.ROOT_DIR, "hugo.toml"))
                    .with_tags(post_meta, lexicon)
                    .with_telemetry(post_meta)
                    .build())
            
            # CAUSAL: The post object handles its own transformation based on rules defined in handoff
            rules = post_meta.get("rules", {})
            
            # Convert elevation_targets (string array) into sublimations (pattern -> replacement dict)
            elevation_targets = rules.get("elevation_targets", [])
            if elevation_targets:
                if "sublimations" not in rules:
                    rules["sublimations"] = {}
                for target in elevation_targets:
                    if target and target not in rules["sublimations"]:
                        rules["sublimations"][re.escape(target)] = ""
            
            PostOrchestrator.cleanup(post, lexicon, rules=rules)
            
            # 3. Final Safeguard Audit
            # ROBUST: Audit is an internal verification step
            with open(source_report_path, 'r', encoding='utf-8') as f:
                src_raw = f.read()
            
            report = post.audit(lexicon_engine=lexicon, source_raw=src_raw, source_path=source_report_path)
            
            # 4. Report Results & Save
            print(f"    Audit Results: {'PASS' if report.passed else 'FAILED'}")
            for issue in report.issues:
                print(f"      {issue}")
            
            if not report.passed:
                log_error(f"  Safeguard Audit failed for {post_meta['slug']} — aborting session.")
                post_meta["status"] = "failed"
                # Save checkpoint before aborting
                try:
                    with open(self.posts_handoff_path, 'w', encoding='utf-8') as f:
                        json.dump(handoff, f, indent=4, ensure_ascii=False)
                except Exception as e:
                    log_error(f"Failed to save handoff checkpoint: {e}")
                return False
            else:
                post.save()
                post_meta["status"] = "verified"
                log_info(f"  Successfully finished {post_meta['slug']}")
                
            # Save checkpoint progress back to posts handoff immediately
            try:
                with open(self.posts_handoff_path, 'w', encoding='utf-8') as f:
                    json.dump(handoff, f, indent=4, ensure_ascii=False)
            except Exception as e:
                log_error(f"Failed to save handoff checkpoint: {e}")

        if all_success:
            log_info(f"SUCCESS: Pipeline finished for {self.session_id}.")
            log_info("Retiring Handoff...")
            self.retire_handoff_and_replenish(handoff)
            
            for hf in [self.posts_handoff_path, self.terms_handoff_path]:
                if os.path.exists(hf):
                    os.remove(hf)
            
            return True
        else:
            log_error(f"FAILURE: Some steps failed for {self.session_id}. Handoff retained for retry.")
            return False

    def retire_handoff_and_replenish(self, handoff):
        """Releases locally invented/locked terms to the Global DB before Handoff retirement.
        
        Processes both `locked` and `declared` (with refined descriptions) terms.
        `declared` terms are AI-authored at Stage 0 and may never enter `locked` if they
        were not discovered by prepare_handoff -- this ensures they still reach the global DB.
        """
        # If terms_handoff is already deleted, we assume replenishment was handled manually or via sync
        if not os.path.exists(self.terms_handoff_path) and "terms" not in handoff:
            log_info("  Terms handoff already retired/synced. Skipping replenishment.")
            return True
            
        lexicon = Lexicon()
        manager = LexiconManager(lexicon)
        
        placeholder_patterns = ["TODO", "待完善", "PENDING_REFINEMENT", "PENDING_NLP_DIGESTION"]
        
        def is_placeholder(desc):
            return any(p in desc for p in placeholder_patterns)
        
        new_replenishments = []
        added_zh = set()
        
        def try_add(term_item, source_label):
            zh = term_item.get("zh", "")
            if not zh or zh in added_zh:
                return
            res = lexicon.lookup(zh)
            if not res:
                desc = term_item.get("description", "")
                if is_placeholder(desc):
                    log_info(f"  - [SKIP] Term '{zh}' skipped due to placeholder description ({source_label})")
                    return
                item = dict(term_item)
                item["session_id"] = self.session_id
                new_replenishments.append(item)
                added_zh.add(zh)
        
        # 1. Process locked terms (primary source)
        locked_terms = handoff.get("terms", {}).get("locked", [])
        for l in locked_terms:
            try_add(l, "locked")
        
        # 2. Process declared terms with refined descriptions
        # Declared terms are AI-authored at Stage 0 and may not have been promoted to locked.
        declared_terms = handoff.get("terms", {}).get("declared", [])
        for d in declared_terms:
            if not isinstance(d, dict):
                continue
            desc = d.get("description", "")
            # Only replenish if description is present and non-placeholder
            if desc and not is_placeholder(desc):
                try_add(d, "declared")
                
        if not new_replenishments:
            return True
            
        log_info(f"Handoff Retirement: Replenished {len(new_replenishments)} new terms to global draft.")
        manager.replenish(new_replenishments)
        
        return True

    def run_ultimate(self):
        """[ULTIMATE TURBO] Single-pass execution from Handoff to save.
        Orchestrates: Baseline -> Finish.
        Terminology lifecycle steps (scanning, refinement) are expected to be completed in Stage 0 (/init-handoff).
        """
        log_info(f"=== ULTIMATE TURBO PIPELINE: {self.session_id} ===")
        
        # 1. Baseline Generation
        if self.run_baseline() is False:
            log_error("Failed at Baseline stage.")
            return False
            
        # 2. Automated Finish (Sublimation + Anchoring + Audit)
        if self.run_finish() is False:
            log_error("Failed at Finish/Refinement stage.")
            return False
            
        return True


def main():
    parser = argparse.ArgumentParser(description="Integrated Production Pipeline (Ultimate Turbo)")
    parser.add_argument("session_id", help="Session ID to process")
    parser.add_argument("--mode", choices=["baseline", "finish", "ultimate"], default="ultimate", help="Processing mode (default: ultimate)")
    
    args = parser.parse_args()
    
    pipeline = ProductionPipeline(args.session_id)
    if args.mode == "baseline":
        if not pipeline.run_baseline(): sys.exit(1)
    elif args.mode == "finish":
        if not pipeline.run_finish(): sys.exit(1)
    else:
        if not pipeline.run_ultimate(): sys.exit(1)

if __name__ == "__main__":
    main()
