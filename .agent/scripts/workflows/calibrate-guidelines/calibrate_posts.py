## Authored by Schema: none (utility)
## Reference Workflow: .agent/workflows/calibrate-guidelines.md

import os
import re
import json

def calibrate_post(file_path, found_terms):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find the boundary of front matter to avoid messing it up
    lines = content.splitlines()
    body_start_idx = 0
    if lines and lines[0].strip() == '+++':
        try:
            end_idx = lines.index('+++', 1)
            body_start_idx = sum(len(l) + 1 for l in lines[:end_idx+1])
        except ValueError:
            pass
    
    front_matter = content[:body_start_idx]
    body = content[body_start_idx:]
    
    new_body = body
    for item in found_terms:
        if not item["is_anchored"]:
            term = item["term"]
            en = item["expected_en"]
            key_val = item.get("key_val") or term
            # Replace ONLY the first occurrence in the body
            # Check if it's already bolded
            pattern_bold = r'\*\*' + re.escape(term) + r'\*\*'
            replacement = f"**{term}**（{en}） <!-- term:{key_val} -->"
            
            if re.search(pattern_bold, new_body):
                new_body = re.sub(pattern_bold, replacement, new_body, count=1)
            else:
                pattern_normal = re.escape(term)
                new_body = re.sub(pattern_normal, replacement, new_body, count=1)
            print(f"  Fixed: {term} -> {replacement}")

    if new_body != body:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(front_matter + new_body)
        return True
    return False

def main():
    if os.path.exists('audit_results.json'):
        with open('audit_results.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
    else:
        print("Error: audit_results.json not found. Run audit_lexicon.py first.")
        return
    
    posts_dir = os.path.join(os.getcwd(), "content", "posts")
    
    for rel_path, results in data.items():
        full_path = os.path.join(posts_dir, rel_path)
        print(f"Processing {rel_path}...")
        if calibrate_post(full_path, results["found_terms"]):
            print(f"  Updated {rel_path}")

    # Clean up audit_results.json after consumption
    try:
        os.remove('audit_results.json')
        print("\nINFO: Cleaned up temporary audit_results.json")
    except Exception as e:
        pass

if __name__ == "__main__":
    main()

