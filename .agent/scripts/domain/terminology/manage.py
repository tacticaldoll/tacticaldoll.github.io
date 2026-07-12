import os
import sys
import argparse

# Add scripts root to path
scripts_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if scripts_root not in sys.path:
    sys.path.append(scripts_root)

# Correct path for lexicon-core scripts (relative to manage.py)
# manage.py is in .agent/scripts/domain/terminology/
base_path = os.path.dirname(os.path.abspath(__file__))
lexicon_core_scripts = os.path.abspath(os.path.join(base_path, "../../../lexicon-core/scripts"))
if lexicon_core_scripts not in sys.path:
    sys.path.append(lexicon_core_scripts)

from manager import LexiconManager

def main():
    parser = argparse.ArgumentParser(description="Terminology Management Utility")
    parser.add_argument("--promote", action="store_true", help="Promote all drafts to Core")
    parser.add_argument("--add", help="Add single term: 'zh,en,description'")
    parser.add_argument("--level", type=int, default=1, help="Level for the new term (default: 1)")
    
    args = parser.parse_args()
    
    mgr = LexiconManager()
    
    if args.promote:
        mgr.promote_all_drafts()
        
    elif args.add:
        parts = args.add.split(',', 2)
        if len(parts) < 3:
            print("Error: --add requires 'zh,en,description'")
            sys.exit(1)
        zh, en, desc = parts
        mgr.add_term(zh.strip(), en.strip(), desc.strip(), level=args.level)
        
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
