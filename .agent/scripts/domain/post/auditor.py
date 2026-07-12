## Authored by Schema: .agent/schemas/publish-article.task.schema.yaml
## Reference Workflow: .agent/workflows/publish-article.md

import re
import os
import glob
from infra import config
from infra.utils import parse_toml_front_matter

class MarkdownAnalyzer:
    """Analyzes markdown content and extracts structural metrics."""
    @staticmethod
    def analyze(content, is_source=False):
        if is_source:
            # Source report uses a different format (headers/bold keys)
            lines = content.splitlines()
            temp_lines = []
            skip_meta = True
            in_yaml = False
            for idx, line in enumerate(lines):
                if line.strip() == '---':
                    if in_yaml or idx < 3:
                        in_yaml = not in_yaml
                        continue
                if in_yaml:
                    continue
                if line.startswith('# '): continue
                if line.startswith('## '): skip_meta = False
                if skip_meta and re.match(r'\*\*.*?\*\*:', line): continue
                if skip_meta and '<!-- front matter -->' in line: continue
                temp_lines.append(line)
            body_text = "\n".join(temp_lines)
        else:
            # Target post uses TOML front matter
            _, body_text = parse_toml_front_matter(content)

        preview_area = ""
        main_body = body_text
        if not is_source and '<!--more-->' in body_text:
            parts = body_text.split('<!--more-->', 1)
            preview_area, main_body = parts[0], parts[1]
        
        headers = re.findall(r'^##\s+|^###\s+', body_text, re.MULTILINE)
        list_items = re.findall(r'^\s*[-*]\s+', body_text, re.MULTILINE)
        paragraphs = [p for p in re.split(r'\n\s*\n', body_text) if p.strip()]
        
        return {
            "text": main_body,
            "preview": preview_area,
            "full_text": content,
            "lines": len([l for l in body_text.splitlines() if l.strip()]),
            "headers": len(headers),
            "list_items": len(list_items),
            "paragraphs": len(paragraphs)
        }

class AuditReport:
    """Standardized report container for audit results."""
    def __init__(self, source_path=None, target_path=None):
        self.source_path = source_path
        self.target_path = target_path
        self.issues = []
        self.passed = True
        self.metrics = {}

    def add_issue(self, message, category="FAILURE"):
        self.issues.append(f"{category}: {message}")
        if category in ["FAILURE", "CRITICAL"]:
            self.passed = False

