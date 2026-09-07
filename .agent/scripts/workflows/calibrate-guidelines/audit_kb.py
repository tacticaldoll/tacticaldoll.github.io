import os
import re
import ast
import io
import contextlib
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

    def _called_name(self, call):
        """Returns the final attribute or bare name of a Call's target, so `x.y.get(...)`
        and `get(...)` both answer 'get'. None when the target is not a plain reference."""
        func = call.func
        if isinstance(func, ast.Attribute):
            return func.attr
        if isinstance(func, ast.Name):
            return func.id
        return None

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

        # A broad whitespace class placed immediately after a line anchor eats the
        # newline the anchor exists to assert, so the pattern matches from an earlier
        # line and crosses blank lines it was never meant to reach. Only [ \t] may
        # express horizontal whitespace there.
        #
        # Keyed on the anchored form itself, not on a header marker. The previous
        # condition required a '#' on the same line, which no front-matter regex
        # carries: the provenance stripper's own three anchored patterns sat in a file
        # this loop already walked, and passed. Widening the marker list to ** and
        # <!-- instead catches <!--\s*anchor:, where the class sits inside the comment
        # and has no anchor to defeat. The anchored form is the defect, so it is what
        # this reads.
        for file_path in self.iter_repo_files(extensions=(".py",)):
            rel_path = self.rel(file_path)
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_no, line in enumerate(f, 1):
                    if not any(call in line for call in ("re.sub", "re.match", "re.compile", "re.search", "re.findall")):
                        continue
                    if "^\\s*" not in line:
                        continue
                    errors.append(f"[Governance] Broad whitespace after a line anchor in "
                                  f"{rel_path}:{line_no}; the anchor does not hold when the "
                                  f"class can consume the newline. Use '^[ \\t]*'.")

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

        # `is_series` has exactly one SSOT: the physical existence of a `guide*.md`
        # in the session directory (init-handoff.task.schema.yaml). A session that
        # produced a single main report legitimately omits the guide, so it is a
        # standalone post and MUST NOT declare a series-level `series` in its
        # series-map — the declaration would be silently discarded downstream,
        # leaving a series named in the internal map but absent from the post.
        for map_path in glob.glob(os.path.join(config.SCRATCH_DIR, "*", "series-map*.md")):
            with open(map_path, 'r', encoding='utf-8') as f:
                map_content = f.read()
            declares_series = re.search(r'^[ \t]*series[ \t]*=', map_content, re.MULTILINE)
            if not declares_series:
                continue
            session_dir = os.path.dirname(map_path)
            if not glob.glob(os.path.join(session_dir, "guide*.md")):
                errors.append(
                    f"[Governance] series-map declares `series` but session has no guide*.md, "
                    f"so is_series resolves false and the declaration is dropped: {self.rel(map_path)}")

        # Provenance headers must never reach domain classification: `**Agent**: ...`
        # matches a detection keyword and is identical across a session's reports, so
        # raw text let generation metadata pick the domain for all of them.
        #
        # Asserted by running the classifier, not by reading it. An earlier version
        # walked classify_domain's AST for a strip_report_provenance call, which a
        # discarded `strip_report_provenance("")` satisfies while the real path
        # classifies raw text — the check passed with the defect fully restored. What
        # matters is whether provenance can decide the answer, and only the answer
        # shows that. The keyword is drawn from taxonomy.json so this test does not
        # embed a copy of the SSOT either.
        try:
            from infra.taxonomy import TaxonomyEngine
        except ImportError as exc:
            errors.append(f"[Governance] Cannot import TaxonomyEngine to verify the "
                          f"provenance invariant: {exc}")
        else:
            engine = TaxonomyEngine()
            detection = engine.data.get("ai_taxonomy", {}).get("detection_keywords", {})
            probe = next(((cat, kws[0]) for cat, kws in detection.items() if kws), None)
            if probe is None:
                errors.append("[Governance] taxonomy.json defines no detection keywords; "
                              "the provenance invariant cannot be verified")
            else:
                category, keyword = probe
                # A neutral body: one character cannot contain any multi-character keyword.
                header_voter = (f"# T\n\n<!-- front matter -->\n"
                                f"**Structure**: Analytical Essay\n"
                                f"**Agent**: {keyword} harness 1.0\n"
                                f"**Source**: conversation\n\n---\n\nx\n")
                if engine.classify_domain(header_voter) is not None:
                    errors.append(f"[Governance] classify_domain lets the provenance header decide "
                                  f"the domain: a report whose only occurrence of '{keyword}' is in "
                                  f"**Agent** classified as '{category}'. Strip the header before "
                                  f"matching (infra.utils.strip_report_provenance).")
                # And the strip must not eat the prose it is meant to preserve.
                body_voter = (f"# T\n\n<!-- front matter -->\n"
                              f"**Structure**: Analytical Essay\n"
                              f"**Agent**: neutral harness 1.0\n"
                              f"**Source**: conversation\n\n---\n\n{keyword}\n")
                if engine.classify_domain(body_voter) != category:
                    errors.append(f"[Governance] classify_domain no longer sees the prose: a report "
                                  f"whose body contains '{keyword}' did not classify as '{category}'.")

                # And the strip must be idempotent, because it runs twice: from_source
                # strips a report to build the body, then classify_domain strips again
                # whatever it is handed. Every line it removes is provenance only
                # inside a header block — a leading H1 is otherwise the document's
                # title, a bold pair is otherwise prose — so a second pass over a clean
                # body was eating that body's own first line, keywords and all. Both
                # shapes are probed with the keyword placed only in the line at risk,
                # so a strip that eats it shows up as a lost classification rather than
                # as a text comparison nobody can read.
                for shape, prose in (
                        ("a bold pair", f"**前提**: 本文討論 {keyword} 的邊界。\n\n## T\nx\n"),
                        ("an H1 title", f"# 論 {keyword} 的邊界\n\n## T\nx\n")):
                    if engine.classify_domain(prose) != category:
                        errors.append(
                            f"[Governance] a prose body opening with {shape} lost that line to "
                            f"the provenance strip: '{keyword}' appears only there and the body "
                            f"no longer classifies as '{category}'. The strip must be idempotent "
                            f"— from_source strips the report, classify_domain strips again — so "
                            f"it may only remove those lines when a provenance header block is "
                            f"actually present (infra.utils.opens_provenance_header).")

        # Asymmetric Tagging must survive the call site. classify_domain returns None
        # on purpose so a post with no AI subject matter carries no AI domain tag, and
        # `AI` is itself one of the categories — so a coerced `or "AI"` cancels that
        # policy, and the same literal as the default for an absent domain_tag makes
        # the `not in ai_categories` guard False and skips classification entirely.
        # Neither is visible in the data: the emitted tag looks like a real category.
        #
        # Asserted by assembling tags, not by reading the source. An AST check for the
        # literal would pass the moment the coercion moved into a helper or a config
        # constant, and what matters is only whether a domain can be invented for a
        # post that has none. The categories come from taxonomy.json so this test
        # holds no copy of the SSOT.
        try:
            from domain.post.assembler import PostAssembler
            from infra.taxonomy import TaxonomyEngine as _ProbeEngine
        except ImportError as exc:
            errors.append(f"[Governance] Cannot import PostAssembler to verify "
                          f"asymmetric tagging: {exc}")
        else:
            class _StubPost:
                def __init__(self, body):
                    self.body = body
                    self.metadata = {}

            def _clean(tag):
                return re.sub(r'\s*[(（].*?[)）]', '', tag or '').strip().lower()

            probe_lex = Lexicon(self.terminology_path)
            probe_cats = probe_lex.taxonomy.get("ai_taxonomy", {}).get("categories", [])
            if not probe_cats:
                errors.append("[Governance] taxonomy.json defines no AI categories; "
                              "asymmetric tagging cannot be verified")
            else:
                cat_set = {_clean(c) for c in probe_cats}
                # A pure-technical body: no detection keyword and no lexicon term, so
                # the only domain-shaped tag it could carry is an invented one. This is
                # the case classify_domain's Asymmetric Tagging comment names (Linux).
                neutral = "本文說明掛載點與憑證傳遞，以及 setuid 位元在權限升級路徑上的角色。\n"
                if _ProbeEngine().classify_domain(neutral) is not None:
                    errors.append("[Governance] the asymmetric-tagging probe body is no longer "
                                  "keyword-free; it now classifies, so the check below cannot "
                                  "distinguish an invented domain from a real one")
                else:
                    # A real genre, drawn from taxonomy.json rather than hardcoded, so the
                    # probe does not trip genre_tag's unrelated fallback alarm.
                    probe_genre = next((en for en in probe_lex.taxonomy.get("genres", {})
                                        if " " in en), "")
                    base = {"ai_info": {"generation": {"scope": probe_genre}}}
                    for label, extra in (("absent", {}),
                                         ("unclassifiable", {"domain_tag": "NotACategory"})):
                        meta = dict(base, **extra)
                        try:
                            tags = PostAssembler(_StubPost(neutral)).with_tags(meta, probe_lex)._tags
                        except Exception as exc:
                            errors.append(f"[Governance] cannot assemble tags to verify asymmetric "
                                          f"tagging ({label} domain_tag): {exc}")
                            continue
                        invented = [zh for zh, _ in tags if _clean(zh) in cat_set]
                        if invented:
                            errors.append(
                                f"[Governance] a post with no AI subject matter was given the "
                                f"domain tag {invented!r} ({label} domain_tag). "
                                f"TaxonomyEngine.classify_domain returns None for it on purpose; "
                                f"the call site in domain/post/assembler.py must not coerce that "
                                f"to a category. Note `AI` is itself a category, so using it as "
                                f"the default also skips classification.")

                    # The reverse direction matters as much. A call site that dropped the
                    # domain unconditionally would satisfy the check above while stripping
                    # every post of its category — so a body that does classify must still
                    # carry that category out as a tag. Keyword and category both come from
                    # taxonomy.json.
                    probe = next(((cat, kws[0]) for cat, kws
                                  in probe_lex.taxonomy.get("ai_taxonomy", {})
                                             .get("detection_keywords", {}).items() if kws), None)
                    if probe is None:
                        errors.append("[Governance] taxonomy.json defines no detection keywords; "
                                      "the domain-survives-assembly direction cannot be verified")
                    else:
                        cat, kw = probe
                        classified = f"本文討論 {kw} 的作用與邊界。\n"
                        if _ProbeEngine().classify_domain(classified) != cat:
                            errors.append(f"[Governance] the domain-survival probe no longer "
                                          f"classifies as '{cat}'; the direction below is vacuous")
                        else:
                            try:
                                tags = PostAssembler(_StubPost(classified)).with_tags(dict(base), probe_lex)._tags
                            except Exception as exc:
                                errors.append(f"[Governance] cannot assemble tags to verify domain "
                                              f"survival: {exc}")
                            else:
                                if not any(_clean(zh) == _clean(cat) for zh, _ in tags):
                                    errors.append(
                                        f"[Governance] a post that classifies as '{cat}' lost its "
                                        f"domain tag during assembly (emitted {[z for z, _ in tags]!r}). "
                                        f"Asymmetric Tagging drops the tag only when "
                                        f"classify_domain returns None, never otherwise.")

                            # And no caller may window the text it classifies. The
                            # authoritative path (prepare_handoff) classifies the full
                            # report; a truncation at the assembly call site classified on
                            # a different basis, so the same post could resolve to
                            # different domains depending on which caller reached it. A
                            # subject stated only in a long post's final paragraph must
                            # still decide its domain.
                            long_body = (neutral * 200) + classified
                            if len(long_body) < 6000:
                                errors.append("[Governance] the windowing probe body is too short "
                                              "to detect a truncation; raise the filler count")
                            else:
                                try:
                                    tags = PostAssembler(_StubPost(long_body)).with_tags(dict(base), probe_lex)._tags
                                except Exception as exc:
                                    errors.append(f"[Governance] cannot assemble tags to verify the "
                                                  f"classification window: {exc}")
                                else:
                                    if not any(_clean(zh) == _clean(cat) for zh, _ in tags):
                                        errors.append(
                                            f"[Governance] a {len(long_body)}-character post whose only "
                                            f"'{kw}' occurrence sits in its final paragraph did not "
                                            f"classify as '{cat}': the classification input is being "
                                            f"truncated. prepare_handoff classifies the full report, so "
                                            f"a window at any other caller gives the same post a "
                                            f"different domain.")

        # The evidence view and the answer must stay the same decision. classify_domain
        # delegates to classify_domain_evidence so that a caller surfacing ambiguity is
        # never reporting on a classification other than the one that shipped; two
        # parallel implementations would drift and the report would start describing a
        # domain the post does not have. Asserted over every category's own keyword.
        try:
            from infra.taxonomy import TaxonomyEngine as _EvEngine
        except ImportError as exc:
            errors.append(f"[Governance] Cannot import TaxonomyEngine to verify the "
                          f"evidence invariant: {exc}")
        else:
            ev = _EvEngine()
            ev_tax = ev.data.get("ai_taxonomy", {})
            ev_cats = ev_tax.get("categories", [])
            ev_det = ev_tax.get("detection_keywords", {})
            probes = ["本文說明掛載點與憑證傳遞。\n"]
            probes += [f"本文討論 {ev_det[c][0]} 的邊界。\n" for c in ev_cats if ev_det.get(c)]
            # One keyword from every category. Single-category probes cannot detect a
            # divergence in iteration order — they resolve to the same answer forwards or
            # backwards — so the set must include a body where order is the only thing
            # deciding the winner. This is the probe that catches a reimplementation.
            every = [ev_det[c][0] for c in ev_cats if ev_det.get(c)]
            if len(every) > 1:
                probes.append("本文討論 " + "、".join(every) + " 的邊界。\n")
            for body in probes:
                answer = ev.classify_domain(body)
                evidenced = ev.classify_domain_evidence(body)["domain"]
                if answer != evidenced:
                    errors.append(f"[Governance] classify_domain and "
                                  f"classify_domain_evidence disagree ({answer!r} vs "
                                  f"{evidenced!r}); the ambiguity report would describe a "
                                  f"different classification than the one that ships")
                    break

            # And the flags must not be dead. A winner resting on one keyword while a
            # lower-priority category hits several is exactly the case priority order
            # decides silently, so it is the case that must raise WEAK_WINNER.
            rival = next((c for c in ev_cats[1:] if len(ev_det.get(c, [])) >= 2), None)
            winner = next((c for c in ev_cats if ev_det.get(c)), None)
            if rival is None or winner is None or winner == rival:
                errors.append("[Governance] taxonomy.json cannot supply a contested probe; "
                              "the ambiguity flags cannot be verified")
            else:
                contested = (f"本文討論 {ev_det[winner][0]}，以及 "
                             f"{ev_det[rival][0]}、{ev_det[rival][1]} 的邊界。\n")
                got = ev.classify_domain_evidence(contested)
                if got["domain"] != winner or len(got["hits"]) < 2:
                    errors.append(f"[Governance] the contested probe did not come out "
                                  f"contested (domain {got['domain']!r}, "
                                  f"{len(got['hits'])} category hit(s)); the ambiguity "
                                  f"flags cannot be verified")
                else:
                    for flag in (ev.CONTESTED, ev.WEAK_WINNER):
                        if flag not in got["flags"]:
                            errors.append(f"[Governance] classify_domain_evidence did not raise "
                                          f"{flag} for a winner with {len(got['hits'][winner])} "
                                          f"keyword(s) against a loser with "
                                          f"{len(got['hits'][rival])}; an ambiguous "
                                          f"classification would reach the review gate silently")

            # SINGLE_HIT was the one flag never asserted, and the one most easily made
            # vacuous: evidence was counted per keyword, so a single stretch of text
            # matched by both `注意力` and `自我注意力` counted as two and the flag stayed
            # silent on a classification resting on one phrase. Two shapes are probed,
            # and the nested pair is found in taxonomy rather than named here.
            solo_cat = next((c for c in ev_cats if ev_det.get(c)), None)
            if solo_cat is None:
                errors.append("[Governance] taxonomy.json defines no detection keywords; "
                              "SINGLE_HIT cannot be verified")
            else:
                solo = ev.classify_domain_evidence(f"本文討論 {ev_det[solo_cat][0]} 的邊界。\n")
                if solo["domain"] != solo_cat or len(solo["hits"].get(solo_cat, [])) != 1:
                    errors.append(f"[Governance] the SINGLE_HIT probe did not resolve to one "
                                  f"hit on '{solo_cat}'; the flag cannot be verified")
                elif ev.SINGLE_HIT not in solo["flags"]:
                    errors.append("[Governance] classify_domain_evidence did not raise "
                                  "SINGLE_HIT for a winner resting on one keyword; a "
                                  "classification with no other evidence would reach the "
                                  "review gate looking corroborated")

            nested = next(((c, outer, inner)
                           for c, kws in ev_det.items()
                           for outer in kws for inner in kws
                           if inner != outer and inner.lower() in outer.lower()), None)
            if nested:
                cat_n, outer, inner = nested
                got_n = ev.classify_domain_evidence(f"本文討論{outer}的邊界。\n")
                if len(got_n["hits"].get(cat_n, [])) != 1:
                    errors.append(
                        f"[Governance] '{outer}' counted as "
                        f"{len(got_n['hits'].get(cat_n, []))} pieces of evidence because "
                        f"'{inner}' is a keyword inside it. One stretch of text is one "
                        f"occurrence; a match contained in a longer one is the same text "
                        f"read less specifically. Inflating the count is what silences "
                        f"SINGLE_HIT and skews the WEAK_WINNER comparison.")
                elif got_n["domain"] != cat_n:
                    errors.append(f"[Governance] the nested-keyword probe resolved to "
                                  f"'{got_n['domain']}' rather than '{cat_n}'; SINGLE_HIT "
                                  f"cannot be read off it")
                elif ev.SINGLE_HIT not in got_n["flags"]:
                    errors.append(f"[Governance] a body whose only evidence is '{outer}' did "
                                  f"not raise SINGLE_HIT")

        # The knowledge funnel must place evaluation before crystallization. §7.2 numbers
        # distill-knowledge as the first of three states, but §7's funnel once listed only
        # dialogue, crystallize and consolidate — so nothing in the funnel said that
        # crystallizing without evaluating first writes reports out of material already
        # judged too thin or belonging elsewhere. An ordering stated in one section and
        # not the other is an ordering an executor will skip.
        #
        # GUIDE is read here rather than borrowed from another check. A first version of
        # this block referenced a variable bound further down the method, so every branch
        # was skipped and all four falsifiers passed: an absent input made the check
        # vacuous while it still reported HEALTHY.
        guide_md_path = os.path.join(config.ROOT_DIR, "GUIDE.md")
        if not os.path.exists(guide_md_path):
            errors.append("[Governance] Missing GUIDE.md; the knowledge funnel and the "
                          "crystallization-report scope cannot be verified")
        else:
            with open(guide_md_path, 'r', encoding='utf-8-sig') as f:
                guide_md = f.read()

            funnel_lines = re.findall(r'^- \*\*第[一二三四五]級[：:].*$', guide_md, re.M)
            stages = [m.group(1) for m in
                      (re.search(r'`([a-z][a-z-]+)`', ln) for ln in funnel_lines) if m]
            if not funnel_lines:
                errors.append("[Governance] Cannot locate GUIDE's 知識漏斗 levels; the "
                              "evaluation-before-crystallization order cannot be verified")
            elif "distill-knowledge" not in stages:
                errors.append(f"[Governance] GUIDE's 知識漏斗 does not name "
                              f"`distill-knowledge` as a level (found {stages}); §7.2 "
                              f"numbers it the first of the three states, and a funnel that "
                              f"omits it lets crystallization run on unevaluated material.")
            elif "crystallize-report" in stages and \
                    stages.index("distill-knowledge") > stages.index("crystallize-report"):
                errors.append(f"[Governance] GUIDE's 知識漏斗 places `crystallize-report` "
                              f"before `distill-knowledge` ({stages}); evaluation is the "
                              f"precondition, not a later refinement.")

            # And §10.2 must not demand a crystallization report for the material that
            # crystallize-report refuses to crystallize. That workflow's first stage
            # forbids crystallizing governance material and routes it to
            # calibrate-guidelines; while §10.2 also required a report for 治理規則
            # changes, the two pointed one change at opposite processes and whichever an
            # executor read first won.
            cr_path = os.path.join(config.AGENT_DIR, "workflows", "crystallize-report.md")
            if not os.path.exists(cr_path):
                errors.append("[Governance] Missing .agent/workflows/crystallize-report.md")
            else:
                with open(cr_path, 'r', encoding='utf-8-sig') as f:
                    cr_src = f.read()
                demand = re.search(r'^- \*\*架構級變更\*\*[：:](.*)$', guide_md, re.M)
                if "禁止執行結晶" not in cr_src or "治理" not in cr_src:
                    errors.append("[Governance] crystallize-report.md no longer forbids "
                                  "crystallizing governance material; GUIDE §10.2's "
                                  "exclusion now rests on nothing and the pair must be "
                                  "re-decided together")
                elif not demand:
                    errors.append("[Governance] Cannot locate GUIDE's 架構級變更 "
                                  "requirement; the crystallization-report scope cannot "
                                  "be verified")
                elif "治理" in demand.group(1):
                    errors.append("[Governance] GUIDE §10.2 requires a crystallization "
                                  "report for 治理 changes, which crystallize-report.md's "
                                  "first stage forbids crystallizing and routes to "
                                  "calibrate-guidelines. Two rules pointing one change at "
                                  "opposite processes resolve by whichever an executor "
                                  "reads first.")

        # The ignore file and the guideline must name the same protected directories.
        # GUIDE defers the operative list to `.antigravityignore` ("被列入
        # .antigravityignore 的目錄") while separately declaring absolute protection for
        # named directories, so the two can drift apart in either direction: a directory
        # added to the ignore file that no rule explains, or a directory declared
        # untouchable that the ignore file never covers. Both failures are silent, and
        # the second is the dangerous one — the declaration reads as enforced when the
        # mechanism carrying it does not list the path.
        ignore_path = os.path.join(config.ROOT_DIR, ".antigravityignore")
        guide_path = os.path.join(config.ROOT_DIR, "GUIDE.md")
        if not os.path.exists(ignore_path):
            errors.append("[Governance] Missing .antigravityignore; GUIDE defers the "
                          "protected-directory list to it")
        elif not os.path.exists(guide_path):
            errors.append("[Governance] Missing GUIDE.md; the protected-directory "
                          "declarations have no source")
        else:
            with open(ignore_path, 'r', encoding='utf-8-sig') as f:
                ignored = {ln.strip() for ln in f
                           if ln.strip() and not ln.lstrip().startswith("#")}
            with open(guide_path, 'r', encoding='utf-8-sig') as f:
                guide_src = f.read()

            # The absolute-protection block, bounded by its own heading bullet and the
            # next bullet at the same indent. Located rather than assumed: a renamed
            # heading must report itself, not silently match nothing.
            block = re.search(r'^- \*\*目錄保護絕對規則.*?$(.*?)(?=^- \*\*)',
                              guide_src, re.S | re.M)
            if not block:
                errors.append("[Governance] Cannot locate GUIDE's 目錄保護絕對規則 block; "
                              "the protected-directory agreement cannot be verified")
            else:
                declared = {t for t in re.findall(r'`([^`]+/)`', block.group(1))}
                if not declared:
                    errors.append("[Governance] GUIDE's 目錄保護絕對規則 block names no "
                                  "directory; the ignore list has nothing to agree with")
                undeclared = sorted(ignored - declared)
                unenforced = sorted(declared - ignored)
                if undeclared:
                    errors.append(f"[Governance] .antigravityignore protects {undeclared} "
                                  f"but GUIDE's 目錄保護絕對規則 does not declare them; an "
                                  f"agent excluding a path for no stated reason cannot tell "
                                  f"a boundary from an accident.")
                if unenforced:
                    errors.append(f"[Governance] GUIDE declares {unenforced} absolutely "
                                  f"protected but .antigravityignore does not list them; the "
                                  f"declaration reads as enforced while the mechanism GUIDE "
                                  f"defers to omits the path.")

        # Category order decides the domain and the first hit wins. That is a settled
        # decision rather than an artefact: AI 經濟與社會 precedes AI 代理人 so that a
        # specific reading beats a broad one even on a single keyword, and the posts it
        # was decided for are the ones a weighted or threshold scheme would invert.
        # Ambiguity is surfaced instead (classify_domain_evidence flags it) precisely so
        # that nobody needs to re-decide this to make a close call visible.
        #
        # Pinned by running the classifier: a lower-priority category carrying strictly
        # more keywords must still lose. Reading the source cannot carry this — a
        # weighting could be introduced anywhere in the scan without changing its shape.
        try:
            from infra.taxonomy import TaxonomyEngine as _OrderEngine
        except ImportError as exc:
            errors.append(f"[Governance] Cannot import TaxonomyEngine to verify category "
                          f"priority: {exc}")
        else:
            order_engine = _OrderEngine()
            order_tax = order_engine.data.get("ai_taxonomy", {})
            order_cats = order_tax.get("categories", [])
            order_det = order_tax.get("detection_keywords", {})
            first = next((c for c in order_cats if order_det.get(c)), None)
            if first is None:
                errors.append("[Governance] taxonomy.json defines no detection keywords; "
                              "category priority cannot be verified")
            else:
                own = {k.lower() for k in order_det[first]}
                # A rival later in the order whose keywords are its own, so the hit counts
                # below mean what they say.
                rival = next((c for c in order_cats[order_cats.index(first) + 1:]
                              if len([k for k in order_det.get(c, [])
                                      if k.lower() not in own]) >= 3), None)
                if rival is None:
                    errors.append("[Governance] taxonomy.json offers no lower-priority "
                                  "category with three distinct keywords; category "
                                  "priority cannot be verified")
                else:
                    weak = order_det[first][0]
                    strong = [k for k in order_det[rival] if k.lower() not in own][:3]
                    body = f"本文討論 {weak}，以及 {'、'.join(strong)} 的邊界。\n"
                    seen = order_engine.classify_domain_evidence(body)
                    if len(seen["hits"].get(first, [])) != 1 or len(seen["hits"].get(rival, [])) < 3:
                        errors.append(f"[Governance] the priority probe did not come out "
                                      f"lopsided ({len(seen['hits'].get(first, []))} vs "
                                      f"{len(seen['hits'].get(rival, []))} hits); category "
                                      f"priority cannot be verified")
                    elif seen["domain"] != first:
                        errors.append(
                            f"[Governance] classification is no longer decided by category "
                            f"priority: '{rival}' won on {len(seen['hits'][rival])} keyword(s) "
                            f"over '{first}' on {len(seen['hits'][first])}. First hit in "
                            f"taxonomy.json order wins by decision, so that a specific reading "
                            f"beats a broad one; a weighted or threshold scheme inverts the "
                            f"posts that decision was made for. Surface a close call through "
                            f"classify_domain_evidence's flags instead of re-deciding it.")

        # Tag truncation must announce itself. TAG_SCAN_LIMIT and TAG_CAP both discard
        # candidates, and a post whose curated terms outnumber the cap used to ship with
        # some of them missing and nothing saying which — the same silence as the genre
        # fallback and the coerced domain, in the one place where the loss is invisible
        # because the surviving tags all look deliberate.
        #
        # Asserted by assembling a post over the cap and reading what it printed. Both
        # directions: over the cap must report, under the cap must stay silent, or a
        # check satisfied by logging unconditionally would prove nothing.
        try:
            from domain.post.assembler import PostAssembler as _TagAssembler
        except ImportError as exc:
            errors.append(f"[Governance] Cannot import PostAssembler to verify tag "
                          f"truncation reporting: {exc}")
        else:
            class _TagStub:
                def __init__(self):
                    self.body = ""
                    self.metadata = {}

            tag_lex = Lexicon(self.terminology_path)
            genre_scope = next((en for en in tag_lex.taxonomy.get("genres", {})
                                if " " in en), "")
            tag_base = {"ai_info": {"generation": {"scope": genre_scope}}}
            genre_values = {v for v in tag_lex.taxonomy.get("genres", {}).values()}
            # Categories are stored as `中文 (English)` while lexicon keys are the bare
            # Chinese, so comparing the two shapes excluded nothing: AI 經濟與社會 is a
            # category and also a lexicon term, and it was reaching the pool. Harmless
            # only because the probe body classifies to None and no domain tag is there
            # to dedupe against — the precondition this set exists to establish was
            # simply not established. Compared on the bare form now.
            ai_values = {re.sub(r'\s*[(（].*?[)）]', '', c).strip()
                         for c in tag_lex.taxonomy.get("ai_taxonomy", {}).get("categories", [])}
            # Real lexicon terms, so anchoring succeeds; none of them a genre or domain
            # value, which the assembler drops as deduplication rather than as loss.
            pool = [str(k) for k in tag_lex.mapping
                    if str(k) not in genre_values and str(k) not in ai_values]

            if len(pool) <= config.TAG_CAP:
                errors.append(f"[Governance] the lexicon holds too few anchorable terms "
                              f"({len(pool)}) to exceed TAG_CAP ({config.TAG_CAP}); tag "
                              f"truncation reporting cannot be verified")
            else:
                def assemble_tags(term_count):
                    """Returns (tags, captured output, error message or None)."""
                    buf = io.StringIO()
                    meta = dict(tag_base, tags=pool[:term_count])
                    # Both streams, because the assertion below must test whether the
                    # loss is reported at all and not which stream carries it. Every
                    # sibling loss in the pipeline is raised to stderr (the genre
                    # fallback in tag_anchor and prepare_handoff), so a truncation
                    # report correctly moved there would read here as no report at
                    # all — and this check would pin in place the under-reporting it
                    # exists to catch.
                    # Reported, not raised, as at every sibling probe in this method.
                    # with_tags raises on a tag whose English form yields an empty key,
                    # and this block sits ahead of the category-default scan, the
                    # series-naming guard and the four-way genre reconciliation — all in
                    # this same method. An escaping exception would abort them and hand
                    # back a traceback in place of the governance errors they exist to
                    # produce, so one bad lexicon entry would quietly disable the rest of
                    # the gate.
                    try:
                        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
                            built = _TagAssembler(_TagStub()).with_tags(meta, tag_lex)
                    except Exception as exc:
                        return [], buf.getvalue(), str(exc)
                    return built._tags, buf.getvalue(), None

                over_tags, over_log, over_err = assemble_tags(config.TAG_CAP + 4)
                under_tags, under_log, under_err = assemble_tags(1)
                probe_err = over_err or under_err
                if probe_err:
                    errors.append(f"[Governance] cannot assemble tags to verify tag "
                                  f"truncation reporting: {probe_err}")
                elif "[TAGS DROPPED]" not in over_log:
                    errors.append(f"[Governance] assembling {config.TAG_CAP + 4} anchorable "
                                  f"tags kept only {len(over_tags)} and reported nothing; "
                                  f"candidates discarded at TAG_SCAN_LIMIT or TAG_CAP must "
                                  f"be named, or a post silently loses curated terms.")
                elif len(over_tags) > config.TAG_CAP:
                    errors.append(f"[Governance] tag assembly emitted {len(over_tags)} tags, "
                                  f"over TAG_CAP ({config.TAG_CAP})")

                if not probe_err and "[TAGS DROPPED]" in under_log:
                    errors.append(f"[Governance] tag assembly reported a drop for a post "
                                  f"with one tag and {len(under_tags)} emitted; an "
                                  f"unconditional report would make the check above "
                                  f"meaningless.")

                # And each discarded candidate must be named, not summarised. The
                # report once listed five and closed with an ellipsis, so a post over
                # the cap by more than five lost curated terms that nothing anywhere
                # identified — the same silence this reporting exists to break, moved
                # past the fifth name. Sized to overflow that former limit, and the
                # overflow is confirmed before the naming is asserted so the check
                # cannot pass by being vacuous.
                span = config.TAG_CAP + 6
                if len(pool) < span:
                    errors.append(f"[Governance] the lexicon holds too few anchorable terms "
                                  f"({len(pool)}) to overflow the tag cap by more than five; "
                                  f"per-candidate naming cannot be verified")
                else:
                    many_tags, many_log, many_err = assemble_tags(span)
                    discarded = span - max(len(many_tags) - 1, 0)
                    named = sum(1 for t in pool[:span] if t in many_log)
                    if many_err:
                        errors.append(f"[Governance] cannot assemble tags to verify "
                                      f"per-candidate naming: {many_err}")
                    elif discarded <= 5:
                        errors.append(f"[Governance] the per-candidate naming probe discarded "
                                      f"only {discarded} candidate(s); it cannot distinguish "
                                      f"full naming from a list truncated at five")
                    elif named <= 5:
                        errors.append(f"[Governance] tag assembly discarded {discarded} "
                                      f"candidates and named {named} of them; every candidate "
                                      f"dropped at TAG_SCAN_LIMIT or TAG_CAP must be reported "
                                      f"one by one, not summarised with a count.")

        # taxonomy.json is the SSOT for the AI category list and its order, which
        # classify_domain depends on (first hit wins, deepest first). A hardcoded
        # fallback default is a second definition free to drift: one such default
        # still listed three categories after the file held five. Mentioning a
        # category in prose is fine; supplying a list of them as a default is not.
        # Matched on the parse tree, so splitting the call across lines does not evade it.
        #
        # Walked repo-wide rather than under SCRIPTS_DIR. The commitment binds scripts,
        # and lexicon-core/scripts sits outside that tree while reading the category
        # list itself — so a copy planted there was exempt from the guard meant to stop
        # exactly that. The scope now matches the whitespace gate above, which has no
        # tree to get wrong.
        for py_path in self.iter_repo_files(extensions=(".py",)):
            with open(py_path, 'r', encoding='utf-8-sig') as f:
                py_src = f.read()
            try:
                tree = ast.parse(py_src)
            except SyntaxError as exc:
                errors.append(f"[Governance] Cannot parse {self.rel(py_path)}: {exc}")
                continue
            for node in ast.walk(tree):
                if not (isinstance(node, ast.Call) and self._called_name(node) == "get"):
                    continue
                if len(node.args) < 2:
                    continue
                key, default = node.args[0], node.args[1]
                if not (isinstance(key, ast.Constant) and key.value == "categories"):
                    continue
                if isinstance(default, (ast.List, ast.Tuple, ast.Set)) and default.elts:
                    errors.append(f"[Governance] Hardcoded AI category list as a default; "
                                  f"taxonomy.json owns the category list and order: "
                                  f"{self.rel(py_path)}:{node.lineno}")

        # Series naming has one SSOT: init-handoff.task.schema.yaml's
        # `[核心主題]：[敘事化副標題]`. taxonomy.json owns tag/domain classification and
        # directory naming, never a mandatory series prefix.
        #
        # Scope of this check: prose cannot be gated semantically, and this does not
        # claim to catch every way a document could reassign the SSOT. It is two
        # concrete guards — the dead phrasings that were actually found here must not
        # return, and the clause must keep citing the schema it defers to. A rewrite
        # that reassigns the SSOT in new words needs a human reading, which is what
        # calibrate-guidelines is for.
        dead_prefix_phrasings = re.compile(r'\[領域前綴\]|系列前綴必須依')
        schema_citation = "init-handoff.task.schema.yaml"
        for gov_path in (os.path.join(config.ROOT_DIR, "GUIDE.md"),
                         os.path.join(config.REFERENCE_DIR, "agent-operating-guideline.md")):
            if not os.path.exists(gov_path):
                continue
            with open(gov_path, 'r', encoding='utf-8') as f:
                gov_text = f.read()
            if dead_prefix_phrasings.search(gov_text):
                errors.append(f"[Governance] {self.rel(gov_path)} mandates a taxonomy domain prefix for "
                              f"series names; the series naming SSOT is {schema_citation}")
            if "系列命名" in gov_text and schema_citation not in gov_text:
                errors.append(f"[Governance] {self.rel(gov_path)} states a series naming rule without "
                              f"citing {schema_citation}, which owns the format")

        # Genre is tags[0] on every post, and four projections describe the same set:
        # taxonomy.json's canonical `中文 (English)` genres (the tag SSOT, GUIDE §0) and
        # their slug aliases, the Structure line the report template offers an author,
        # and the `structures:` definitions saying what each genre must contain. All
        # four have drifted at some point — the schema named 分析論文 and 技術隨筆 where
        # taxonomy says 分析論述 and 技術筆記, and taxonomy offered a 案例研究 that no
        # structure defined. A genre is real only when every projection agrees.
        #
        # Each projection is extracted unconditionally and an empty one is a finding.
        # Guarding the comparisons behind `if projection:` is how two of these rules
        # previously passed a repo that had deleted the thing being audited.
        schema_path = os.path.join(config.AGENT_DIR, "schemas", "crystallize-report.schema.yaml")
        # Read the JSON SSOT directly; load_taxonomy() parses taxonomy.md, which is a
        # read-only view and must never be treated as the source.
        genres = {}
        if not os.path.exists(config.TAXONOMY_JSON):
            errors.append("[Governance] Missing taxonomy.json; genre has no source of truth")
        else:
            with open(config.TAXONOMY_JSON, 'r', encoding='utf-8') as f:
                try:
                    genres = json.load(f).get("genres", {})
                except json.JSONDecodeError as exc:
                    errors.append(f"[Governance] Invalid taxonomy JSON: {exc}")

        canonical = {en: zh for en, zh in genres.items() if " " in en}
        aliases = {en: zh for en, zh in genres.items() if " " not in en}
        schema_text = ""
        if not os.path.exists(schema_path):
            errors.append(f"[Governance] Missing report schema {self.rel(schema_path)}; the genre "
                          f"set cannot be reconciled against taxonomy.json")
        else:
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema_text = f.read()

        defined = {}
        for zh, en in re.findall(r'^[ \t]*name:\s*"([^"(]+?)\s*\(([^)"]+)\)"', schema_text, re.MULTILINE):
            defined[en.strip()] = zh.strip()
        offered = set()
        offered_match = re.search(r'\*\*Structure\*\*:.*?從\s*(.+?)\s*中擇一', schema_text)
        if offered_match:
            offered = {g.strip() for g in offered_match.group(1).split("/") if g.strip()}

        if not genres:
            errors.append("[Governance] taxonomy.json defines no `genres`; genre is tags[0] on "
                          "every post and has no source of truth")
        if genres and not canonical:
            errors.append("[Governance] taxonomy.json `genres` has no canonical `中文 (English)` "
                          "entries; only slug aliases were found")
        if schema_text and not offered:
            errors.append(f"[Governance] {self.rel(schema_path)} has no **Structure** line offering "
                          f"a genre choice; an author is given nothing to declare")
        if schema_text and not defined:
            errors.append(f"[Governance] {self.rel(schema_path)} defines no genre `structures:`; "
                          f"no genre says what it must contain")

        # TagAnchorer folds canonical names and slug aliases into one map keyed by
        # camel_key, and taxonomy.json lists the aliases second, so an alias silently
        # overrides the canonical display at runtime. A single wrong alias value
        # retags every post of that genre, with nothing in the data looking wrong.
        # Each canonical genre therefore needs exactly its own slug, carrying the
        # identical display.
        expected_aliases = {en.lower().replace(" ", "-"): (en, zh) for en, zh in canonical.items()}
        for slug, (en, zh) in sorted(expected_aliases.items()):
            if slug not in aliases:
                errors.append(f"[Governance] taxonomy.json genre '{en}' has no '{slug}' alias; "
                              f"slug-keyed lookups would miss it")
            elif aliases[slug] != zh:
                errors.append(f"[Governance] taxonomy.json genre alias '{slug}' displays as "
                              f"'{aliases[slug]}' but canonical '{en}' says '{zh}'; the alias wins "
                              f"at runtime and would retag every post of this genre")
        for stray in sorted(set(aliases) - set(expected_aliases)):
            errors.append(f"[Governance] taxonomy.json has genre alias '{stray}' with no canonical "
                          f"`中文 (English)` entry behind it")

        # The remaining comparisons are unconditional: an empty projection is already
        # reported above, and comparing against it surfaces the same drift again rather
        # than hiding it.
        for en, zh in sorted(defined.items()):
            expected = canonical.get(en)
            if expected and expected != zh:
                errors.append(f"[Governance] {self.rel(schema_path)} names genre '{en}' as "
                              f"'{zh}' but taxonomy.json says '{expected}'")
        for missing in sorted(set(canonical) - offered):
            errors.append(f"[Governance] taxonomy.json defines genre '{missing}' but "
                          f"{self.rel(schema_path)} does not offer it in **Structure**")
        for extra in sorted(offered - set(canonical)):
            errors.append(f"[Governance] {self.rel(schema_path)} offers genre '{extra}' in "
                          f"**Structure** but taxonomy.json does not define it")
        for undefined in sorted(set(canonical) - set(defined)):
            errors.append(f"[Governance] genre '{undefined}' is offerable but has no "
                          f"`structures:` definition in {self.rel(schema_path)}")
        for orphan in sorted(set(defined) - set(canonical)):
            errors.append(f"[Governance] {self.rel(schema_path)} defines genre '{orphan}' but "
                          f"taxonomy.json does not list it")

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
