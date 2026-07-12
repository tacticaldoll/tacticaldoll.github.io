## Authored by Schema: .agent/schemas/publish-article.task.schema.yaml
## Reference Workflow: .agent/workflows/publish-article.md

import re
import os

class PostFormatter:
    """Handles Markdown formatting, narrative sublimation, and physical layout for posts."""
    
    def sublimate_narrative(self, content, rules=None):
        """Automated de-projectification and narrative elevation (NLP Driven)."""
        replacements = []
        
        if rules and "sublimations" in rules:
            for pattern, subst in rules["sublimations"].items():
                replacements.append((pattern, subst))
        
        if rules and "redactions" in rules:
            if isinstance(rules["redactions"], dict):
                for target_str, subst in rules["redactions"].items():
                    if target_str:
                        replacements.append((r'`' + re.escape(target_str) + r'`', f'`{subst}`'))
            elif isinstance(rules["redactions"], list):
                for path in rules["redactions"]:
                    if path:
                        replacements.append((r'`' + re.escape(path) + r'`', '`內部管線工具`'))
        
        result = content
        for pattern, replacement in replacements:
            result = re.sub(pattern, replacement, result)
            
        return result

    def normalize_headers(self, content, rules=None):
        """Standardizes headers based on taxonomy rules in handoff and global rules SSOT."""
        header_map = {}
        try:
            from infra import config
            import json
            if os.path.exists(config.RULES_JSON):
                with open(config.RULES_JSON, 'r', encoding='utf-8') as f:
                    global_rules = json.load(f)
                    header_map.update(global_rules.get("header_normalization", {}))
        except Exception as e:
            import sys
            print(f"[WARNING] formatter: Failed to load RULES_JSON, using built-in defaults: {e}", file=sys.stderr)

        if not header_map:
            header_map = {
                "Introduction": "背景",
                "Analysis": "分析",
                "Reflection": "省思",
                "Conclusion": "結論"
            }

        if rules and rules.get("headers"):
            header_map.update(rules["headers"])
            
        result = content
        for variation, standard in sorted(header_map.items(), key=lambda x: len(x[0]), reverse=True):
            if variation == standard:
                continue
            pattern = re.compile(r'^(#+[ \t]+)' + re.escape(variation) + r'[ \t]*$', re.MULTILINE | re.IGNORECASE)
            result = pattern.sub(r'\1' + standard, result)
            
        return result

    def format_decision_points(self, body):
        """Formats decision points as NOTE alerts if not already formatted."""
        lines = body.split('\n')
        new_lines = []
        for i, line in enumerate(lines):
            if line.strip().startswith('> **Decision Point**:'):
                if i == 0 or not lines[i-1].strip().startswith('> [!NOTE]'):
                    new_lines.append('> [!NOTE]')
            new_lines.append(line)
        return '\n'.join(new_lines)

    def ensure_more_tag(self, body):
        """Inserts <!--more--> at the first double line break if not present."""
        if "<!--more-->" in body:
            return body
            
        body_parts = re.split(r'\n\s*\n', body, maxsplit=1)
        if len(body_parts) > 1:
            return body_parts[0] + "\n\n<!--more-->\n\n" + body_parts[1].strip()
        else:
            return "<!--more-->\n\n" + body

    def relocate_alerts_after_more(self, post):
        """Moves summary-disturbing alerts to after the <!--more--> tag."""
        if '<!--more-->' not in post.body:
            return False
            
        pre_more, post_more = post.split_by_more()
        
        intro_lines = pre_more.splitlines()
        new_intro_lines = []
        collected_alerts = []
        collected_headers = []
        i = 0
        while i < len(intro_lines):
            line = intro_lines[i]
            line_strip = line.strip()
            
            if re.match(r'^>\s*\[!.*?\]', line_strip):
                collected_alerts.append(line)
                i += 1
                while i < len(intro_lines) and intro_lines[i].strip().startswith('>'):
                    collected_alerts.append(intro_lines[i])
                    i += 1
                continue
            elif re.match(r'^#+[ \t]+', line_strip):
                collected_headers.append(line)
            else:
                new_intro_lines.append(line)
            i += 1
        
        if collected_alerts or collected_headers:
            new_pre = "\n".join(new_intro_lines).strip() + "\n\n"
            moved_content = "\n".join(collected_headers + collected_alerts)
            post.body = new_pre + "<!--more-->\n\n" + moved_content.strip() + "\n\n" + post_more.strip()
            return True
        return False
