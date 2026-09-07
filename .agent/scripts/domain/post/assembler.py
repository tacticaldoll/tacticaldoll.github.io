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

    def _resolve_domain_tag(self, post_meta, lexicon, body_content):
        """Returns the post's AI domain, from the handoff if it named one, else from the
        classifier — reporting the evidence when the classifier had to decide."""
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
        if domain_tag in ai_categories:
            return domain_tag

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
        #
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
        return domain_tag

    def _harvest_candidates(self, post_meta, lexicon, body_content, dedupe_against):
        """Returns the tag candidates in the order they should survive the cap: the
        author's curated tags first, then terms found in the body."""
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
        # Level 3 is the IGNORE_LIST (GUIDE §3.2): generic vocabulary kept in the lexicon
        # for the Chinese-usage safeguard, and never a tag — anchor_by_display drops it.
        # Harvesting it anyway spent scan budget on candidates that could not become
        # tags, pushed eligible terms past TAG_SCAN_LIMIT, and put 錯誤 / 差異 / 行為 into
        # the discard report of every post as though something had been lost.
        sorted_terms = sorted(
            (str(k) for k in lexicon.mapping.keys() if lexicon.levels.get(str(k), 1) < 3),
            key=len, reverse=True)
        for zh in sorted_terms:
            if zh in body_content:
                is_substring = any(zh in h for h in harvested_tags)
                if not is_substring:
                    clean_zh = self._get_clean_tag(zh)
                    if clean_zh in structural_names:
                        continue
                    if clean_zh not in dedupe_against:
                        harvested_tags.append(zh)

        # Level 1 terms are the ones §3.2 says are extracted preferentially. The harvest
        # above found them in length order, which stands proxy for nothing: at the cap a
        # Level 1 term lost its slot to longer Level 2 terms — 假設空間, 校準, 條件數 and
        # 感受野 were all discarded while Level 2 terms shipped. Sorted by level, stably,
        # so length still breaks ties within a level. Curated tags stay ahead of the
        # harvest either way: an author's choice outranks a substring match.
        harvested_tags.sort(key=lambda zh: lexicon.levels.get(zh, 1))
        return valid_user_tags + [t for t in harvested_tags if t not in valid_user_tags]

    def _anchor_domain(self, domain_tag, lexicon):
        """Returns the domain as a (display, key) tag, or None. The key is the lexicon's
        own, because that key is the identity reanchor rewrites tags by."""
        if not domain_tag:
            return None
        # Resolve on the bare form. The category strings carry a parenthetical —
        # `大型語言模型 (LLM)` — which the lexicon does not key on, so lookup on the
        # full string has always missed and every domain tag was keyed off the
        # parenthetical instead. That agreed with the lexicon only by coincidence of
        # the English wording: `(Machine Learning)` camel-cases to MachineLearning,
        # which is the key, but `(LLM)` gives Llm where the lexicon says
        # LargeLanguageModel. A tag whose key the lexicon cannot resolve is dropped
        # by reanchor as an orphan, so the coincidence was load-bearing — and it held
        # only because no post had ever carried the 大型語言模型 domain.
        bare_domain = re.sub(r'\s*[(（].*?[)）]', '', domain_tag).strip()
        domain_res = lexicon.lookup(domain_tag) or lexicon.lookup(bare_domain)
        if domain_res and domain_res["status"] == "standard":
            return (domain_res["zh"], domain_res.get("key", ""))

        ai_tax = lexicon.taxonomy.get("ai_taxonomy", {})
        detection = ai_tax.get("detection_keywords", {})
        ai_categories = ai_tax.get("categories", [])
        if domain_tag not in detection and domain_tag not in ai_categories:
            return None
        match = re.search(r'\((.*?)\)', domain_tag)
        if not match:
            return (domain_tag, "AIDomain")
        fallback_key = "".join(w.capitalize() for w in re.findall(r'[a-zA-Z0-9]+', match.group(1)))
        clean_display = re.sub(r'\s*[(（].*?[)）]', '', domain_tag).strip()
        return (clean_display, fallback_key)

    def _apply_tag_limits(self, final_tags, tech_tags, anchorer, lexicon, dedupe_against):
        """Appends candidates to final_tags within TAG_SCAN_LIMIT and TAG_CAP, naming
        every candidate the limits discard."""
        # Both limits discard candidates, and both used to do it in silence: a post
        # whose curated terms outnumbered the cap shipped with some of them missing
        # and nothing anywhere saying which. Duplicates and collisions with the genre
        # or domain tag are not losses — they are deduplication — so they stay quiet.
        # Truncation is a loss and is reported on the loss channel: log_error, the
        # same stderr the genre fallback uses, because a run that watches stdout for
        # narration and stderr for problems must not have to read the narration to
        # find out that curated terms were discarded.
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
                if lexicon.levels.get(t, 1) >= 3:
                    # The IGNORE_LIST doing its job. Not a loss, so not reported — the
                    # same exemption deduplication has. A curated tag can land here if
                    # the handoff named a generic term.
                    continue
                dropped.append(f"{t} (not in the lexicon; /init-handoff must lock a term "
                               f"before it can be anchored as a tag)")
                continue
            if not anchored[1]:
                raise ValueError(f"Tag '{t}' generated an empty key. An English translation is required.")

            clean_anchored = self._get_clean_tag(anchored[0])
            if clean_anchored in dedupe_against:
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
        return final_tags

    def with_tags(self, post_meta, lexicon):
        """Synthesizes Genre, Domain, user-defined tech tags, and auto-harvests tags from body."""
        from domain.terminology.tag_anchor import TagAnchorer
        anchorer = TagAnchorer(lexicon)
        # Read the body once, so the fallback classification and the term harvest cannot
        # end up reading different text.
        body_content = self.post.body if hasattr(self.post, 'body') else ""

        structure_tag, structure_key = self._get_structure_tag(post_meta, anchorer)
        domain_tag = self._resolve_domain_tag(post_meta, lexicon, body_content)
        # Genre and domain occupy the first slots, so a candidate matching either is a
        # duplicate rather than a loss, and the discard report stays quiet about it.
        dedupe_against = [self._get_clean_tag(structure_tag), self._get_clean_tag(domain_tag)]

        tech_tags = self._harvest_candidates(post_meta, lexicon, body_content, dedupe_against)

        final_tags = [(structure_tag, structure_key)]
        anchored_domain = self._anchor_domain(domain_tag, lexicon)
        if anchored_domain:
            final_tags.append(anchored_domain)

        self._tags = self._apply_tag_limits(final_tags, tech_tags, anchorer, lexicon,
                                            dedupe_against)
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
