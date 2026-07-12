## Authored by Schema: .agent/schemas/handoff.posts.schema.yaml, .agent/schemas/handoff.terms.schema.yaml
## Reference Spec: .agent/reference/agent-operating-guideline.md
"""Stage 0.5 Handoff scanner.

Consumes a session directory and the NLP-authored handoff files, then fills
script-managed scan fields such as existing/discovered/forbidden terms and
derived taxonomy data. This module does not write NLP term descriptions, invent
article intent, or publish posts; those decisions remain in /init-handoff and
the final consumer remains pipeline.py.
"""

import os
import sys
import re
import json
import glob
import copy
from datetime import datetime, timedelta
from typing import Any, Dict

# Add scripts root to path
scripts_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if scripts_root not in sys.path:
    sys.path.append(scripts_root)

from domain.terminology.engine import TerminologyEngine
from infra.utils import normalize_path, log_info, log_error
from infra.taxonomy import TaxonomyEngine
from infra import config

class HandoffPreparer:
    def __init__(self, session_id):
        self.session_id = session_id
        self.handoff: Dict[str, Any] = {}
        self.root_dir = config.ROOT_DIR
        self.scratch_dir = os.path.join(self.root_dir, ".agent-scratch", session_id)
        self.taxonomy_path = config.TAXONOMY_MD
        self.term_json_path = config.TERMINOLOGY_JSON
        
        
        if not os.path.exists(self.scratch_dir):
            raise FileNotFoundError(f"Session directory not found: {self.scratch_dir}")
            
        self.engine = TerminologyEngine(self.term_json_path)
        self.tax_engine = TaxonomyEngine()
        
        self.terms_handoff_path = os.path.join(self.scratch_dir, "handoff.terms.json")
        self.posts_handoff_path = os.path.join(self.scratch_dir, "handoff.posts.json")
        # 1. Selection logic: scratch (specific) > root (broad Stage 0 Stage 0 manual input)
        load_path = None
        # Priority: scratch
        p_scratch = self.posts_handoff_path
        if os.path.exists(p_scratch):
            load_path = p_scratch
        else:
            # Priority: root (Stage 0 manual input)
            p_root = os.path.join(self.root_dir, "handoff.posts.json")
            if os.path.exists(p_root):
                try:
                    with open(p_root, 'r', encoding='utf-8') as f:
                        root_data = json.load(f)
                        if root_data.get("session_id") == session_id:
                            load_path = p_root
                        else:
                            log_info(f"Ignoring stale root handoff.posts.json (session_id mismatch: {root_data.get('session_id')} vs {session_id})")
                except Exception as e:
                    log_info(f"Failed to read root handoff.posts.json: {e}")
                
        if load_path:
            with open(load_path, 'r', encoding='utf-8') as f:
                self.handoff = json.load(f)
            
            # Merge terms if they are in a separate file
            if os.path.exists(self.terms_handoff_path):
                with open(self.terms_handoff_path, 'r', encoding='utf-8') as f:
                    terms_data = json.load(f)
                    self.handoff["terms"] = terms_data.get("terms", {})
            
            # Ensure required keys exist and are of correct type
            if "status" not in self.handoff: self.handoff["status"] = "initiated"
            if "terms" not in self.handoff or not isinstance(self.handoff["terms"], dict): self.handoff["terms"] = {}
            if "existing" not in self.handoff["terms"]: self.handoff["terms"]["existing"] = []
            if "discovered" not in self.handoff["terms"]: self.handoff["terms"]["discovered"] = []
            if "declared" not in self.handoff["terms"]: self.handoff["terms"]["declared"] = []
            if "locked" not in self.handoff["terms"]: self.handoff["terms"]["locked"] = []
            if "forbidden_found" not in self.handoff["terms"]: self.handoff["terms"]["forbidden_found"] = []
            if "rules" not in self.handoff or not isinstance(self.handoff["rules"], dict): self.handoff["rules"] = {"headers": {}, "redactions": {}, "sublimations": {}}
            if "sublimations" not in self.handoff["rules"]: self.handoff["rules"]["sublimations"] = {}
            if "metadata" not in self.handoff or not isinstance(self.handoff["metadata"], dict): self.handoff["metadata"] = {"series": None, "is_series": False, "posts": []}
            self.handoff["prepared_at"] = datetime.now().isoformat()
        else:
            self.handoff = {
                "session_id": session_id,
                "prepared_at": datetime.now().isoformat(),
                "status": "initiated",
                "metadata": {
                    "series": None,
                    "is_series": False,
                    "posts": []
                },
                "terms": {
                    "declared": [],
                    "existing": [],
                    "discovered": [],
                    "forbidden_found": [],
                    "locked": []
                },
                "rules": {
                    "headers": {},
                    "redactions": {},
                    "sublimations": {}
                }
            }
        
        # Default session date from ID
        date_match = re.match(r'(\d{4}-\d{2}-\d{2})', session_id)
        if date_match:
            self.session_date = f"{date_match.group(1)}T11:00:00+08:00"
        else:
            self.session_date = datetime.now().strftime('%Y-%m-%dT11:00:00+08:00')
        self.handoff["metadata"]["date"] = self.session_date

        # Internal cache for report-specific metadata and rules
        self.report_ai_info = {}
        self.report_dates = {}
        self.report_redactions = {}
        self.taxonomy_headers = {}

    def load_taxonomy_rules(self):
        """Extracts standard headers and domain tags from taxonomy.md."""
        if not os.path.exists(self.taxonomy_path):
            return
            
        with open(self.taxonomy_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Parse Generic Headers table
        header_table = re.findall(r'^\|\s*(.*?)\s*\|\s*\*\*(.*?)\*\*\s*\|', content, re.MULTILINE)
        for variants, standard in header_table:
            for v in variants.split('` / `'):
                v_clean = v.strip('` ')
                self.taxonomy_headers[v_clean] = standard

        # Parse Domain Tags (Slugs to ZH)
        tag_matches = re.findall(r'- `(.*?)`: (.*)', content)
        for slug, zh in tag_matches:
            # We don't store them all, just use them to identify terms in content
            pass

    def scan_reports(self):
        """Scans selected reports in the session for terms and context (prioritizing zh)."""
        # Ensure exact idempotency: clear derived lists before scanning
        self.handoff["terms"]["discovered"] = []
        self.handoff["terms"]["existing"] = []
        self.handoff["terms"]["forbidden_found"] = []
        
        # Gather target reports (one per directory bundle)
        target_reports = []
        subdirs = sorted([d for d in os.listdir(self.scratch_dir) if os.path.isdir(os.path.join(self.scratch_dir, d))])
        for d in subdirs:
            report_files = sorted(glob.glob(os.path.join(self.scratch_dir, d, "report.*.md")))
            if report_files:
                zh_reports = [f for f in report_files if 'zh' in os.path.basename(f).lower()]
                target_reports.append(zh_reports[0] if zh_reports else report_files[0])
                

        
        for rf in target_reports:
            with open(rf, 'r', encoding='utf-8') as f:
                content = f.read()

            # Anchor the publish time to the report's own **Date** header (to the
            # minute). The seconds slot is reserved for sort ordering (see
            # _calculate_post_date); falls back to session_date when absent.
            date_m = re.search(r'^\s*\*\*Date\*\*:\s*(.*)', content[:1000], re.MULTILINE)
            if date_m and date_m.group(1).strip():
                self.report_dates[rf] = date_m.group(1).strip()

            # 0. Extract Generation Metadata (if found at the top)
            # Pattern: **Key**: Value
            meta_patterns = {
                "model": re.compile(r'^\s*\*\*Model\*\*:\s*(.*)', re.MULTILINE),
                "agent": re.compile(r'^\s*\*\*Agent\*\*:\s*(.*)', re.MULTILINE),
                "scope": re.compile(r'^\s*\*\*Structure\*\*:\s*(.*)', re.MULTILINE),
                "tags": re.compile(r'^\s*\*\*Tags\*\*:\s*(.*)', re.MULTILINE),
                "description": re.compile(r'^\s*\*\*Description\*\*:\s*(.*)', re.MULTILINE)
            }
            
            # Store metadata for this specific report
            self.report_ai_info[rf] = {"generation": {"scope": "Technical Note", "model": "Unknown", "agent": "Unknown"}}
            gen_info = self.report_ai_info[rf]["generation"]
            
            for key, pattern in meta_patterns.items():
                match = pattern.search(content[:1000]) # Only look at start of file
                if match:
                    gen_info[key] = match.group(1).strip()

            # Strip markdown code blocks before processing to prevent false positives
            content_no_code = re.sub(r'```[\s\S]*?```', '', content)

            # 1. Discover New Terms (Patterns: **ZH** or ZH (EN))
            bilingual_pattern = re.compile(r'([\u4e00-\u9fa5]{2,})\s*[\(（]([a-zA-Z\s\-/]+)[\)）]')
            bold_pattern = re.compile(r'\*\*(.*?)\*\*')
            
            def is_valid_term(text, context_after="", is_bilingual=False):
                # 1. Length constraint
                # Bilingual (ZH (EN)) can be slightly longer, but bold-only should be tight terms.
                # [REDUCED] Long strings are usually sentence fragments
                max_len = 10
                if len(text) < 2 or len(text) > max_len:
                    return False
                
                # 2. Punctuation/Noise check
                if re.search(r'[?.,!?:]', text):
                    return False
                
                # 3. Logical/Grammar Noise starts
                noise_starts = []
                if any(text.startswith(ns) for ns in noise_starts):
                    return False

                # 4. Metadata key check (trailing colon in context)
                if context_after.lstrip().startswith(':'):
                    return False
                
                # 5. Excluded common metadata/formatting keywords
                excluded = {"Structure", "Date", "Model", "Agent", "Source", "Tags", "Description", "Summary", "Note", "Example", "Caution", "Warning", "Important", "Tip", "Standalone Post"}
                if text in excluded:
                    return False
                
                # 6. Must contain Chinese and not be a long sentence
                if not re.search(r'[\u4e00-\u9fa5]', text):
                    return False
                
                # 7. Refined noise filtering for residue prevention
                # Exclude strings that look like sentences or have common non-terminology particles
                if len(text) > 4 and any(p in text for p in []):
                    return False
                
                return True


            # Find all potential bilingual terms
            for zh, en in bilingual_pattern.findall(content_no_code):
                if not is_valid_term(zh, is_bilingual=True): continue
                res = self.engine.lookup(zh)
                if not res:
                    if zh not in [d["zh"] for d in self.handoff["terms"]["discovered"]]:
                        # Normalize English to Title Case for project consistency
                        en_title = en.strip().title()
                        self.handoff["terms"]["discovered"].append({
                            "zh": zh, 
                            "en": [en_title], 
                            "source": rf,
                            "type": "bilingual",
                            "confidence": "high"
                        })
                elif res["status"] == "forbidden":
                    self.handoff["terms"]["forbidden_found"].append({"term": zh, "correction": res["correction"]})
            
            # Find all bold terms that might be new
            for match in bold_pattern.finditer(content_no_code):
                term = match.group(1).strip()
                context_after = content_no_code[match.end():match.end()+1]
                
                if not is_valid_term(term, context_after, is_bilingual=False):
                    continue
                
                res = self.engine.lookup(term)
                if not res:
                    # Check if already added via bilingual scan
                    if term not in [d["zh"] for d in self.handoff["terms"]["discovered"]]:
                        self.handoff["terms"]["discovered"].append({
                            "zh": term, 
                            "source": rf,
                            "type": "bold",
                            "confidence": "medium"
                        })
                elif res["status"] == "forbidden":
                    if term not in [f["term"] for f in self.handoff["terms"]["forbidden_found"]]:
                        self.handoff["terms"]["forbidden_found"].append({"term": term, "correction": res["correction"]})
                else:
                    if term not in self.handoff["terms"]["existing"]:
                        self.handoff["terms"]["existing"].append(term)

            # 2. Extract Redaction Targets (Internal scripts, paths)
            self.report_redactions[rf] = []
            internal_paths = re.findall(r'`(\.agent/scripts/.*?)`', content)
            for path in internal_paths:
                if path not in self.report_redactions[rf]:
                    self.report_redactions[rf].append(path)

    def harvest_metadata_terms(self):
        """Root-cause supplement to the bilingual/bold scanner.

        scan_reports() only catches `中文(EN)` pairs and **bold** spans, so reports
        that never mark up terminology (common for externally-generated drafts)
        yield zero candidates and silently ship with new flagship terms missing
        from the lexicon. Series authors, however, DO curate per-report `tags` in
        the `## Metadata` TOML of series-map.md / guide.md. Harvest those as
        high-confidence 'tag' candidates so refine_handoff promotes them to
        locked (PENDING_REFINEMENT for new terms, synced for known ones). Must run
        AFTER scan_reports() because that method clears the discovered list."""
        sources = (sorted(glob.glob(os.path.join(self.scratch_dir, "series-map*.md")))
                   + sorted(glob.glob(os.path.join(self.scratch_dir, "guide*.md"))))
        if not sources:
            return

        seen = {d["zh"] for d in self.handoff["terms"]["discovered"]}
        seen |= set(self.handoff["terms"]["existing"])
        seen |= {l.get("zh") for l in self.handoff["terms"]["locked"] if isinstance(l, dict)}

        harvested = []
        for src in sources:
            try:
                with open(src, 'r', encoding='utf-8') as f:
                    content = f.read()
            except Exception as e:
                log_error(f"Failed to read metadata source {src}: {e}")
                continue

            # Parse `tags = ["...", "..."]` TOML arrays; tolerate single quotes.
            for arr in re.findall(r'tags\s*=\s*\[([^\]]*)\]', content):
                for q1, q2 in re.findall(r'"([^"]+)"|\'([^\']+)\'', arr):
                    term = (q1 or q2).strip()
                    # Keep pure CJK nouns within a sane length; refine's
                    # is_obvious_junk handles the finer fragment filtering.
                    if not term or not re.search(r'[一-龥]', term):
                        continue
                    if len(term) < 2 or len(term) > 12:
                        continue
                    if term in seen:
                        continue
                    res = self.engine.lookup(term)
                    if res and res["status"] == "forbidden":
                        continue
                    seen.add(term)
                    self.handoff["terms"]["discovered"].append({
                        "zh": term,
                        "source": src,
                        "type": "tag",
                        "confidence": "high"
                    })
                    harvested.append(term)

        if harvested:
            log_info(f"  [METADATA HARVEST] {len(harvested)} curated term(s) from "
                     f"series-map/guide: {', '.join(harvested)}")

    def _detect_domain(self, content):
        """Delegates domain detection to the centralized TaxonomyEngine."""
        return self.tax_engine.classify_domain(content)

    def _sanitize_text(self, text):
        """Replaces forbidden terms in text using the lexicon engine."""
        if not text: return text
        return self.engine.replace_forbidden(text)

    def _detect_tags(self, content):
        """Detects technical tags from content using the lexicon."""
        tags = []
        # Find all Level 1 terms in the body
        body_text = content
        lexicon = self.engine.lexicon
        for zh in lexicon.mapping:
            if lexicon.levels.get(zh, 1) < 3:
                if zh in body_text:
                    tags.append(zh)
        
        # Deduplicate and sort by appearance
        tags = sorted(list(set(tags)), key=lambda x: body_text.find(x))[:5]
        return tags

    def _calculate_post_date(self, basis_date_str, index):
        """Anchors to the basis date's minute and writes `index` into the seconds
        slot to lock per-session sort order. Tolerates report headers that omit
        seconds and/or timezone (e.g. '2026-03-28T17:45')."""
        try:
            clean_date = basis_date_str.strip().replace('Z', '+08:00')
            # Normalize to YYYY-MM-DDTHH:MM:SS<tz> so fromisoformat accepts it and
            # the seconds slot is ours to control.
            m = re.match(r'^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2})(?::\d{2})?(?:\.\d+)?(.*)$', clean_date)
            if m:
                tz = m.group(2).strip() or '+08:00'
                clean_date = f"{m.group(1)}:00{tz}"
            dt = datetime.fromisoformat(clean_date)
            dt = dt.replace(second=0, microsecond=0) + timedelta(seconds=index)
            return dt.isoformat()
        except Exception:
            return basis_date_str

    def _refine_series(self, raw_title):
        if not raw_title: return raw_title
        
        generic_keywords = ["導讀", "介紹", "前言", "總覽"]
        if any(kw in raw_title for kw in generic_keywords) or raw_title.startswith("Session "):
            if self.handoff["metadata"]["posts"]:
                raw_title = self.handoff["metadata"]["posts"][0]["title"]
                
        return raw_title

    def determine_series_and_posts(self):
        """Determines series names and post structure."""
        guide_content = ""
        guide_files = glob.glob(os.path.join(self.scratch_dir, "guide*.md"))
        if guide_files:
            self.handoff["metadata"]["is_series"] = True
            log_info(f"  [SERIES DETECTED] Found guide file: {os.path.basename(guide_files[0])}")
            try:
                with open(guide_files[0], 'r', encoding='utf-8') as f:
                    guide_content = f.read()
                    # NLP Refinement for Series Title: Extract first H1
                    title_match = re.search(r'^#[ \t]*(.*)', guide_content, re.MULTILINE)
                    if title_match:
                        series_title = title_match.group(1).strip()
                        self.handoff["metadata"]["series"] = series_title
            except Exception as e:
                log_error(f"Failed to parse guide file: {e}")
        else:
            self.handoff["metadata"]["is_series"] = False
            self.handoff["metadata"]["series"] = None
            log_info("  [STANDALONE DETECTED] No guide file found. Standard single post mode.")

        found_posts = False
        subdirs = sorted([d for d in os.listdir(self.scratch_dir) if os.path.isdir(os.path.join(self.scratch_dir, d))])
        
        # Sort by appearance in guide_content if available, giving us narrative sequence
        if guide_content:
            subdirs_copy = list(subdirs)
            def _sort_by_guide(x):
                # Try to find the title inside the report of subdirectory x
                report_files = sorted(glob.glob(os.path.join(self.scratch_dir, x, "report.*.md")))
                title = x
                if report_files:
                    zh_reports = [f for f in report_files if 'zh' in os.path.basename(f).lower()]
                    selected_report = zh_reports[0] if zh_reports else report_files[0]
                    try:
                        with open(selected_report, 'r', encoding='utf-8') as f:
                            for line in f:
                                if line.strip().startswith('# '):
                                    title = line.strip()[2:].strip()
                                    break
                    except Exception:
                        pass
                
                # Try finding title first
                idx = guide_content.find(title)
                if idx == -1:
                    # Try finding directory name fallback
                    idx = guide_content.find(x)
                if idx == -1:
                    from infra.utils import log_info
                    log_info(f"  [SERIES ORDER WARNING] Subdir '{x}' (Title: '{title}') not found in guide.md. Falling back to default order.")
                    idx = len(guide_content) + subdirs_copy.index(x)
                return idx
            subdirs.sort(key=_sort_by_guide)
        
        def _extract_metadata(selected_report, slug, default_title, post_idx):
            title = default_title
            extracted_tags = []
            extracted_desc = ""
            domain_tag = None
            try:
                with open(selected_report, 'r', encoding='utf-8') as f:
                    report_content = f.read()
                    detected_domain = self._detect_domain(report_content)
                    if detected_domain:
                        domain_tag = detected_domain
                    
                    report_head = report_content[:2000]
                    for line in report_head.splitlines():
                        if line.strip().startswith('# '):
                            title = line.strip()[2:].strip()
                        elif '**Tags**:' in line:
                            tags_str = line.split('**Tags**:')[1].strip()
                            extracted_tags = [t.strip() for t in tags_str.split(',') if t.strip()]
                        elif '**Description**:' in line:
                            extracted_desc = line.split('**Description**:')[1].strip()
                        elif '**Summary**:' in line:
                            extracted_desc = line.split('**Summary**:')[1].strip()
                    
                    if not extracted_desc:
                        for para in report_head.split('\n\n'):
                            p = para.strip()
                            if not p or p.startswith(('#', '<', '<!--')): continue
                            if re.match(r'^\*\*.*?\*\*:', p): continue
                            extracted_desc = p.replace('\n', ' ')[:200]
                            break
            except Exception as e:
                log_error(f"Error extracting metadata from {selected_report}: {e}")
                
            title = self._sanitize_text(title)
            extracted_desc = self._sanitize_text(extracted_desc)
            
            if not extracted_tags:
                try:
                    with open(selected_report, 'r', encoding='utf-8') as f:
                        extracted_tags = self._detect_tags(f.read())
                except:
                    pass
            
            for t in extracted_tags:
                clean_t = re.sub(r'\s*[(（].*?[)）]', '', t).strip()
                res = self.engine.lookup(clean_t)
                if res and res["status"] == "standard":
                    existing_locked = {l["zh"] for l in self.handoff["terms"]["locked"]}
                    if res["zh"] not in existing_locked:
                        self.handoff["terms"]["locked"].append({
                            "zh": res["zh"],
                            "en": res["en"][0] if res["en"] else "Unknown",
                            "description": res.get("description") or "Refined during Handoff Tag Sync",
                            "level": res.get("level", 1)
                        })
                        log_info(f"  [LEXICON SYNC] Tag '{clean_t}' matched and promoted to locked terms.")
                else:
                    existing_zh = {d["zh"] for d in self.handoff["terms"]["discovered"]}
                    if clean_t not in existing_zh and clean_t not in {l["zh"] for l in self.handoff["terms"]["locked"]}:
                        self.handoff["terms"]["discovered"].append({
                            "zh": clean_t,
                            "source": selected_report,
                            "type": "tag",
                            "confidence": "high"
                        })
                        log_info(f"  [TAG DISCOVERY] Unrecognized tag '{clean_t}' funneled to discovered list for quality gate.")

            is_duplicate = False
            target_post = None
            for p in self.handoff["metadata"]["posts"]:
                if p.get("slug") == slug:
                    is_duplicate = True
                    target_post = p
                    break
                if p.get("report_rel") and p.get("report_rel").startswith(f"{slug}/") and slug != self.session_id:
                    is_duplicate = True
                    target_post = p
                    break
                    
            if not is_duplicate:
                post_data = {
                    "title": title,
                    "date": self._calculate_post_date(self.report_dates.get(selected_report, self.session_date), post_idx),
                    "slug": slug,
                    "report_rel": f"{slug}/{os.path.basename(selected_report)}" if slug != self.session_id else os.path.basename(selected_report),
                    "description": extracted_desc or "PENDING_NLP_DIGESTION",
                    "tags": extracted_tags if extracted_tags else ["PENDING_NLP_DIGESTION"],
                    "domain_tag": domain_tag if domain_tag else "",
                    "rules": {
                        "headers": copy.deepcopy(self.taxonomy_headers),
                        "redactions": {},
                        "sublimations": {}
                    }
                }
                if selected_report in self.report_ai_info:
                    post_data["ai_info"] = self.report_ai_info[selected_report]
                    
                self.handoff["metadata"]["posts"].append(post_data)
            else:
                if selected_report in self.report_ai_info and target_post is not None:
                    if "ai_info" not in target_post:
                        target_post["ai_info"] = {}
                    target_post["ai_info"]["generation"] = self.report_ai_info[selected_report].get("generation", {})

        for d in subdirs:
            report_files = sorted(glob.glob(os.path.join(self.scratch_dir, d, "report.*.md")))
            if report_files:
                found_posts = True
                slug = d
                default_title = slug.replace('-', ' ').title()
                zh_reports = [f for f in report_files if 'zh' in os.path.basename(f).lower()]
                selected_report = zh_reports[0] if zh_reports else report_files[0]
                post_idx = len(self.handoff["metadata"]["posts"]) + 1
                _extract_metadata(selected_report, slug, default_title, post_idx)

        # Final Refinement of Series Name
        if self.handoff["metadata"].get("is_series"):
            raw_series = self.handoff["metadata"].get("series")
            self.handoff["metadata"]["series"] = self._refine_series(raw_series)

    def lock_terms(self):
        """Creates a definitive list of valid terms to be anchored by the pipeline."""
        # Idempotency Protection: Load existing refined terms from disk if present
        existing_locked_map = {}
        if os.path.exists(self.terms_handoff_path):
            try:
                with open(self.terms_handoff_path, 'r', encoding='utf-8') as f:
                    old_data = json.load(f)
                    for l_item in old_data.get("terms", {}).get("locked", []):
                        if isinstance(l_item, dict) and "zh" in l_item:
                            existing_locked_map[l_item["zh"]] = l_item
            except Exception:
                pass

        self.handoff["terms"]["locked"] = []
        all_terms = set(self.handoff["terms"].get("existing", []))
        
        declared_map = {}
        for d in self.handoff["terms"].get("declared", []):
            if isinstance(d, dict) and "zh" in d:
                declared_map[d["zh"]] = d
                all_terms.add(d["zh"])
            elif isinstance(d, str):
                declared_map[d] = {"zh": d, "en": ""}
                all_terms.add(d)
        
        discovered_map = {}
        for d in self.handoff["terms"].get("discovered", []):
            discovered_map[d["zh"]] = d
            all_terms.add(d["zh"])
            
        for f in self.handoff["terms"].get("forbidden_found", []):
            all_terms.add(f["correction"])
            
        for t in all_terms:
            corrected_t = self.engine.replace_forbidden(t)
            
            # Idempotency Inheritance: If term was already locked and refined/modified, preserve it
            if corrected_t in existing_locked_map:
                if not any(l.get("zh") == corrected_t for l in self.handoff["terms"]["locked"]):
                    self.handoff["terms"]["locked"].append(existing_locked_map[corrected_t])
                continue

            res = self.engine.lookup(corrected_t)
            
            if res and res["status"] != "forbidden":
                if not any(l.get("zh") == res["zh"] for l in self.handoff["terms"]["locked"]):
                    en_list = res.get("en", [])
                    self.handoff["terms"]["locked"].append({
                        "zh": res["zh"],
                        "en": en_list[0] if isinstance(en_list, list) and en_list else (en_list if isinstance(en_list, str) else ""),
                        "level": res.get("level", 1)
                    })
            elif not res:
                # Local Snapshot Trust Logic for New Terms
                # [GATE] Only lock if description is NOT a placeholder (TODO/Residue)
                if t in declared_map:
                    item = declared_map[t]
                    en_str = item.get("en", "")
                    desc = item.get("description", "")
                    
                    if "TODO" in desc or "PENDING" in desc:
                        # Skip auto-locking for non-refined terms
                        continue
 
                    # Guard: Empty or missing description is unsafe
                    # auto-assign PENDING_REFINEMENT to prevent silent pass-through
                    if not desc or not desc.strip():
                        desc = "PENDING_REFINEMENT"

                    if isinstance(en_str, list) and en_str: en_str = en_str[0]
                    if isinstance(en_str, str) and en_str: en_str = en_str.strip().title()
                    
                    if not any(l.get("zh") == corrected_t for l in self.handoff["terms"]["locked"]):
                        self.handoff["terms"]["locked"].append({
                            "zh": corrected_t,
                            "en": en_str,
                            "level": 1,
                            "description": desc
                        })
                    # Discovered terms usually have default TODO descriptions, don't auto-lock
                    # They must be moved to 'declared' and refined first.
                    pass
 
        # [GATE] Auto-locking for discovered terms is disabled to ensure quality.
        # terms must be promoted to the global DB or manually locked with a refined description.
        pass

    def save(self):
        # Prepare two sections
        terms_data = {
            "session_id": self.session_id,
            "terms": self.handoff.get("terms", {})
        }
        posts_data = {
            "session_id": self.session_id,
            "prepared_at": self.handoff.get("prepared_at"),
            "status": self.handoff.get("status"),
            "metadata": self.handoff.get("metadata"),
            "rules": self.handoff.get("rules")
        }

        # Write to separate files
        with open(self.terms_handoff_path, 'w', encoding='utf-8') as f:
            json.dump(terms_data, f, indent=4, ensure_ascii=False)
        with open(self.posts_handoff_path, 'w', encoding='utf-8') as f:
            json.dump(posts_data, f, indent=4, ensure_ascii=False)
            
        print(f"SUCCESS: Handoff split created:")
        print(f"  - Terms: {self.terms_handoff_path}")
        print(f"  - Posts: {self.posts_handoff_path}")
        
        
        # Summary for AI
        remaining_discovered = [d for d in self.handoff["terms"]["discovered"] if d.get("confidence") != "high"]
        if remaining_discovered:
            print("\nWARNING: Discovered potential medium-confidence terms (Please check manually):")
            for d in remaining_discovered:
                print(f"  - {d['zh']} (Bold only)")

def main():
    parser = argparse.ArgumentParser(description="Stage 0.5: Handoff Preparation (Local Snapshot Builder)")
    parser.add_argument("session_id", help="Session ID to scan")
    
    args = parser.parse_args()
    
    preparer = HandoffPreparer(args.session_id)
    preparer.load_taxonomy_rules()
    preparer.scan_reports()
    preparer.harvest_metadata_terms()
    preparer.determine_series_and_posts()
    preparer.lock_terms()
    preparer.save()

if __name__ == "__main__":
    import argparse
    main()
