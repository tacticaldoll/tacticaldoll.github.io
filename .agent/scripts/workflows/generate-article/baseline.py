## Authored by Schema: .agent/schemas/handoff.posts.schema.yaml
## Reference Workflow: .agent/workflows/publish-article.md
## Role: Pipeline Worker (Exclusive Consumption of inputs delegated from pipeline.py)

import sys
import os
import re
from datetime import datetime

# Add scripts root to path
scripts_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if scripts_root not in sys.path:
    sys.path.append(scripts_root)

from infra.utils import get_python_executable, normalize_path, load_json
from infra import config
from domain.post.post import HugoPost
from domain.terminology.engine import TerminologyEngine
import json



def main():
    import argparse
    parser = argparse.ArgumentParser(description="Baseline Generator")
    parser.add_argument("src_file", help="Source report markdown file")
    parser.add_argument("tgt_dir", help="Target post directory")
    parser.add_argument("--meta", help="Post metadata as JSON string")
    
    args = parser.parse_args()

    src_file = args.src_file
    tgt_dir = args.tgt_dir
    
    if not os.path.exists(src_file):
        print(f"Error: Source file {src_file} not found.")
        sys.exit(1)

    if not os.path.exists(tgt_dir):
        os.makedirs(tgt_dir)

    with open(src_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Load Metadata SSOT from arguments
    if not args.meta:
        print("Error: --meta <json_string_or_file_path> is required. Handoff consumption is now centralized in the pipeline.")
        sys.exit(1)
        
    try:
        if os.path.exists(args.meta):
            with open(args.meta, 'r', encoding='utf-8') as f:
                post_meta = json.load(f)
        else:
            post_meta = json.loads(args.meta)
    except Exception as e:
        print(f"Error: Failed to parse --meta JSON or file: {e}")
        sys.exit(1)

    # Find the current post slug from tgt_dir if not explicitly in meta
    slug_match = re.search(r'--(.*?)$', os.path.basename(tgt_dir))
    slug = slug_match.group(1) if slug_match else "unknown"
    
    # 2. Use HugoPost factory for structure initialization
    # This automatically retains pure body text without frontmatter
    post = HugoPost.from_source(content, post_meta)

    target_file = os.path.join(tgt_dir, "index.md")
    # This automatically handles directory creation and +++ formatting
    post.save(target_file)

    print(f"SUCCESS: Baseline generated at {target_file}")
    
    # G2: Run safeguard check and capture returncode ??failures were silently ignored before.
    print("\nRunning initial Safeguard Audit...")
    python_exe = get_python_executable()
    safeguard_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "workflows", "calibrate-guidelines", "safeguard.py")
    import subprocess
    audit_result = subprocess.run([python_exe, safeguard_path, src_file, target_file])
    if audit_result.returncode != 0:
        print(f"WARNING: Initial Safeguard Audit flagged issues (exit code {audit_result.returncode}). Review before running pipeline.py.")
        sys.exit(1)

if __name__ == "__main__":
    main()
