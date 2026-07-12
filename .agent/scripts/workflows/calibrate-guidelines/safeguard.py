## Authored by Schema: none (utility)
## Reference Workflow: .agent/workflows/calibrate-guidelines.md

import os
import sys

# Add scripts root to path
scripts_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if scripts_root not in sys.path:
    sys.path.append(scripts_root)

from infra import config
from infra.utils import normalize_path
from domain.post.post import HugoPost
from lexicon import Lexicon

def main():
    if len(sys.argv) < 3:
        print("Usage: python3 safeguard.py <source_md> <target_md>")
        sys.exit(1)

    src_path, tgt_path = normalize_path(sys.argv[1]), normalize_path(sys.argv[2])
    term_path = config.TERMINOLOGY_JSON

    if not os.path.exists(src_path) or not os.path.exists(tgt_path):
        print(f"Error: Files not found. Source: {src_path}, Target: {tgt_path}")
        sys.exit(1)

    with open(src_path, 'r', encoding='utf-8') as f:
        src_raw = f.read()

    # 1. Initialize Lexicon/Engine
    lexicon = Lexicon(term_path)
    
    # 2. Load Post as Domain Entity
    post = HugoPost(tgt_path)
    
    # 3. ROBUST AUDIT: Delegate to domain entity
    report = post.audit(lexicon_engine=lexicon, source_raw=src_raw, source_path=src_path)

    # 4. Print Report (Matching previous format)
    print(f"--- Safeguard Audit Report ---")
    print(f"Source: {src_path}")
    print(f"Target: {tgt_path}")
    
    if "source" in report.metrics and "target" in report.metrics:
        src_stats = report.metrics["source"]
        tgt_stats = report.metrics["target"]
        print(f"Metrics:   [{src_stats['headers']:>2}H, {src_stats['paragraphs']:>2}P, {src_stats['lines']:>3}L] -> [{tgt_stats['headers']:>2}H, {tgt_stats['paragraphs']:>2}P, {tgt_stats['lines']:>3}L]")
    
    for issue in report.issues:
        print(issue)

    if not report.passed:
        sys.exit(1)
    else:
        print("PASS: Physical Scale & Security Safeguards verified.")

if __name__ == "__main__":
    main()
