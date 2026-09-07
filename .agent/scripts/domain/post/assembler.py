## Authored by Schema: .agent/schemas/publish-article.task.schema.yaml
## Reference Workflow: .agent/workflows/publish-article.md

import os
import re
from datetime import datetime
from infra import config

class PostAssembler:
    """
    Builder pattern for assembling HugoPost metadata from handoff and system configurations.
    Encapsulates the procedural logic previously scattered across pipeline orchestrators.
    """
    def __init__(self, post):
        self.post = post
        self._title = "Untitled"
        self._desc = ""
        self._date = datetime.now().strftime('%Y-%m-%dT11:00:00+08:00')
        self._author = "Tactical Doll"
        self._tags = []
        self._ai_info = {}
        self._series = None
        self._is_series = False

    def with_base_meta(self, post_meta, handoff_meta=None):
        """Assembles Title, Description, Date, and Draft status."""
        self._title = post_meta.get("title", self.post.metadata.get("title", "Untitled"))
        self._desc = post_meta.get("description", self.post.metadata.get("description", ""))
        
        # Date resolution
        date_str = post_meta.get("date")
        if not date_str and handoff_meta:
            date_str = handoff_meta.get("date")
        if not date_str:
            date_str = datetime.now().strftime('%Y-%m-%dT11:00:00+08:00')
        self._date = date_str
        
        # Series
        if handoff_meta and handoff_meta.get("is_series"):
            self._is_series = True
            refined_series = handoff_meta.get("series")
            if refined_series:
                self._series = refined_series
                
        return self

    def with_author(self, hugo_toml_path):
        """Extracts the global author from Hugo config."""
        if os.path.exists(hugo_toml_path):
            with open(hugo_toml_path, 'r', encoding='utf-8') as tf:
                author_match = re.search(r'author\s*=\s*"(.*?)"', tf.read())
                if author_match:
                    self._author = author_match.group(1)
        return self

    def _get_structure_tag(self, post_meta, anchorer):
        """Resolves the genre/structure tag (tags[0]) from the post's scope via the
        taxonomy genre SSOT (shared TagAnchorer). Returns (display_zh, key)."""
        scope = post_meta.get("ai_info", {}).get("generation", {}).get("scope")
        # genre_tag announces every fallback, whether the scope is absent or simply
        # not a genre, so there is nothing to pre-validate here.
        return anchorer.genre_tag(scope or "", default_scope=config.GENRE_FALLBACK_SCOPE)

    def _get_clean_tag(self, tag):
        if not tag: return ""
        return re.sub(r'\s*[(（].*?[)）]', '', tag).strip().lower()

    def with_tags(self, post_meta, lexicon):
        """Synthesizes Genre, Domain, user-defined tech tags, and auto-harvests tags from body."""
        from domain.terminology.tag_anchor import TagAnchorer
        anchorer = TagAnchorer(lexicon)
        structure_tag, structure_key = self._get_structure_tag(post_meta, anchorer)
        # `AI` is itself one of taxonomy.json's categories, so defaulting to it made an
        # absent domain_tag look already-classified: the `not in ai_categories` guard
        # below was False and classification never ran. An absent tag must fall through
        # to the classifier.
        #
        # And the classifier's None must survive. TaxonomyEngine.classify_domain returns
        # None deliberately (Asymmetric Tagging) so a post with no AI subject matter
        # carries no AI domain tag; coercing it to "AI" here re-decided that policy at
        # the call site and silently cancelled it. Same shape as the provenance strip
        # that had to move into the engine rather than be remembered by every caller.
        # Both literals were also program-internal copies of a taxonomy category value,
        # which is the drift 7f958bf removed from classify_domain itself.
        domain_tag = post_meta.get("domain_tag") or ""
        ai_categories = lexicon.taxonomy.get("ai_taxonomy", {}).get("categories", [])
        # Read once, so the fallback classification below and the term harvest further
        # down cannot end up reading different text.
        body_content = self.post.body if hasattr(self.post, 'body') else ""

        if domain_tag not in ai_categories:
            from infra.taxonomy import TaxonomyEngine
            from infra.utils import log_error, log_info
            tax_engine = TaxonomyEngine()
            # No window. This is the fallback path — prepare_handoff already classified
            # the full report and wrote domain_tag, and classify_posts re-derives it the
            # same way — so a window here would classify on a different basis than the
            # authoritative path and hand the same post a different domain depending on
            # which caller reached it. The body is still pre-anchoring at this point
            # (with_tags runs before PostOrchestrator.cleanup), so no injected term
            # vocabulary can vote.
            # The evidence, not just the answer. prepare_handoff reports an ambiguous
            # classification while a human still holds the handoff, but this path is
            # reached only when that run wrote no domain_tag at all — so it is the one
            # classification nobody has looked at, and it was the last one still
            # deciding in silence. Same severity split as there: a winner the evidence
            # argues against interrupts, the rest is context.
            evidence = tax_engine.classify_domain_evidence(body_content)
            domain_tag = evidence["domain"] or ""
            if domain_tag and evidence["flags"]:
                report = (f"  [DOMAIN AMBIGUITY] {self._title}: {domain_tag} on "
                          f"{len(evidence['hits'][domain_tag])} keyword(s), "
                          f"{len(evidence['hits'])} category(ies) hit. "
                          f"Flags: {', '.join(evidence['flags'])}.")
                if tax_engine.WEAK_WINNER in evidence["flags"]:
                    log_error(report + " The evidence favours a category that lost on "
                                       "category priority; confirm the domain.")
                else:
                    log_info(report)

        clean_structure_tag = self._get_clean_tag(structure_tag)
        clean_domain_tag = self._get_clean_tag(domain_tag)

        # 1. Harvest valid user tags
        tech_tags_raw = post_meta.get("tags", [])
        if not isinstance(tech_tags_raw, list): tech_tags_raw = []
        
        valid_user_tags = []
        for t in tech_tags_raw:
            if not t or any(p in t for p in ["PENDING_NLP_DIGESTION", "TODO"]):
                continue
            valid_user_tags.append(t)
            
        # 2. Auto harvest standard terms from body
        # rules.de_bilingual_headers is the project's SSOT for generic SECTION names
        # (導言 / 反思 / 實務對比 ...). Some of them also exist as lexicon terms, so a
        # naive substring harvest turns a post's own structure into its topic tags and
        # crowds out the curated ones (tags cap at 8). Structure is not subject matter.
        structural_names = {
            self._get_clean_tag(h)
            for h in lexicon.rules.get("de_bilingual_headers", [])
            if h
        }
        harvested_tags = []
        sorted_terms = sorted([str(k) for k in lexicon.mapping.keys()], key=len, reverse=True)
        for zh in sorted_terms:
            if zh in body_content:
                is_substring = any(zh in h for h in harvested_tags)
                if not is_substring:
                    clean_zh = self._get_clean_tag(zh)
                    if clean_zh in structural_names:
                        continue
                    if clean_zh not in [clean_structure_tag, clean_domain_tag]:
                        harvested_tags.append(zh)
                        
        tech_tags = valid_user_tags + [t for t in harvested_tags if t not in valid_user_tags]
        
        # 3. Anchor Domain
        anchored_domain = None
        if domain_tag:
            domain_res = lexicon.lookup(domain_tag)
            if domain_res and domain_res["status"] == "standard":
                key = domain_res.get("key", "")
                en_primary = domain_res["en"][0] if domain_res.get("en") else None
                if en_primary and domain_res["zh"].lower() != en_primary.lower():
                    anchored_domain = (domain_res["zh"], key)
                else:
                    anchored_domain = (domain_res["zh"], key)
            else:
                ai_tax = lexicon.taxonomy.get("ai_taxonomy", {})
                detection = ai_tax.get("detection_keywords", {})
                if domain_tag in detection or domain_tag in ai_categories:
                    match = re.search(r'\((.*?)\)', domain_tag)
                    if match:
                        fallback_key = "".join(w.capitalize() for w in re.findall(r'[a-zA-Z0-9]+', match.group(1)))
                        clean_display = re.sub(r'\s*[(（].*?[)）]', '', domain_tag).strip()
                        anchored_domain = (clean_display, fallback_key)
                    else:
                        anchored_domain = (domain_tag, "AIDomain")

        # 4. Final Assembly
        final_tags = []
        
        # Structure (genre) tag: display + key resolved via the taxonomy SSOT (see _get_structure_tag).
        final_tags.append((structure_tag, structure_key))
        
        if anchored_domain:
            final_tags.append(anchored_domain)
        
        # Both limits below discard candidates, and both used to do it in silence: a
        # post whose curated terms outnumbered the cap shipped with some of them
        # missing and nothing anywhere saying which. Duplicates and collisions with
        # the genre or domain tag are not losses — they are deduplication — so they
        # stay quiet. Truncation is a loss and is reported on the loss channel:
        # log_error, the same stderr the genre fallback uses, because a run that
        # watches stdout for narration and stderr for problems must not have to
        # read the narration to find out that curated terms were discarded.
        from infra.utils import log_error
        scan = tech_tags[:config.TAG_SCAN_LIMIT]
        dropped = []
        if len(tech_tags) > len(scan):
            beyond = [t for t in tech_tags[len(scan):] if t and t != "TODO: Add tags"]
            if beyond:
                dropped.append(f"{len(beyond)} beyond the {config.TAG_SCAN_LIMIT}-candidate "
                               f"scan ({', '.join(beyond)})")

        for idx, t in enumerate(scan):
            if not t or t == "TODO: Add tags": continue
            anchored = anchorer.anchor_by_display(t)
            if not anchored:
                dropped.append(f"{t} (no lexicon anchor)")
                continue
            if not anchored[1]:
                raise ValueError(f"Tag '{t}' generated an empty key. An English translation is required.")
            
            clean_anchored = self._get_clean_tag(anchored[0])
            if clean_anchored in [clean_structure_tag, clean_domain_tag]:
                continue
                
            # Avoid duplicate tag values
            if not any(f[0] == anchored[0] for f in final_tags):
                final_tags.append(anchored)
                
            if len(final_tags) >= config.TAG_CAP:
                remaining = [x for x in scan[idx + 1:] if x and x != "TODO: Add tags"]
                if remaining:
                    dropped.append(f"{len(remaining)} at the {config.TAG_CAP}-tag cap "
                                   f"({', '.join(remaining)})")
                break

        if dropped:
            log_error(f"  [TAGS DROPPED] {self._title}: " + "; ".join(dropped))

        self._tags = final_tags
        return self

    def with_telemetry(self, post_meta):
        from infra.utils import format_model_id
        # Copy so popping does not mutate the shared handoff post_meta (it is
        # checkpointed back to disk and re-read on --mode finish retries).
        gen_info = dict(post_meta.get("ai_info", {}).get("generation", {}))
        gen_info.pop("tags", None)
        gen_info.pop("description", None)
        # scope is build-only: consumed by _get_structure_tag to derive the genre
        # tag (tags[0]); it is not persisted to the published front matter.
        gen_info.pop("scope", None)

        if "model" in gen_info:
            gen_info["model"] = format_model_id(gen_info["model"])

        ref_info = post_meta.get("ai_info", {}).get("refinement", {})

        self._ai_info = {
            "generation": gen_info
        }
        if ref_info:
            self._ai_info["refinement"] = ref_info
            
        return self

    def build(self):
        """Assembles all fields into the HugoPost metadata dictionary and returns it."""
        self.post.metadata = {
            "title": self._title,
            "date": self._date,
            "author": self._author,
            "draft": False,
            "isCJKLanguage": True,
            "description": self._desc,
            "tags": self._tags,
            "ai_info": self._ai_info
        }
        
        if self._is_series and self._series:
            self.post.metadata["series"] = [self._series]
            
        return self.post
