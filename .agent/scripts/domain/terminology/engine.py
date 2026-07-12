## Authored by Schema: .agent/schemas/terminology.schema.yaml
## Reference Workflow: .agent/workflows/publish-article.md

import re
import os
import json
import sys

# Add scripts root to path
scripts_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if scripts_root not in sys.path:
    sys.path.append(scripts_root)

from infra import config
from domain.post.post import HugoPost
from lexicon import Lexicon
from infra.utils import normalize_path

class TerminologyEngine:
    """
    Back-compat wrapper for the decoupled Lexicon and HugoPost processor.
    """
    def __init__(self, json_path=None):
        self.lexicon = Lexicon(json_path)

    def scope_to_terms(self, term_objects):
        self.lexicon = self.lexicon.scoped_copy({"terms": {"locked": term_objects}})
        return True

    def enable_handoff_mode(self, handoff_path):
        if not os.path.exists(handoff_path):
            return False
        with open(handoff_path, 'r', encoding='utf-8') as f:
            handoff = json.load(f)
        self.lexicon = self.lexicon.scoped_copy(handoff)
        return True

    def replace_forbidden(self, text):
        if not self.lexicon.forbidden_regex:
            return text
        return self.lexicon.forbidden_regex.sub(lambda m: self.lexicon.forbidden[m.group(0)], text)

    def process_content(self, content, mode="anchor_first"):
        post = HugoPost()
        post.load(content=content)
        from domain.terminology.injector import TerminologyInjector
        TerminologyInjector().apply_lexicon(post, self.lexicon, mode=mode)
        return post.save_to_string()

    def remove_all_anchors(self, content):
        post = HugoPost()
        post.load(content=content)
        post.remove_all_anchors(self.lexicon)
        return post.save_to_string()

    def lookup(self, term):
        return self.lexicon.lookup(term)

    def validate_tags(self, tags):
        return self.lexicon.validate_tags(tags)

    def get_all_forbidden(self):
        return self.lexicon.forbidden

# CLI interface extracted to engine_cli.py (SRP: engine.py is a domain service, not a CLI tool)
