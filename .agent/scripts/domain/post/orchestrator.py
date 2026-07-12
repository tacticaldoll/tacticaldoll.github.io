## Authored by Schema: .agent/schemas/publish-article.task.schema.yaml
## Reference Workflow: .agent/workflows/publish-article.md

from domain.post.protector import BlockProtector
from domain.post.formatter import PostFormatter
from domain.terminology.injector import TerminologyInjector
from domain.post.post import HugoPost

class PostOrchestrator:
    """Coordinates the cleanup and refinement pipeline for a post."""
    
    @staticmethod
    def cleanup(post, lexicon=None, rules=None):
        protector = BlockProtector()
        formatter = PostFormatter()
        
        # 1. Protection Phase
        protected_content, protected_blocks = protector.extract(post.body)

        # 2. Refinement Phase (On protected content)
        refined_content = formatter.sublimate_narrative(protected_content, rules)
        refined_content = formatter.normalize_headers(refined_content, rules)

        # 2.2 Terminology Anchoring
        if lexicon:
            injector = TerminologyInjector()
            temp_post = HugoPost()
            temp_post.body = refined_content
            injector.apply_lexicon(temp_post, lexicon)
            refined_content = temp_post.body

        # 3. Formatting Phase
        refined_content = formatter.ensure_more_tag(refined_content)
        refined_content = formatter.format_decision_points(refined_content)

        # 4. Restoration Phase
        post.body = protector.restore(refined_content, protected_blocks)
        
        # 5. Post-Restoration Polish
        formatter.relocate_alerts_after_more(post)
        
        return True
