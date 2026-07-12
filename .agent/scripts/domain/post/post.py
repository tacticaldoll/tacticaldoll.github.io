## Authored by Schema: .agent/schemas/publish-article.task.schema.yaml
## Reference Workflow: .agent/workflows/publish-article.md

import os
import re
from datetime import datetime
from infra import utils

class HugoPost:
    """
    Standardized entity for Hugo posts (Markdown with TOML front matter).
    Provides robust methods for parsing, manipulating, and reassembling posts.
    """
    def __init__(self, file_path=None):
        self.file_path = file_path
        self.metadata = {}
        self.body = ""
        self.raw_content = ""
        if file_path and os.path.exists(file_path):
            self.load()

    @classmethod
    def from_source(cls, source_text, post_meta):
        """
        [FACTORY] Creates a post entity from raw source report text and specific post metadata.
        Incorporates 'extract_pure_body' logic.
        """
        # 1. Extract pure body
        # 1.1 Strip YAML frontmatter if it exists at the absolute top
        content = re.sub(r'^---\s*\n.*?\n---\s*\n', '', source_text, flags=re.DOTALL)
        # 1.2 Strip the very first H1 if it exists
        content = re.sub(r'^[ \t]*#[ \t]+.*?\n', '', content).lstrip()
        # 1.3 Strip HTML front matter comment
        content = re.sub(r'^\s*<!--\s*front matter\s*-->\s*\n', '', content, flags=re.IGNORECASE)
        # 1.4 Strip standard top-level bold Key: Value pairs if they exist at the top
        while True:
            match = re.match(r'^\s*\*\*.*?\*\*:\s*.*?\n', content)
            if match:
                content = content[match.end():]
            else:
                break
        
        body = content.strip()
        
        # 2. Extract metadata
        post = cls()
        post.body = body
        
        # Initialize with minimal structural metadata only.
        # Full metadata (title, tags, draft status) is assembled by PostAssembler in pipeline run_finish().
        post.metadata = {
            "title": post_meta.get("title", "Untitled"),
            "date": post_meta.get("date", datetime.now().strftime('%Y-%m-%dT%H:%M:00+08:00')),
            "description": post_meta.get("description", ""),
            "tags": post_meta.get("tags", []),
            "draft": True  # Explicitly draft until assembler.build() promotes to published
        }
        
        return post

    def load(self, content=None):
        """Loads and parses post content from file or string."""
        if content is None and self.file_path:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        
        self.raw_content = content
        
        # 1. Handle Byte Order Mark (BOM)
        if content.startswith('\ufeff'):
            content = content[1:]
            
        # 2. Split Front Matter and Body using robust regex
        # Pattern: ^+++ [whitespace] $ (Multiline)
        parts = re.split(r'^\+\+\+\s*$', content, maxsplit=2, flags=re.MULTILINE)
        
        if len(parts) >= 3:
            # Metadata block found
            fm_text = parts[1].strip()
            self.body = parts[2].lstrip()
            
            # Use utility to parse TOML
            self.metadata, _ = utils.parse_toml_front_matter(f"+++\n{fm_text}\n+++")
        else:
            # Fallback for ill-formatted or missing FM
            self.metadata = {}
            self.body = content.lstrip()

    def save_to_string(self):
        """Returns the reassembled post content as a string."""
        if not self.metadata:
            return self.body.lstrip()
        # Reconstruct FM
        fm_str = utils.build_toml_front_matter(self.metadata).strip()
        
        # Consistent reassembly (+++ on own lines, double newline before body)
        return fm_str + "\n\n" + self.body.lstrip()

    def save(self, target_path=None):
        """Reassembles and saves the post."""
        path = target_path or self.file_path
        if not path:
            raise ValueError("No file path specified for saving.")

        final_content = self.save_to_string()
        
        # Ensure parent directory exists
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(final_content)
        
        return True

    def split_by_more(self, custom_body=None):
        """Returns (preview_area, main_body) split by the <!--more--> tag."""
        target_body = custom_body or self.body
        if "<!--more-->" in target_body:
            parts = target_body.split("<!--more-->", 1)
            return parts[0], parts[1]
        return "", target_body

    def get_summary_area(self):
        """Returns the text between the FM and the <!--more--> tag."""
        if "<!--more-->" in self.body:
            return self.body.split("<!--more-->", 1)[0].strip()
        return ""

    def audit(self, lexicon_engine=None, source_raw=None, source_path=None):
        """
        [VERIFICATION] Runs the audit suite via PostAuditor.
        Returns an AuditReport.
        """
        from domain.post.auditor import PostAuditor
        auditor = PostAuditor(engine=lexicon_engine)
        return auditor.audit(self, source_raw=source_raw, source_path=source_path)