class PostAuditor:
    """Domain service for auditing Hugo posts against source reports and lexicon rules."""
    
    def __init__(self, engine=None):
        self.engine = engine

    def audit(self, post, source_raw=None, source_path=None):
        """Runs a full suite of audits on the post."""
        report = AuditReport(source_path=source_path, target_path=post.file_path)
        
        tgt_stats = MarkdownAnalyzer.analyze(post.save_to_string(), is_source=False)
        report.metrics["target"] = tgt_stats

        # 1. Structural Alignment
        if source_raw:
            src_stats = MarkdownAnalyzer.analyze(source_raw, is_source=True)
            report.metrics["source"] = src_stats
            self._audit_structure(src_stats, tgt_stats, report)

        # 2. Terminology Compliance
        if self.engine:
            self._audit_terminology(tgt_stats['text'], post.metadata, report)

        # 3. Content Purity & Formatting
        self._audit_content(post.save_to_string(), report)

        # 4. Security Check
        # Security check is now called from _audit_content using stripped text
        pass

        # 5. Series Continuity
        if source_path:
            self._audit_series(post.metadata, source_path, report)

        return report

    def _audit_structure(self, src, tgt, report):
        src_h, tgt_h = int(src['headers']), int(tgt['headers'])
        src_p, tgt_p = int(src['paragraphs']), int(tgt['paragraphs'])
        src_l, tgt_l = int(src['lines']), int(tgt['lines'])

        if src_h != tgt_h:
            report.add_issue(f"Header count mismatch! Source: {src_h}, Target: {tgt_h}")
        if src_p > tgt_p:
            report.add_issue("Paragraph collapse detected!", "FAILURE")
        if src_l > 0 and (tgt_l / src_l) < 0.9:
            report.add_issue(f"Density below 90% gate! ({tgt_l/src_l:.2%})", "FAILURE")

    def _audit_terminology(self, text, metadata, report):
        engine = self.engine
        if hasattr(engine, 'lexicon'):
            engine = engine.lexicon

        if not engine:
            return

        # 1. Forbidden terms in body
        forbidden = getattr(engine, 'forbidden', {}) or {}
        for f_term, correct_zh in forbidden.items():
            if f_term in text:
                report.add_issue(f"Found forbidden term '{f_term}' in body, use '{correct_zh}' instead.", "ALERT")

        # 2. First-use anchoring (Support for [!IMPORTANT] blocks)
        # Strip headers but KEEP alert blocks for anchor verification
        text_no_headers = re.sub(r"^#+\s+.*$", "", text, flags=re.MULTILINE)
        
        # Split text into logical paragraphs to check local anchoring
        # We split by double newline to treat paragraphs and their trailing callouts as one unit if not separated
        paragraphs = re.split(r'\n\s*\n', text_no_headers)
        
        mapping = getattr(engine, 'mapping', {}) or {}
        for zh, en_primary in mapping.items():
            if zh not in text_no_headers: continue
            
            # Find the first paragraph containing the term
            # IMPORTANT: We only care about the FIRST paragraph where it appears
            first_para_idx = -1
            first_match_obj = None
            for idx, para in enumerate(paragraphs):
                m = re.search(re.escape(zh), para)
                if m:
                    # Filter out overlapping terms
                    is_overlap = any(len(oz) > len(zh) and zh in oz and oz in para for oz in mapping.keys() if len(oz) > len(zh))
                    if not is_overlap:
                        first_para_idx = idx
                        first_match_obj = m
                        break
            
            if first_para_idx == -1 or first_match_obj is None: continue
            
            levels = getattr(engine, 'levels', {}) or {}
            level = levels.get(zh, 1)
            if level >= 3: continue
            
            para = paragraphs[first_para_idx]
            res = engine.lookup(zh)
            key = res.get("key") if res else zh
            if not key:
                key = zh
            
            # Check for block anchor at the end of this paragraph/unit (supporting both legacy ZH and CamelCase key)
            block_anchor = re.search(f'<!--\\s*anchor:(?:{re.escape(zh)}|{re.escape(key)})\\s*-->', para)
            
            # Check for deprecated inline anchor
            suffix = para[first_match_obj.end():first_match_obj.end()+100]
            inline_anchor = re.search(r'^[\s\*_]*[\(（](.*?)[\)）]', suffix)
            
            if not block_anchor and not inline_anchor:
                report.add_issue(f"First use of '{zh}' (Level {level}) must be anchored in an [!IMPORTANT] block.", "ALERT")
            elif inline_anchor:
                # Flag inline anchors for relocation unless it's a Level 3 term (already skipped)
                report.add_issue(f"Inline anchor for '{zh}' should be moved to an [!IMPORTANT] block at the end of the paragraph.", "ALERT")
            
            # Verify if it's inside an IMPORTANT block
            if block_anchor and "> [!IMPORTANT]" not in para:
                report.add_issue(f"Anchor for '{zh}' found but its [!IMPORTANT] block is missing or malformed.", "ALERT")

        # 3. Metadata Tags
        tag_issues = engine.validate_tags(metadata.get('tags', []))
        for issue in tag_issues:
            report.add_issue(issue, "CRITICAL")

    def _audit_security(self, text, report):
        forbidden_patterns = [r'\.agent-scratch', r'c:\\', r'[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}']
        for p in forbidden_patterns:
            if re.search(p, text, re.IGNORECASE):
                report.add_issue(f"Sensitive string matching pattern '{p}'", "CRITICAL")

    def _audit_content(self, content, report):
        # Alert position checks
        more_match = re.search(r'<!--\s*more\s*-->', content)
        if more_match:
            summary_part = content[:more_match.start()]
            if re.search(r'^>\s*\[!(.*?)\]', summary_part, re.MULTILINE):
                report.add_issue("Alert block found before '<!--more-->'. Move to body.")
        
        # Alerts in code blocks
        content_no_code_temp = re.sub(r'```[\s\S]*?```', '', content)
        if content.count("> [!") > content_no_code_temp.count("> [!"):
            report.add_issue("Alert block found inside a code block.", "CRITICAL")
            
        # Strip code blocks for security audit to avoid false positives with UUIDs etc.
        content_no_code = re.sub(r'```[\s\S]*?```', '', content)
        self._audit_security(content_no_code, report)

    def _audit_series(self, metadata, src_path, report):
        series = metadata.get('series', [])
        if not series: return
        
        src_dir = os.path.dirname(src_path)
        guide_files = glob.glob(os.path.join(src_dir, "guide*.md"))
        if not guide_files:
            parent_dir = os.path.dirname(src_dir)
            guide_files = glob.glob(os.path.join(parent_dir, "guide*.md"))
            
        if not guide_files:
            report.add_issue(f"Series assigned ({series}) but no 'guide*.md' found.", "CRITICAL")
