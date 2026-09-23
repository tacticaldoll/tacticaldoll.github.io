import re

# Machine-generated definition callouts: an [!IMPORTANT] header followed only by
# marker-bearing definition lines. Author callouts carry no marker and must not
# match. The leading newlines are consumed deliberately: the append step re-emits
# them, so eating them here is what makes a second pass a no-op. Re-emitting a
# blank line instead accumulates two newlines per round.
_RM_ANCHOR_BLOCK = re.compile(
    r'[\r\n]+>[ \t]*\[!IMPORTANT\]\r?\n'
    r'(?:>[ \t]*\*\*.*?\*\*[^\r\n]*<!--[ \t]*(?:anchor|term):[^\r\n]*(?:\r?\n)?)+'
)


# De-anchoring is the inverse of anchoring and has to agree with it about whose
# brackets these are. It removes the gloss ONLY when the bracket holds exactly one of
# this term's aliases — the same test the anchoring side applies. Anything else is the
# author's （NAS）or（Effective Receptive Field, ERF）, and eating it means a reanchor
# deletes text nobody asked it to touch: the anchor side kept it, so the round trip has
# to as well. The span is also bounded away from a second bracket and from a table pipe.
# With an unbounded `.*?` a "parenthetical" could start at `(Seeds)` in a table row's
# first cell and run to a marker near the row's end, taking every cell between them —
# which is exactly what collapsed one row to `| **3. 種子規格。 |`.
_ANCHOR_TAIL = (r'(?:(?:[ \t]*([\(（][^()（）|\r\n]*[\)）]))?'
                r'[ \t]*<!--\s*(?:anchor|term):.*?\s*-->)?')

# Orphan sweep: terms removed from the lexicon leave a marker the term-driven cleanup
# can no longer find. Their gloss is machine output and always plain ASCII, so keep the
# bracket class that tight rather than letting it reach across author text.
_ORPHAN_SWEEP = re.compile(r"(?:[ \t]*[\(（][A-Za-z0-9 ,./&'\-]*[\)）])?"
                           r'[ \t]*<!--\s*(?:anchor|term):.*?-->')

# Runs after the term-driven cleanup, so a marker still here belongs to a renamed or
# removed term and the bold it carried is first-occurrence residue, as for L3 demotion.
_ORPHAN_BOLD = re.compile(r"\*\*([^*\n]+?)\*\*(?=(?:[ \t]*[\(（][A-Za-z0-9 ,./&'\-]*[\)）])?"
                          r'[ \t]*<!--\s*(?:anchor|term):)')


_MERMAID_FENCE = re.compile(r'^```mermaid[^\n]*\n[\s\S]*?^```', re.MULTILINE)


def correct_mermaid_fences(body, lexicon):
    """Corrects variant spellings inside mermaid fences, whose labels render as prose.

    Every other fence stays verbatim, and nothing is anchored here: a marker inside a
    diagram would render as literal text.
    """
    if not body or not lexicon.forbidden_regex:
        return body
    return _MERMAID_FENCE.sub(
        lambda m: lexicon.forbidden_regex.sub(lambda f: lexicon.forbidden[f.group(0)], m.group(0)),
        body)


