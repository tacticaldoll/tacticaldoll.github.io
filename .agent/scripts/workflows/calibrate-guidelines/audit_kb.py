import os
import re
import json
import sys
import glob

# Add scripts root to path
scripts_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if scripts_root not in sys.path:
    sys.path.append(scripts_root)

from infra import config
from lexicon import Lexicon

class KBAuditor:
    """Class-based auditor for terminology and Hugo content compliance."""
    
    def __init__(self):
        self.terminology_path = config.TERMINOLOGY_JSON
        self.taxonomy_path = config.TAXONOMY_MD
        self.content_dir = config.POSTS_DIR
        self.lexicon = Lexicon(self.terminology_path)
        self.valid_headers, self.taxonomy_tags = self.load_taxonomy()

    def iter_repo_files(self, extensions=None):
        """Yields project files for governance scans."""
        skip_dirs = {".git", "node_modules", "public", "resources"}
        for root, dirs, files in os.walk(config.ROOT_DIR):
            dirs[:] = [d for d in dirs if d not in skip_dirs]
            for filename in files:
                if extensions and not any(filename.endswith(ext) for ext in extensions):
                    continue
                yield os.path.join(root, filename)

    def rel(self, file_path):
        return os.path.relpath(file_path, config.ROOT_DIR)
        
    def load_taxonomy(self):
        """Extracts valid headers and tags from taxonomy.md."""
        if not os.path.exists(self.taxonomy_path):
            return set(), set()
        with open(self.taxonomy_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 1. Generic Headers
        header_section = re.search(r'### A\. 全域通用標題.*?\n(.*?)\n###', content, re.DOTALL)
        valid_headers = []
        if header_section:
            matches = re.findall(r'\|\s*\*\*(.*?)\*\*\s*\|', header_section.group(1))
            valid_headers = [m.strip() for m in matches]

        # 2. Taxonomy Tags (slugs)
        tag_matches = re.findall(r'- `(.*?)`:', content)
        
        return set(valid_headers), set(tag_matches)
        
    def get_banned_words(self):
        """Dynamically extracts all forbidden terms from the knowledge base."""
        banned = set()
        for item in self.lexicon.items:
            for f in item.get('forbidden', []):
                banned.add(f)
        return banned

    def audit_terminology(self):
        """Audits the terminology source of truth (JSON)."""
        banned_words = self.get_banned_words()
        errors = []
        
        for item in self.lexicon.items:
            zh = item.get('zh', '')
            desc = item.get('description', '')
            for banned in banned_words:
                if banned in zh or banned in desc:
                    errors.append(f"[Terminology] Term '{zh}' contains banned word '{banned}'")
        return errors

    def audit_posts(self):
        """Audits Hugo posts for linguistic and taxonomy compliance."""
        banned_words = self.get_banned_words()
        errors = []
        post_files = glob.glob(os.path.join(self.content_dir, "**/index.md"), recursive=True)
        
        for file_path in post_files:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            rel_path = os.path.relpath(file_path, self.content_dir)
            
            # 1. Linguistic Safeguard (Banned words in body)
            for banned in banned_words:
                if banned in content:
                    errors.append(f"[{rel_path}] Contains banned word '{banned}'")
            
            # 2. Header Normalization
            headers = re.findall(r'^##\s+(.*)', content, re.MULTILINE)
            for h in headers:
                h_clean = h.strip()
                generic_candidates = {"引言", "背景", "前言", "觀察", "發現", "結果", "決策", "決議", "結案", "總結", "教訓", "啟示", "後記", "結論"}
                if h_clean in generic_candidates and h_clean not in self.valid_headers:
                    errors.append(f"[{rel_path}] Header '## {h_clean}' should be normalized per taxonomy.md")

        return errors

    def audit_governance(self):
        """Audits governance files for drift that should be physically blocked."""
        errors = []
        reference_path = os.path.join(config.AGENT_DIR, "reference", "agent-operating-guideline.md")
        knowledge_dir = os.path.join(config.AGENT_DIR, "knowledge")

        if os.path.exists(knowledge_dir):
            errors.append("[Governance] Deprecated .agent/knowledge directory exists; active reference must live in .agent/reference/")

        if not os.path.exists(reference_path):
            errors.append("[Governance] Missing active reference: .agent/reference/agent-operating-guideline.md")

        # Reference is a non-executable guidance layer, not a JSON database area.
        for file_path in self.iter_repo_files(extensions=(".json",)):
            rel_path = self.rel(file_path)
            if rel_path.startswith(os.path.join(".agent", "reference") + os.sep):
                errors.append(f"[Governance] JSON database entity found in reference layer: {rel_path}")

        markdown_files = list(self.iter_repo_files(extensions=(".md", ".yaml", ".yml")))
        for file_path in markdown_files:
            rel_path = self.rel(file_path)
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            if "../databases/" in content:
                errors.append(f"[Governance] Stale database path '../databases/' in {rel_path}")

            for line in content.splitlines():
                if "file:///Users/" in line or "/Users/" in line:
                    if "如 `" in line or "例如" in line:
                        continue
                    errors.append(f"[Governance] Local absolute path reference in {rel_path}")
                    break

            terminology_allowed = {
                "GUIDE.md",
                os.path.join(".agent", "reference", "agent-operating-guideline.md"),
            }
            # Match the bare filename terminology.md, not longer names like consolidate-terminology.md.
            if re.search(r'(?<![\w-])terminology\.md', content) and rel_path not in terminology_allowed:
                errors.append(f"[Governance] terminology.md referenced outside permanent gate definitions: {rel_path}")

            command_docs = rel_path == "GUIDE.md" or rel_path.startswith(os.path.join(".agent", "workflows") + os.sep) or rel_path.startswith(os.path.join(".agent", "schemas") + os.sep) or rel_path == os.path.join(".agent", "reference", "agent-operating-guideline.md")
            if command_docs:
                for line_no, line in enumerate(content.splitlines(), 1):
                    if re.search(r'(^|[` ])python \.agent/', line):
                        errors.append(f"[Governance] Python command example must use python3 in {rel_path}:{line_no}")

            if rel_path == "GUIDE.md":
                if ".agent/reference/agent-operating-guideline.md" not in content:
                    errors.append("[Governance] GUIDE.md does not reference agent-operating-guideline.md")
                if ".agent/lexicon-core/databases/taxonomy.md` 定義" in content:
                    errors.append("[Governance] GUIDE.md treats taxonomy.md as taxonomy SSOT")

            if rel_path == os.path.join(".agent", "workflows", "distill-knowledge.md"):
                if "../schemas/" in content or ".agent/" in content:
                    errors.append("[Governance] distill-knowledge workflow is project-coupled despite zero-coupling boundary")

        # Workflow front matter references must point to existing specs and schemas.
        workflow_dir = os.path.join(config.AGENT_DIR, "workflows")
        for workflow_path in glob.glob(os.path.join(workflow_dir, "*.md")):
            rel_workflow = self.rel(workflow_path)
            with open(workflow_path, "r", encoding="utf-8") as f:
                content = f.read()
            spec_match = re.search(r'^spec:\s*"([^"]+)"', content, re.MULTILINE)
            if spec_match:
                spec_path = os.path.normpath(os.path.join(os.path.dirname(workflow_path), spec_match.group(1)))
                if not os.path.exists(spec_path):
                    errors.append(f"[Governance] Missing spec target in {rel_workflow}: {spec_match.group(1)}")
            schema_match = re.search(r'^schema:\s*\[(.*?)\]', content, re.MULTILINE)
            if schema_match:
                for schema_ref in re.findall(r'"([^"]+)"', schema_match.group(1)):
                    schema_path = os.path.normpath(os.path.join(os.path.dirname(workflow_path), schema_ref))
                    if not os.path.exists(schema_path):
                        errors.append(f"[Governance] Missing schema target in {rel_workflow}: {schema_ref}")

        publish_task = os.path.join(config.AGENT_DIR, "schemas", "publish-article.task.schema.yaml")
        if os.path.exists(publish_task):
            with open(publish_task, 'r', encoding='utf-8') as f:
                task_content = f.read()
            forbidden_publish_phrases = [
                "初始化 `handoff.posts.json`",
                "初始化 `handoff.terms.json`",
                "執行 `python .agent/scripts/workflows/generate-article/prepare_handoff.py",
                "執行 `python .agent/scripts/workflows/generate-article/refine_handoff.py",
                "執行 `python3 .agent/scripts/workflows/generate-article/prepare_handoff.py",
                "執行 `python3 .agent/scripts/workflows/generate-article/refine_handoff.py",
            ]
            for phrase in forbidden_publish_phrases:
                if phrase in task_content:
                    errors.append(f"[Governance] publish-article task reclaims init-handoff duty: {phrase}")
            if "填寫 `domain_tag`" in task_content:
                errors.append("[Governance] publish-article task asks AI to fill script-owned domain_tag")

        handoff_posts_schema = os.path.join(config.AGENT_DIR, "schemas", "handoff.posts.schema.yaml")
        if os.path.exists(handoff_posts_schema):
            with open(handoff_posts_schema, "r", encoding="utf-8") as f:
                schema_content = f.read()
            if "[Stage 1]: 由 `/publish-article`" in schema_content:
                errors.append("[Governance] handoff.posts schema assigns prepare_handoff to publish-article")
            if "processed" in schema_content and "status:" in schema_content:
                errors.append("[Governance] handoff.posts schema contains stale status 'processed'")

        prepare_script = os.path.join(config.AGENT_DIR, "scripts", "workflows", "generate-article", "prepare_handoff.py")
        if os.path.exists(prepare_script):
            with open(prepare_script, "r", encoding="utf-8") as f:
                if "Stage 1: Handoff Preparation" in f.read():
                    errors.append("[Governance] prepare_handoff.py still describes itself as Stage 1")

        orchestrate_batch = os.path.join(config.AGENT_DIR, "scripts", "workflows", "generate-article", "orchestrate_batch.py")
        if os.path.exists(orchestrate_batch):
            with open(orchestrate_batch, "r", encoding="utf-8") as f:
                batch_content = f.read()
            if "prepare_handoff.py" in batch_content:
                errors.append("[Governance] batch orchestration must not rerun prepare_handoff outside /init-handoff")

        # Header rewrite/crop regex must not use broad \s* because it can consume newlines.
        for file_path in self.iter_repo_files(extensions=(".py",)):
            rel_path = self.rel(file_path)
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_no, line in enumerate(f, 1):
                    if not any(call in line for call in ("re.sub", "re.match", "re.compile", "re.search", "re.findall")):
                        continue
                    if "\\s*" not in line:
                        continue
                    if "##" in line or "#{" in line or "^#" in line or "^\\s*#" in line:
                        errors.append(f"[Governance] Potential broad header whitespace regex '\\s*' in {rel_path}:{line_no}")

        # Active handoff term descriptions must be completed before publishing.
        for file_path in self.iter_repo_files(extensions=("handoff.terms.json",)):
            with open(file_path, 'r', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError as exc:
                    errors.append(f"[Governance] Invalid handoff terms JSON {self.rel(file_path)}: {exc}")
                    continue
            locked = data.get("terms", {}).get("locked", [])
            for term in locked:
                desc = term.get("description", "")
                if not desc.strip() or any(p in desc for p in ["TODO", "PENDING_REFINEMENT", "PENDING_NLP_DIGESTION"]):
                    zh = term.get("zh", "<unknown>")
                    errors.append(f"[Governance] Incomplete locked term description in {self.rel(file_path)}: {zh}")

        # Crystallization reports are internal knowledge artifacts, NOT Hugo posts:
        # terminology anchoring is a publish-article responsibility. Report prose in
        # .agent-scratch/ must stay anchor-free. Syntax shown for explanation belongs
        # in code blocks, so strip code before scanning (mirrors the injector's own
        # code-block protection) to avoid flagging legitimate examples.
        anchor_marker = re.compile(r'<!--\s*(?:term|anchor):')
        for file_path in glob.glob(os.path.join(config.SCRATCH_DIR, "**", "*.md"), recursive=True):
            with open(file_path, 'r', encoding='utf-8') as f:
                prose = f.read()
            prose = re.sub(r'^```[\s\S]*?^```', '', prose, flags=re.MULTILINE)  # fenced code
            prose = re.sub(r'`[^`\n]*`', '', prose)                              # inline code spans
            if anchor_marker.search(prose):
                errors.append(f"[Governance] Terminology anchor in non-post report prose (anchoring is publish-only): {self.rel(file_path)}")

        return errors

    def run(self):
        print("-" * 50)
        print("KB & Content Comprehensive Auditor (Class-based)")
        print("-" * 50)
        
        # 1. Terminology Audit
        term_errors = self.audit_terminology()
        if term_errors:
            print(f"TERMINOLOGY ERRORS: {len(term_errors)}")
            for e in term_errors:
                print(f"  - {e}")
        else:
            print("TERMINOLOGY: PASSED")
            
        # 2. Content Audit
        content_errors = self.audit_posts()
        if content_errors:
            print(f"CONTENT ERRORS: {len(content_errors)}")
            for e in content_errors:
                print(f"  - {e}")
        else:
            print("CONTENT: PASSED")

        # 3. Governance Drift Audit
        governance_errors = self.audit_governance()
        if governance_errors:
            print(f"GOVERNANCE ERRORS: {len(governance_errors)}")
            for e in governance_errors:
                print(f"  - {e}")
        else:
            print("GOVERNANCE: PASSED")
            
        print("-" * 50)
        if term_errors or content_errors or governance_errors:
            return False
        else:
            print("Overall Status: HEALTHY")
            return True

def main():
    auditor = KBAuditor()
    if not auditor.run():
        sys.exit(1)

if __name__ == "__main__":
    main()
