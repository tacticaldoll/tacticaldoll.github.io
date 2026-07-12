import re

class TerminologyInjector:
    """Handles terminology anchoring and glossary injection into post text."""
    
    def apply_lexicon(self, post, lexicon, mode="anchor_first"):
        """
        Applies terminology rules from a Lexicon to the post body.
        Handles paragraph-based processing, code block protection, and anchor injection.
        Modifies post.body directly.
        """
        if not post.body:
            return False

        # Globally remove standalone terminology definition boxes (including mutated/legacy ones)
        # to ensure perfect idempotency before processing paragraphs. Each generated box line
        # carries a <!-- term:/anchor: --> marker; requiring it prevents deleting author-written
        # [!IMPORTANT] callouts that merely start with bold text.
        body = re.sub(r'[\r\n]+>\s*\[!IMPORTANT\]\r?\n(?:>\s*\*\*.*?\*\*[^\r\n]*<!--\s*(?:anchor|term):[^\r\n]*(?:\r?\n)?)+', '', post.body)

        # 1. Temporarily extract/protect code blocks
        code_blocks = []
        def code_replacer(match):
            code_blocks.append(match.group(0))
            return f"__CODE_BLOCK_{len(code_blocks)-1}__"
        
        protected_body = re.sub(r'^```[\s\S]*?^```', code_replacer, body, flags=re.MULTILINE)
        
        def comment_replacer(match):
            comment = match.group(0)
            # Keep the <!--more--> separator literal so split_by_more can isolate the preview
            # area below; otherwise it gets placeholder-ized here, the split sees nothing, and
            # the whole body (summary included) is anchored — violating GUIDE §5.111.
            if comment == "<!--more-->":
                return comment
            # In remove_all or anchor_first mode, we want to clean up anchors, so do not protect them.
            if mode in ["remove_all", "anchor_first"] and re.search(r'<!--\s*(?:anchor|term):', comment):
                return comment
            code_blocks.append(comment)
            return f"__CODE_BLOCK_{len(code_blocks)-1}__"
            
        protected_body = re.sub(r'<!--[\s\S]*?-->', comment_replacer, protected_body)

        # If in anchor_first mode, first perform a complete cleanup on protected body to ensure idempotency
        if mode == "anchor_first":
            sorted_zh = sorted(lexicon.mapping.keys(), key=len, reverse=True)
            cleanup_pattern = re.compile(
                r'([\*_]{1,2})?(' + '|'.join(re.escape(z) for z in sorted_zh) + r')([\*_]{1,2})?' +
                r'(?:[ \t]*[\(（].*?[\)）])?' + 
                r'(?:[ \t]*<!--\s*(?:anchor|term):.*?\s*-->)?'
            )
            def cleaner(m):
                pre = m.group(1) or ""
                zh = m.group(2)
                post_val = m.group(3) or ""
                # De-anchoring must also drop the bold it once added. A standalone
                # **L3term** is orphan first-occurrence bold left when the term was
                # demoted to level 3 (IGNORE_LIST) — level-3 terms are never anchored,
                # so that emphasis is residue. Strip ONLY when the term is bolded as a
                # symmetric standalone unit (same marker on both sides); if it is merely
                # the edge of a longer author bold (one side only), leave it intact.
                if pre and pre == post_val and lexicon.levels.get(zh, 1) >= 3:
                    return zh
                return f"{pre}{zh}{post_val}"
            protected_body = cleanup_pattern.sub(cleaner, protected_body)
            # Sweep orphan anchors left by terms removed/archived from the lexicon: their ZH is
            # no longer a key, so the term-driven cleanup above misses them. Marker-driven, so it
            # clears the inline comment plus an attached （bilingual） while keeping the ZH text.
            protected_body = re.sub(r'(?:[ \t]*[\(（][^\r\n]*?[\)）])?[ \t]*<!--\s*(?:anchor|term):.*?-->', '', protected_body)

        # 2. Split by <!--more--> to protect preview area from heavy anchoring
        had_more = "<!--more-->" in protected_body
        preview_area, main_body = post.split_by_more(protected_body)
        
        # 3. Process main body paragraphs
        blocks = re.split(r'(\n\s*\n)', main_body)
        processed_blocks = []
        found_globally = set()
        first_use_terms = []

        for block in blocks:
            if not block.strip():
                processed_blocks.append(block)
                continue
            
            processed_block, newly_anchored = self._process_paragraph(block, lexicon, mode, found_globally, first_use_terms)
            processed_blocks.append(processed_block)

        # 4. Preview Area: Only forbidden replacements, no anchors
        if preview_area:
            preview_area, _ = self._process_paragraph(preview_area, lexicon, "remove_all", set(), [])

        # 5. Reassemble body (re-insert the separator iff the original had one, so an
        #    empty summary does not silently drop <!--more-->).
        new_body = (preview_area + "<!--more-->" if had_more else "") + "".join(processed_blocks)

        # Programmatic stable solution: Clean up nested bold quotes and align term tags consistently inside quotes
        new_body = re.sub(
            r'\*\*「\*\*([^\n*?]+?)\*\*([ \t]*<!-- term:[a-zA-Z0-9_-]+ -->)?[ \t]*」\*\*',
            lambda m: f"「**{m.group(1)}**{m.group(2) or ''}」",
            new_body
        )
        new_body = re.sub(
            r'「\*\*([^\n*?]+?)\*\*」[ \t]*(<!-- term:[a-zA-Z0-9_-]+ -->)',
            lambda m: f"「**{m.group(1)}** {m.group(2)}」",
            new_body
        )

        for i, cb in enumerate(code_blocks):
            new_body = new_body.replace(f"__CODE_BLOCK_{i}__", cb)
            
        post.body = new_body
        return True

    def _process_paragraph(self, block, lexicon, mode, found_globally, first_use_terms):
        """Internal helper to process a single paragraph using lexicon regex."""
        if not lexicon.terms_regex and mode != "remove_all":
            return block, []

        header_lines = []
        other_lines = []
        
        # Protection logic from Rules
        generic_headers = lexicon.rules.get("de_bilingual_headers", [])
        generic_pattern = re.compile(r'^(#+[ \t]+(?:' + '|'.join(generic_headers) + r'))[ \t]*[(（].*?[)）]')
        protected_patterns = lexicon.rules.get("markdown_anchors", {}).get("protected_alert_patterns", [])

        for line in block.splitlines(True):
            if re.match(r'^#+[ \t]+', line):
                line = generic_pattern.sub(r'\1', line)
                header_lines.append(line)
            elif any(re.match(p, line) for p in protected_patterns):
                header_lines.append(line)
            else:
                other_lines.append(line)
                
        if not other_lines:
            return "".join(header_lines), []

        text = "".join(other_lines)
        newly_anchored_info = []

        # Forbidden Replacement (Always)
        if lexicon.forbidden_regex:
            text = lexicon.forbidden_regex.sub(lambda m: lexicon.forbidden[m.group(0)], text)

        if mode == "remove_all":
            # 1. First remove standalone terminology definition boxes (including mutated/legacy ones).
            #    Require the <!-- term:/anchor: --> marker so author-written [!IMPORTANT] callouts survive.
            text = re.sub(r'[\r\n]+>\s*\[!IMPORTANT\]\r?\n(?:>\s*\*\*.*?\*\*[^\r\n]*<!--\s*(?:anchor|term):[^\r\n]*(?:\r?\n)?)+', '', text)

            # 2. Strip all (EN) anchors and inline comments
            sorted_zh = sorted(lexicon.mapping.keys(), key=len, reverse=True)
            cleanup_pattern = re.compile(
                r'([\*_]{1,2})?(' + '|'.join(re.escape(z) for z in sorted_zh) + r')([\*_]{1,2})?' +
                r'(?:[ \t]*[\(（].*?[\)）])?' + 
                r'(?:[ \t]*<!--\s*(?:anchor|term):.*?\s*-->)?'
            )
            def cleaner(m):
                pre = m.group(1) or ""
                zh = m.group(2)
                post_val = m.group(3) or ""
                # Same as the anchor_first path: drop orphan standalone **L3term** bold
                # (level-3 terms are never anchored, so the emphasis is de-anchor residue).
                # Symmetric markers only, to avoid breaking a longer author bold span.
                if pre and pre == post_val and lexicon.levels.get(zh, 1) >= 3:
                    return zh
                return f"{pre}{zh}{post_val}"

            text = cleanup_pattern.sub(cleaner, text)
            # Sweep orphan anchors of removed/archived terms (marker-driven; see anchor_first path).
            text = re.sub(r'(?:[ \t]*[\(（][^\r\n]*?[\)）])?[ \t]*<!--\s*(?:anchor|term):.*?-->', '', text)
            return "".join(header_lines) + text, []

        # 2. Anchoring Logic
        patterns = []
        for zh in lexicon.mapping.keys():
            # Only level<3 terms participate in anchoring. Level-3 (IGNORE_LIST) generic
            # words (發現/自動化/數據…) are never anchored anyway; including their zh here
            # only lets them greedily consume the ** of an ADJACENT term's bold —
            # "發現**受污染**" → 發現 eats the "**", the real term re-bolds →
            # "發現****受污染**" — which breaks reanchor idempotency. Exclude them.
            if lexicon.levels.get(zh, 1) < 3:
                patterns.append(re.escape(zh))
                for en in lexicon.zh_to_ens.get(zh, []):
                    if len(en) > 3 or en.lower() == "react":
                        # Word-boundary the ASCII alias so "Spec" cannot anchor INSIDE
                        # "OpenSpec"/"Specialists"/"specs/". Bare substring matching here
                        # was the root cause of systematic English-word corruption on
                        # every reanchor. CJK zh above need no boundary.
                        patterns.append(r'\b' + re.escape(en) + r'\b')
        
        patterns.sort(key=len, reverse=True)
        
        anchor_regex = re.compile(
             r'([\*_]{2})?(' + '|'.join(patterns) + r')([\*_]{2})?' +
             r'(?:[ \t]*[\(（].*?[\)）])?' + 
             r'(?:[ \t]*<!--\s*(?:anchor|term):.*?\s*-->)?'
        )

        def replacer(match):
            pre, matched_text, post_val = match.group(1) or "", match.group(2), match.group(3) or ""
            
            # Resolve to primary ZH
            zh = lexicon.en_to_zh.get(matched_text.lower(), matched_text)
            
            is_first = zh not in found_globally
            level = lexicon.levels.get(zh, 1)
            en_primary = lexicon.mapping.get(zh, "Unknown")
            key_val = lexicon.keys.get(zh) if hasattr(lexicon, 'keys') else zh
            if not key_val:
                key_val = zh
                
            clean_zh = re.sub(r'\s*[\(（].*?[\)）]\s*', '', zh).strip()
            clean_en = re.sub(r'^[\(（]+|[\)）]+$', '', en_primary.strip()) if en_primary else ""
            
            if mode == "anchor_first" and is_first and level < 3:
                found_globally.add(zh)
                first_use_terms.append(zh)
                newly_anchored_info.append({
                    "zh": clean_zh, 
                    "en": clean_en,
                    "description": lexicon.descriptions.get(zh, ""),
                    "key": key_val
                })
                return f"**{clean_zh}**（{clean_en}） <!-- term:{key_val} -->"
            
            if level < 3:
                return f"{pre}{clean_zh}{post_val} <!-- term:{key_val} -->"
            return f"{pre}{clean_zh}{post_val}"
   
        text = anchor_regex.sub(replacer, text)
        
        # 3. Append IMPORTANT block if there are new anchors
        if newly_anchored_info:
            anchor_lines = []
            for item in newly_anchored_info:
                key_val = item.get("key") or item["zh"]
                line = f"> **{item['zh']}** <!-- term:{key_val} --> ({item['en']})"
                if item["description"]:
                    line += f": {item['description']}"
                line += f" <!-- anchor:{key_val} -->"
                anchor_lines.append(line)
            
            important_block = "\n> [!IMPORTANT]\n" + "\n".join(anchor_lines)
            
            m = re.search(r'\s*$', text)
            trailing = m.group(0) if m else ""
            text = text[:len(text)-len(trailing)].rstrip() + "\n" + important_block + "\n" + trailing.lstrip('\n')

        return "".join(header_lines) + text, [item['zh'] for item in newly_anchored_info]

    def remove_all_anchors(self, post, lexicon):
        """Restores post to pure zero-anchor state."""
        return self.apply_lexicon(post, lexicon, mode="remove_all")
