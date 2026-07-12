import os
import sys
import json
import argparse
import glob

# Add scripts root to path
scripts_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if scripts_root not in sys.path:
    sys.path.append(scripts_root)

from infra import config
from infra.taxonomy import TaxonomyEngine
from infra.utils import log_info, log_error

class DomainClassifier:
    def __init__(self):
        self.tax_engine = TaxonomyEngine()

    def classify_session(self, session_id):
        """Re-classifies all posts in a session handoff file."""
        session_dir = config.get_session_dir(session_id)
        handoff_path = os.path.join(session_dir, "handoff.posts.json")
        
        if not os.path.exists(handoff_path):
            log_error(f"Handoff file not found: {handoff_path}")
            return False
            
        with open(handoff_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        log_info(f"Re-classifying AI domains for session {session_id}...")
        
        posts = data.get("metadata", {}).get("posts", [])
        updated_count = 0
        
        for post in posts:
            report_rel = post.get("report_rel")
            if not report_rel:
                continue
                
            report_path = os.path.join(session_dir, report_rel)
            if not os.path.exists(report_path):
                log_error(f"Report not found: {report_path}")
                continue
                
            with open(report_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            old_tag = post.get("domain_tag")
            new_tag = self.tax_engine.classify_domain(content)
            
            if old_tag != new_tag:
                post["domain_tag"] = new_tag
                log_info(f"  - [{post['slug']}] Updated: {old_tag} -> {new_tag}")
                updated_count += 1
            else:
                log_info(f"  - [{post['slug']}] Confirmed: {new_tag}")

        if updated_count > 0:
            with open(handoff_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            log_info(f"Successfully updated {updated_count} posts in {handoff_path}.")
        else:
            log_info("No domain tag updates needed.")
            
        return True

def main():
    parser = argparse.ArgumentParser(description="Pipelined AI domain classification for posts.")
    parser.add_argument("session_id", help="Session ID to re-classify")
    
    args = parser.parse_args()
    
    classifier = DomainClassifier()
    classifier.classify_session(args.session_id)

if __name__ == "__main__":
    main()