def _build_deanchor(lexicon):
    """Returns (pattern, cleaner) stripping a machine anchor back to its bare term."""
    sorted_zh = sorted(lexicon.mapping.keys(), key=len, reverse=True)
    pattern = re.compile(
        r'([\*_]{1,2})?(' + '|'.join(re.escape(z) for z in sorted_zh) + r')([\*_]{1,2})?'
        + _ANCHOR_TAIL)

    def cleaner(m):
        pre, zh, post_val = m.group(1) or "", m.group(2), m.group(3) or ""
        paren = m.group(4) or ""
        aliases = {a.strip().lower() for a in lexicon.zh_to_ens.get(zh, []) if a}
        kept = "" if paren and paren[1:-1].strip().lower() in aliases else paren
        # A standalone **L3term** is orphan first-occurrence bold left when the term was
        # demoted to level 3 (IGNORE_LIST): level-3 terms are never anchored, so that
        # emphasis is residue. Symmetric markers only — one-sided means it is the edge of
        # a longer author bold span.
        if pre and pre == post_val and lexicon.levels.get(zh, 1) >= 3:
            return zh + kept
        return f"{pre}{zh}{post_val}{kept}"

    return pattern, cleaner


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
        body = _RM_ANCHOR_BLOCK.sub('', post.body)
        body = correct_mermaid_fences(body, lexicon)

        # 1. Temporarily extract/protect code blocks
        code_blocks = []
        def code_replacer(match):
            code_blocks.append(match.group(0))
            return f"__CODE_BLOCK_{len(code_blocks)-1}__"
        
        protected_body = re.sub(r'^```[\s\S]*?^```', code_replacer, body, flags=re.MULTILINE)

        # Inline code is not prose either. A zh key is matched by plain substring and an EN
        # alias is only word-boundaried, so both fire inside a `...` span that quotes verbatim
        # tool output. The rustc diagnostic `no method named 'deploy' found for struct
        # 'Spec<Ungated>'` came back out as 'Spec' rewritten to '**約束性規格**（Spec）
        # <!-- term:Spec -->' — the quoted error text is then falsified, and because Hugo does
        # not process comments inside a code span the marker also renders as literal text.
        # This runs directly after the fence sweep, so any backtick pair left here is genuinely
        # inline, and a link or formula nested inside a span is protected as one unit rather
        # than as a placeholder inside a placeholder, which the flat restore loop cannot undo.
        protected_body = re.sub(r'`[^`\n]+`', code_replacer, protected_body)

        # Math is not prose. The zh keys below are matched by plain substring, so a term
        # appearing inside \text{…} gets an anchor comment injected into the formula:
        #   \text{條件機率序列生成器 <!-- term:Foo -->} = x
        # which corrupts the LaTeX. BlockProtector guards the assembly path this way;
        # apply_lexicon is reached directly by reanchor.py, which bypasses that path, so
        # the same guard has to exist here. Display math first, then single-line inline
        # math, matching BlockProtector's order.
        protected_body = re.sub(r'\$\$[\s\S]*?\$\$', code_replacer, protected_body)
        protected_body = re.sub(r'(?<!\$)\$(?!\$)[^\n$]+?\$(?!\$)', code_replacer, protected_body)

        # A citation is not prose either. An EN alias is word-boundaried but that only
        # stops matches INSIDE a word, not a legitimate standalone one, so the alias
        # matched inside the English title of a cited paper and rewrote it to the
        # Chinese term: 《Controlling the 假發現率: A Practical …》 and 《Understanding
        # the Effective 感受野 in Deep …》. The work's title is what makes the citation
        # checkable — rewriting it is a falsified reference, and reanchor cannot undo it
        # because the English words are no longer in the file. The URL goes with the
        # label for the same reason: a path segment is not prose. Labels with nested
        # brackets are left alone rather than mis-split.
        protected_body = re.sub(r'!?\[[^\]\n]*\]\([^()\s]*(?:[ \t]+"[^"\n]*")?\)',
                                code_replacer, protected_body)

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
            cleanup_pattern, cleaner = _build_deanchor(lexicon)
            protected_body = cleanup_pattern.sub(cleaner, protected_body)
            protected_body = _ORPHAN_BOLD.sub(r'\1', protected_body)
            protected_body = _ORPHAN_SWEEP.sub('', protected_body)

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

        # Protected lines are held in place by a placeholder instead of being hoisted.
        # Emitting them first reordered the block: a heading that followed a paragraph
        # came out in front of it and, when it was the block's last line and carried no
        # newline, glued to the paragraph's first character.
        protected_map = {}
        seq = []
        for line in block.splitlines(True):
            keep = None
            if re.match(r'^#+[ \t]+', line):
                keep = generic_pattern.sub(r'\1', line)
            elif any(re.match(p, line) for p in protected_patterns):
                keep = line
            if keep is None:
                other_lines.append(line)
                seq.append(line)
            else:
                # Protection is against ANCHORING, not against the Chinese-usage
                # safeguard. The placeholder below takes the line out of reach of the
                # forbidden-variant substitution that runs on `text`, so a regional
                # variant sitting in a heading (「超參數優化」) shipped uncorrected while
                # the identical word one line down was fixed. Correct it at capture
                # time: the substitution matches the WRONG form, so it leaves no marker
                # and stays repeatable.
                if lexicon.forbidden_regex:
                    keep = lexicon.forbidden_regex.sub(
                        lambda m: lexicon.forbidden[m.group(0)], keep)
                token = "__PROTLINE%d__" % len(protected_map)
                protected_map[token] = keep
                header_lines.append(keep)
                seq.append(token + ("\n" if keep.endswith("\n") else ""))

        if not other_lines:
            return "".join(header_lines), []

        def _restore_protected(out):
            for token, original in protected_map.items():
                out = out.replace(token + "\n" if original.endswith("\n") else token,
                                  original)
                out = out.replace(token, original.rstrip("\r\n"))
            return out

        text = "".join(seq)
        newly_anchored_info = []

        # Forbidden Replacement (Always)
        if lexicon.forbidden_regex:
            text = lexicon.forbidden_regex.sub(lambda m: lexicon.forbidden[m.group(0)], text)

        if mode == "remove_all":
            # 1. First remove standalone terminology definition boxes (including mutated/legacy ones).
            #    Require the <!-- term:/anchor: --> marker so author-written [!IMPORTANT] callouts survive.
            text = _RM_ANCHOR_BLOCK.sub('', text)

            # 2. Strip all (EN) anchors and inline comments
            cleanup_pattern, cleaner = _build_deanchor(lexicon)
            text = cleanup_pattern.sub(cleaner, text)
            text = _ORPHAN_SWEEP.sub('', text)
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
                        # every reanchor.
                        #
                        # The CJK zh above gets NO equivalent guard, and that is a known
                        # gap rather than a safe asymmetry: 量化 matches inside 輕量化,
                        # 技術債 inside 技術債務, 導讀 inside 誤導讀者. Chinese has no
                        # orthographic word boundary, so \b is unavailable and a correct
                        # guard would need segmentation or a longest-match exclusion set.
                        # Neither exists here, so the mitigation is a review rule, not
                        # code: see agent-operating-guideline.md §6 — a demotion decision
                        # must inspect match POSITIONS, not just definitions, because the
                        # true-positive rate is not mechanically decidable.
                        patterns.append(r'\b' + re.escape(en) + r'\b')
        
        patterns.sort(key=len, reverse=True)
        
        # The trailing parenthetical is CAPTURED, not blindly eaten. It used to be
        # consumed and replaced by the canonical gloss whatever it held, so everything
        # an author put in brackets right after a term was deleted: a whole citation
        # （參閱 [Jozefowicz 等人，2015 / 《An Empirical Exploration …》](…)）vanished,
        # and so did the qualifier in 感受野（Effective Receptive Field, ERF）— which is
        # the distinction that sentence exists to draw. Only an exact alias is this
        # term's own gloss; anything else is the author's text and survives verbatim.
        anchor_regex = re.compile(
             r'([\*_]{2})?(' + '|'.join(patterns) + r')([\*_]{2})?' +
             r'(?:[ \t]*([\(（][^\n]*?[\)）]))?' + 
             r'([\*_]{2})?' +
             r'(?:[ \t]*<!--\s*(?:anchor|term):.*?\s*-->)?'
        )

        def replacer(match):
            pre, matched_text, post_val = match.group(1) or "", match.group(2), match.group(3) or ""
            
            # Resolve to primary ZH
            zh = lexicon.en_to_zh.get(matched_text.lower(), matched_text)

            # An EN alias carries \b, which stops a match INSIDE a word but not one
            # inside a longer English PHRASE. 泛化有效性（Generalization Viability）
            # had its parenthetical rewritten to （泛化 Viability）: half English, half
            # Chinese, and correct in neither. The alias is only a term when it stands
            # on its own, so an adjacent English word means leave the author's text
            # exactly as it is — the anchor's job never includes editing prose.
            if matched_text != zh:
                src = match.string
                if (re.match(r'[ \t]+[A-Za-z]', src[match.end(2):])
                        or re.search(r'[A-Za-z][ \t]+$', src[:match.start(2)])):
                    return match.group(0)
                # Inside brackets the English is the author's own gloss, and rewriting
                # it to Chinese is one-way: remove_all gives back the Chinese, never the
                # English. （Direct Path / Residual Bypass）came back half-translated,
                # and （Causal Tracing / Activation Patching）the same way. A term's own
                # gloss is never reached here — the Chinese match consumes it — so every
                # alias that lands inside brackets belongs to a phrase someone chose.
                head = src[:match.start(2)].rsplit('\n', 1)[-1]
                if re.search(r'[\(（][^\)）]*$', head):
                    return match.group(0)
            
            is_first = zh not in found_globally
            level = lexicon.levels.get(zh, 1)
            en_primary = lexicon.mapping.get(zh, "Unknown")
            key_val = lexicon.keys.get(zh) if hasattr(lexicon, 'keys') else zh
            if not key_val:
                key_val = zh
                
            clean_zh = re.sub(r'\s*[\(（].*?[\)）]\s*', '', zh).strip()
            clean_en = re.sub(r'^[\(（]+|[\)）]+$', '', en_primary.strip()) if en_primary else ""
            
            # `pre` and `post_val` are only this term's OWN emphasis when they match.
            # When they do not, the stray marker belongs to a NEIGHBOURING span and must
            # stay outside the anchor: 線性探針**無法** matched with pre='' and
            # post_val='**', and re-emitting that '**' before the comment stole the
            # opening marker of 無法's bold span. Asymmetric markers are therefore
            # preserved verbatim, on their own side of the anchor, and no emphasis of
            # ours is added — the author's markup wins over the anchor's styling.
            # Whose brackets are these? Only an exact alias is the gloss this anchor is
            # entitled to rewrite. Author brackets are kept as written and suppress the
            # canonical gloss, so no post ends up carrying （Diffusion Model）（Diffusion
            # Models）. The full English still reaches the reader through the
            # [!IMPORTANT] definition block.
            paren = match.group(4) or ""
            aliases = {a.strip().lower() for a in lexicon.zh_to_ens.get(zh, []) if a}
            authors_paren = paren if paren and paren[1:-1].strip().lower() not in aliases else ""

            # 作者常把粗體畫在「術語＋註記」整段上：**中介誤認（Mediator Misreading）**。
            # The closing marker then sits after the brackets, so it reads as asymmetric
            # and the anchor came out as **術語（EN） <!-- term -->**. De-anchoring folds
            # that back to **術語**, and the next anchoring emits **術語**（EN） <!-- term -->
            # — correct, but a different shape, so the first reanchor of every published
            # post rewrote lines for no reason. Recognise the pair and emit the settled
            # shape immediately.
            tail_emph = match.group(5) or ""
            if pre and not post_val and tail_emph == pre:
                post_val, tail_emph = pre, ""
            symmetric = pre == post_val

            if mode == "anchor_first" and is_first and level < 3:
                found_globally.add(zh)
                first_use_terms.append(zh)
                newly_anchored_info.append({
                    "zh": clean_zh, 
                    "en": clean_en,
                    "description": lexicon.descriptions.get(zh, ""),
                    "key": key_val
                })
                gloss = authors_paren or f"（{clean_en}）"
                if symmetric:
                    return f"**{clean_zh}**{gloss} <!-- term:{key_val} -->{tail_emph}"
                return f"{pre}{clean_zh}{gloss} <!-- term:{key_val} -->{post_val}{tail_emph}"
            
            if level < 3:
                if symmetric:
                    return f"{pre}{clean_zh}{post_val}{authors_paren} <!-- term:{key_val} -->{tail_emph}"
                return f"{pre}{clean_zh}{authors_paren} <!-- term:{key_val} -->{post_val}{tail_emph}"
            return f"{pre}{clean_zh}{post_val}{authors_paren}{tail_emph}"
   
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

        return _restore_protected(text), [item['zh'] for item in newly_anchored_info]

    def remove_all_anchors(self, post, lexicon):
        """Restores post to pure zero-anchor state."""
        return self.apply_lexicon(post, lexicon, mode="remove_all")
