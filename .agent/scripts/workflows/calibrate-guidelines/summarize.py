## Authored by Schema: none (utility)
## Reference Workflow: .agent/workflows/calibrate-guidelines.md

import sys
import os
import re

# Add scripts root to path
scripts_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if scripts_root not in sys.path:
    sys.path.append(scripts_root)

from infra import config
from domain.post.post import HugoPost
from lexicon import Lexicon
from domain.terminology.injector import TerminologyInjector
from infra.utils import normalize_path

def inject_summary(file_path, lexicon=None):
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found.")
        return False

    # Use HugoPost for robust management
    post = HugoPost(file_path)
    if not post.metadata:
        return False
    
    # Initialize Lexicon if not provided
    if lexicon is None:
        lexicon = Lexicon()

    # 1. Extract the 'description' field as the summary source
    summary_text = post.metadata.get('description', '').strip()
    if not summary_text or summary_text.upper() == "TODO: ADD DESCRIPTION":
        # Fallback: Check for legacy 'summary' field
        summary_text = post.metadata.get('summary', '').strip()
        if not summary_text:
            print(f"No valid description/summary field in front matter for {file_path}, falling back to first paragraph.")
            # Fallback: Extract first paragraph from body
            body_lines = post.body.splitlines()
            for line in body_lines:
                clean_line = line.strip()
                if not clean_line: continue
                if clean_line.startswith('#'): continue
                if clean_line.startswith('<!--'): continue
                if clean_line.startswith('> [!'): continue
                summary_text = clean_line
                break

    if not summary_text:
        print(f"Warning: No suitable summary context found in {file_path}.")
        return False

    # 2. (Deprecated) Inject summary if empty - Removed per new specs
    
    # 3. Physically clean up all <!-- anchor:... --> tags and hidden artifacts
    # Use the Lexicon-aware cleanup for physical robustness
    injector = TerminologyInjector()
    injector.remove_all_anchors(post, lexicon)
    
    # We always save if changed or to ensure final purity
    if "anchor:" in post.raw_content or "term:" in post.raw_content:
        post.save()
        print(f"Successfully processed summary and cleaned anchors in {file_path}.")
        return True
    
    print(f"No changes needed for {file_path}.")
    return False

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 summarize.py <file_path>")
        sys.exit(1)
    
    target_file = sys.argv[1]
    inject_summary(target_file)

if __name__ == "__main__":
    main()
