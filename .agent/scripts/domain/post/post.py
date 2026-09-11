## Authored by Schema: .agent/schemas/publish-article.task.schema.yaml
## Reference Workflow: .agent/workflows/publish-article.md

import os
import re
import copy
from datetime import datetime
from infra import utils

# Captures the verbatim front matter block plus the whitespace separating it from
# the body: everything before the body starts. Re-emitting this instead of rebuilding
# from the parsed dict is what preserves the `# term:Key` tag comments, which carry
# every tag's anchor identity and do not survive a TOML parse.
_FM_PREFIX = re.compile(r'^(﻿?\+\+\+[ \t]*\n.*?\n\+\+\+[ \t]*\n\s*)', re.DOTALL)

# The tags array inside a verbatim front matter block, and one entry within it.
# A tag's identity is its `# term:Key` comment, not its display text: the display
# can be corrected while the key stays stable, so edits must be keyed on the comment.
_TAGS_BLOCK = re.compile(r'(tags\s*=\s*\[)(.*?)(\])', re.DOTALL)
_TAG_ENTRY = re.compile(r'^([ \t]*)"(.+?)"[ \t]*,?[ \t]*#[ \t]*term:(\S+)[ \t]*$')

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
        self.raw_fm_prefix = None
        self._meta_snapshot = None
        self.tag_entries = None      # [(display, key)] parsed from the verbatim FM
        self._tags_dirty = False
        if file_path and os.path.exists(file_path):
            self.load()

    @classmethod
    def from_source(cls, source_text, post_meta):
        """
        [FACTORY] Creates a post entity from raw source report text and specific post metadata.
        Incorporates 'extract_pure_body' logic.
        """
        # 1. Extract pure body: the provenance header strip is shared with the
        # report scanners in infra.utils so both paths cannot drift apart.
        body = utils.strip_report_provenance(source_text)
        
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

        # 0. Keep the front matter exactly as written, and snapshot what we parsed
        # out of it. save_to_string() re-emits this prefix verbatim whenever the
        # metadata has not been touched, so a load/save round trip cannot silently
        # drop the tag comments. A caller that DOES mutate metadata falls back to
        # rebuilding, which still loses them \u2014 structured tag editing is a separate
        # concern and belongs to the tag anchorer, not here.
        prefix_match = _FM_PREFIX.match(content)
        self.raw_fm_prefix = prefix_match.group(1) if prefix_match else None

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
            self.raw_fm_prefix = None

        self._meta_snapshot = copy.deepcopy(self.metadata)
        self.tag_entries = self._parse_tag_entries()
        self._tags_dirty = False

    def _parse_tag_entries(self):
        """Reads `[(display, key)]` out of the verbatim front matter. Returns None when
        there is no front matter or no keyed tags array to read."""
        if not self.raw_fm_prefix:
            return None
        m = _TAGS_BLOCK.search(self.raw_fm_prefix)
        if not m:
            return None
        entries = []
        for line in m.group(2).splitlines():
            em = _TAG_ENTRY.match(line)
            if em:
                entries.append((em.group(2), em.group(3)))
        return entries

    def set_tag_entries(self, entries):
        """Replaces the keyed tags. The rest of the front matter still round-trips
        verbatim, so editing tags no longer costs the other fields their formatting
        or their comments."""
        self.tag_entries = list(entries)
        self._tags_dirty = True
        self.metadata["tags"] = [d for d, _ in self.tag_entries]
        self._meta_snapshot = copy.deepcopy(self.metadata)

    def _splice_tags(self, fm_prefix):
        """Rewrites only the tags array inside a verbatim front matter block, keeping
        the original indent and closing padding. Every other byte is preserved."""
        m = _TAGS_BLOCK.search(fm_prefix)
        if not m:
            return fm_prefix
        head, body, tail = m.group(1), m.group(2), m.group(3)

        indent = "    "
        for line in body.splitlines():
            em = _TAG_ENTRY.match(line)
            if em:
                indent = em.group(1) or indent
                break
        close_pad = re.search(r'(\n[ \t]*)$', body)
        close = close_pad.group(1) if close_pad else "\n"

        if self.tag_entries:
            new_body = "".join(f'\n{indent}"{d}", # term:{k}' for d, k in self.tag_entries) + close
        else:
            new_body = ""
        return fm_prefix[:m.start()] + head + new_body + tail + fm_prefix[m.end():]

    def save_to_string(self):
        """Returns the reassembled post content as a string."""
        if not self.metadata:
            return self.body.lstrip()

        # Untouched metadata re-emits the original front matter byte-for-byte, so a
        # load/save round trip is lossless even though the TOML parse behind
        # self.metadata cannot see the `# term:Key` tag comments. Pinned by
        # post_tester.py over the published corpus.
        if self.raw_fm_prefix is not None and self.metadata == self._meta_snapshot:
            prefix = self._splice_tags(self.raw_fm_prefix) if self._tags_dirty else self.raw_fm_prefix
            return prefix + self.body

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
