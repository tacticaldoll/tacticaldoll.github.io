import os
import re
import sys
import json

# Add scripts root to path
scripts_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if scripts_root not in sys.path:
    sys.path.append(scripts_root)

from infra import config
from domain.post.post import HugoPost
from lexicon import Lexicon
from infra.utils import normalize_path

def annotate_terms(file_path, lexicon):
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found.")
        return False

    # Use HugoPost for robust management
    post = HugoPost(file_path)
    if not post.metadata:
        return False

    # 3. Filter body into paragraphs and insert alerts
    blocks = re.split(r'(\n\s*\n)', post.body)
    new_blocks = []
    
    # Track which alerts we've already inserted to avoid duplicates
    inserted_alerts = set()

    for block in blocks:
        if not block.strip():
            new_blocks.append(block)
            continue
        
        # CLEANUP: Remove any existing > [!IMPORTANT] blocks to prevent accumulation
        block = re.sub(r'\n*>\s*\[!IMPORTANT\].*?(\n(?!\s*>)|$)', '\n', block, flags=re.DOTALL)
        
        # Check for anchors in this specific block
        block_anchors = re.findall(r'<!--\s*anchor:(.*?)\s*-->', block)
        # Clean the block by removing the anchors
        cleaned_block = re.sub(r'<!--\s*anchor:.*?\s*-->', '', block).strip()
        
        if cleaned_block:
            new_blocks.append(cleaned_block)
        
        if block_anchors:
            for term_zh in block_anchors:
                term_zh = term_zh.strip()
                result = lexicon.lookup(term_zh)
                if result and term_zh not in inserted_alerts:
                    # ONLY ANNOTATE LEVEL 1 TERMS
                    if result.get('level', 1) == 1:
                        en_list = result.get('en', [])
                        en_name = f" ({en_list[0]})" if en_list else ""
                        desc = result.get('description', '')
                        
                        alert = f"\n\n> [!IMPORTANT]\n> **{term_zh}**{en_name}: {desc}"
                        new_blocks.append(alert)
                        inserted_alerts.add(term_zh)

    # 4. Update body and fix whitespace
    post.body = "".join(new_blocks)
    # Remove redundant triple newlines
    post.body = re.sub(r'\n{3,}', '\n\n', post.body)
    
    # 5. Save using standardized layout
    return post.save()

def main():
    term_path = config.TERMINOLOGY_JSON
    if not os.path.exists(term_path):
        print(f"Error: {term_path} not found.")
        sys.exit(1)
        
    # Initialize Lexicon
    lexicon = Lexicon(term_path)
    
    if len(sys.argv) < 2:
        print("Usage: python3 annotate_terms.py <file_path>")
        sys.exit(1)
        
    target = sys.argv[1]
    annotate_terms(target, lexicon)

if __name__ == "__main__":
    main()
