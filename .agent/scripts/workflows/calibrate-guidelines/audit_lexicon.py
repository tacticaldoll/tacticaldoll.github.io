import os
import re
import json
import sys

# Add script path to sys.path to import domain and infra
scripts_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if scripts_root not in sys.path:
    sys.path.append(scripts_root)

from infra import config
from lexicon import Lexicon, load_json

def check_database_health():
    """
    Checks if there are unpromoted drafts or redundant files (like archive placeholders).
    Returns a list of issues found.
    """
    issues = []
    
    # 1. Check for unpromoted drafts
    if os.path.exists(config.TERMINOLOGY_DRAFT_JSON):
        draft_content = load_json(config.TERMINOLOGY_DRAFT_JSON)
        if draft_content and len(draft_content) > 0:
            issues.append(f"CRITICAL: Found {len(draft_content)} unpromoted terms in {os.path.basename(config.TERMINOLOGY_DRAFT_JSON)}. Run 'manage.py --promote' before submission.")

    # 2. Check for redundant archive placeholder
    if os.path.exists(config.TERMINOLOGY_ARCHIVE_JSON):
        archive_content = load_json(config.TERMINOLOGY_ARCHIVE_JSON)
        if not archive_content or len(archive_content) == 0:
            issues.append(f"WARNING: Redundant empty file found: {os.path.basename(config.TERMINOLOGY_ARCHIVE_JSON)}. This file should be removed for project purity.")
            
    return issues

def scan_post(file_path, lexicon):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Strip front matter for scanning
    parts = content.split('+++', 2)
    body_text = parts[2] if len(parts) >= 3 else content

    results = {
        "found_terms": [], # (term, anchored_correctly, found_text)
        "possible_candidates": [] 
    }
    
    # Use lexicon to find all occurrences of known ZH terms
    for zh, en_primary in lexicon.mapping.items():
        pattern = re.escape(zh)
        matches = list(re.finditer(pattern, body_text))
        if matches:
            # Check if FIRST occurrence is anchored
            first_match = matches[0]
            suffix = body_text[first_match.end():first_match.end()+100]
            key_val = lexicon.keys.get(zh, zh)
            
            # Match either: Optional (English) followed by <!-- term:Key -->
            anchor_match = re.search(r'^(?:\s*[\(（].*?[\)）])?\s*<!--\s*term:(' + re.escape(key_val) + r')\s*-->', suffix)
            
            is_anchored = False
            found_anchor = None
            if anchor_match:
                is_anchored = True
                found_anchor = anchor_match.group(1).strip()
            
            results["found_terms"].append({
                "term": zh,
                "expected_en": en_primary,
                "is_anchored": is_anchored,
                "found_anchor": found_anchor,
                "key_val": key_val,
                "count": len(matches)
            })

    # Heuristic for candidates: 4+ characters ZH strings that look technical
    words = re.findall(r'[\u4e00-\u9fff]{4,}', body_text)
    for word in words:
        if word not in lexicon.mapping and word not in ["以及", "因此", "但是", "不過", "我們", "目前", "可以", "這是一個"]:
            results["possible_candidates"].append(word)

    return results

def main():
    print("--- Terminology Database Health ---")
    health_issues = check_database_health()
    if not health_issues:
        print("OK: Database is clean and ready for submission.")
    else:
        for issue in health_issues:
            print(issue)
    print("\n--- Post Content Terminology Scan ---")

    lexicon = Lexicon(config.TERMINOLOGY_JSON)
    posts_dir = config.POSTS_DIR
    all_results = {}
    
    for root, dirs, files in os.walk(posts_dir):
        if "index.md" in files:
            post_path = os.path.join(root, "index.md")
            rel_path = os.path.relpath(post_path, posts_dir)
            all_results[rel_path] = scan_post(post_path, lexicon)
            
    with open("audit_results.json", "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    print("Audit results written to audit_results.json")

if __name__ == "__main__":
    main()
