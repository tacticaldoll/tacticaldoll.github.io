import os
import sys

# Add scripts root to path
scripts_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if scripts_root not in sys.path:
    sys.path.append(scripts_root)

from infra import config
from lexicon import Lexicon
from domain.post.post import HugoPost
from infra.utils import normalize_path

def cleanup_post(file_path, lexicon):
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found.")
        return False

    # 1. Load through HugoPost entity
    post = HugoPost(file_path)
    if not post.metadata:
        return False
    
    # 2. CAUSAL CLEANUP: Delegate all processing to the domain entity
    from domain.post.orchestrator import PostOrchestrator
    PostOrchestrator.cleanup(post, lexicon)

    # 3. Final standardized save (handles BOM and formatting)
    return post.save()

def main():
    root_dir = os.getcwd()
    term_path = config.TERMINOLOGY_JSON
    
    # Initialize Lexicon
    lexicon = Lexicon(term_path)
    
    # Check if a specific path or file was provided as an argument
    target = normalize_path(os.path.join(root_dir, "content", "posts"))
    if len(sys.argv) > 1:
        target = normalize_path(sys.argv[1])

    if os.path.isfile(target):
        print(f"Cleaning single file: {target}...")
        if cleanup_post(target, lexicon):
            print(f"  Fixed.")
    elif os.path.isdir(target):
        print(f"Cleaning directory: {target}...")
        for root, dirs, files in os.walk(target):
            if "index.md" in files:
                post_path = os.path.join(root, "index.md")
                print(f"Cleaning {post_path}...")
                if cleanup_post(post_path, lexicon):
                    print(f"  Fixed.")
    else:
        print(f"Error: Target {target} not found.")
        sys.exit(1)

if __name__ == "__main__":
    main()
