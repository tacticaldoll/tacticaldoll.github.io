## Authored by Schema: .agent/schemas/publish-article.task.schema.yaml
## Reference Workflow: .agent/workflows/publish-article.md

import re

class BlockProtector:
    """Protects physical blocks (code, comments, alerts) from regex replacement."""
    
    def extract(self, body):
        """Extracts protected blocks and replaces them with markers."""
        blocks = []
        def replacer(match):
            blocks.append(match.group(0))
            return f"__PROTECTED_BLOCK_{len(blocks)-1}__"
        
        # 1. Code blocks
        content = re.sub(r'^```[\s\S]*?^```', replacer, body, flags=re.MULTILINE)

        # 2. Math. LaTeX is not prose: an EN alias in lexicon.terms_regex is
        # word-boundaried, and \b holds between the backslash and the letter, so
        # `\Delta` matched the term "Delta" and was rewritten to `\差異` —
        # corrupting the formula. Display math first, then single-line inline math.
        content = re.sub(r'\$\$[\s\S]*?\$\$', replacer, content)
        content = re.sub(r'(?<!\$)\$(?!\$)[^\n$]+?\$(?!\$)', replacer, content)
        
        def comment_replacer(match):
            comment = match.group(0)
            if re.search(r'<!--\s*(?:anchor|term):', comment) or comment.strip() == '<!--more-->':
                return comment
            blocks.append(comment)
            return f"__PROTECTED_BLOCK_{len(blocks)-1}__"
        content = re.sub(r'<!--[\s\S]*?-->', comment_replacer, content)
        
        # 4. Decision Points and Alerts (Special physical structures, excluding anchor/term alerts)
        def alert_replacer(match):
            alert = match.group(0)
            if "<!-- anchor:" in alert or "<!-- term:" in alert:
                return alert
            blocks.append(alert)
            return f"__PROTECTED_BLOCK_{len(blocks)-1}__"
        content = re.sub(r'^>\s*\[!.*?\][\s\S]*?(?=\n\n|\Z)', alert_replacer, content, flags=re.MULTILINE)
        
        return content, blocks

    def restore(self, content, blocks):
        """Restores protected blocks back to their markers."""
        for i, block in enumerate(blocks):
            content = content.replace(f"__PROTECTED_BLOCK_{i}__", block)
        return content
