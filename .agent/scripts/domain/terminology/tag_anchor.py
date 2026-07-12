# -*- coding: utf-8 -*-
## Authored by Schema: ../../../schemas/terminology.schema.yaml
## Reference Workflow: ../../../workflows/reanchor-posts.md
## Role: Single SSOT for TAG anchoring, shared by the publish assembler (build time)
##       and reanchor-posts (maintenance time). A tag's stable identity is its KEY
##       (the `# term:Key` comment), NOT its display text — the display can drift while
##       the key is stable. Resolution spans terminology.json (tech terms) and
##       taxonomy.json (genres, AI domains).
##
## Split of concerns: this module only ANCHORS/refreshes given tags (annotation). It does
## NOT SELECT which tags exist (harvest/scope/domain detection) — that stays build-time only.

import re


def clean_tag(tag):
    """Strips a trailing parenthetical gloss; returns the bare display text."""
    if not tag:
        return ""
    return re.sub(r'\s*[(（].*?[)）]', '', tag).strip()


def camel_key(en):
    """CamelCase key from an English name/slug (mirrors lexicon key generation)."""
    return "".join(w.capitalize() for w in re.findall(r'[a-zA-Z0-9]+', en or ""))


class TagAnchorer:
    """Resolves tags to their canonical (display, key) against the live SSOTs.

    Two entry points share one resolution core:
      - anchor_by_display(tag): build time — a tag arrives as display text (no key yet).
      - reanchor_entry(display, key): maintenance time — an existing anchored tag is
        refreshed BY KEY (identity), display recomputed, dropped if removed/downgraded.
    """

    def __init__(self, lexicon):
        self.lexicon = lexicon
        # term key -> canonical ZH (reverse of lexicon.keys: ZH -> key)
        self.term_key_to_zh = {key: zh for zh, key in lexicon.keys.items()}
        # genre key -> canonical display ZH, from taxonomy.json (the genre SSOT, not hardcoded)
        self.genre_key_to_zh = {}
        for en, zh in lexicon.taxonomy.get("genres", {}).items():
            self.genre_key_to_zh[camel_key(en)] = zh
        # AI domain category key -> display, from taxonomy.json
        self.domain_key_to_disp = {}
        for c in lexicon.taxonomy.get("ai_taxonomy", {}).get("categories", []):
            m = re.search(r'\((.*?)\)', c)
            self.domain_key_to_disp[camel_key(m.group(1)) if m else camel_key(c)] = clean_tag(c)

    def _canonical_term_display(self, zh):
        """Display rule shared with the legacy assembler: prefer the English primary when
        the ZH equals it (case-insensitively), else the ZH."""
        en_list = self.lexicon.zh_to_ens.get(zh, [])
        en_primary = en_list[0] if en_list else None
        if en_primary:
            clean_en = re.sub(r'^[\(（]+|[\)）]+$', '', en_primary.strip())
            if zh.lower() == clean_en.lower():
                return clean_en
        return zh

    def genre_tag(self, scope, default_scope="Technical Note"):
        """Resolves a genre scope name (e.g. 'Analytical Essay') to (display_zh, key)
        via the taxonomy genre SSOT, falling back to default_scope. Used at build time so
        the published genre matches what reanchor would re-derive."""
        key = camel_key(scope)
        if key in self.genre_key_to_zh:
            return (self.genre_key_to_zh[key], key)
        dkey = camel_key(default_scope)
        return (self.genre_key_to_zh.get(dkey, default_scope), dkey)

    def anchor_by_display(self, tag, is_genre=False):
        """Build time: a tech tag display -> (display, key) or None (drop).
        Mirrors the legacy assembler._anchor_tag semantics for tech terms."""
        clean = clean_tag(tag).lower()
        res = self.lexicon.lookup(clean)
        if res and res.get("status") == "standard" and res.get("level", 1) < 3:
            zh, key = res["zh"], res.get("key", "")
            if is_genre:
                return (zh, key)
            return (self._canonical_term_display(zh), key)
        return None

    def reanchor_entry(self, display, key):
        """Maintenance time: refresh an existing (display, key) BY KEY.

        Returns refreshed (display, key), or None to DROP. Genre/domain tags are
        structural and never dropped (only their display is refreshed); tech tags are
        dropped when their term was removed (key gone) or downgraded to level >= 3.
        """
        if key in self.genre_key_to_zh:
            return (self.genre_key_to_zh[key], key)          # genre: refresh display, keep
        if key in self.term_key_to_zh:
            zh = self.term_key_to_zh[key]
            if self.lexicon.levels.get(zh, 1) < 3:
                return (self._canonical_term_display(zh), key)  # tech: refresh display, keep
            return None                                          # downgraded -> drop
        if key in self.domain_key_to_disp:
            return (self.domain_key_to_disp[key], key)        # domain: refresh display, keep
        return None                                            # removed term -> drop

    def reanchor_tags_block(self, fm_text):
        """Rewrites the `tags = [...]` block inside a verbatim TOML front-matter string,
        IN PLACE: each entry is refreshed/dropped by key, duplicates (same key) are merged.
        Every other byte of the front matter is preserved. Returns (new_fm_text, stats).
        stats = {"refreshed": n, "dropped": n}.
        """
        m = re.search(r'(tags\s*=\s*\[)(.*?)(\])', fm_text, re.DOTALL)
        if not m:
            return fm_text, {"refreshed": 0, "dropped": 0}
        head, body, tail = m.group(1), m.group(2), m.group(3)

        entry_re = re.compile(r'^([ \t]*)"(.+?)"[ \t]*,?[ \t]*#[ \t]*term:(\S+)[ \t]*$')
        indent = "    "
        for line in body.splitlines():
            em = entry_re.match(line)
            if em:
                indent = em.group(1) or indent
                break

        kept, seen = [], set()
        refreshed = dropped = 0
        for line in body.splitlines():
            em = entry_re.match(line)
            if not em:
                continue  # structural whitespace / bracket padding — regenerated below
            disp, key = em.group(2), em.group(3)
            r = self.reanchor_entry(disp, key)
            if r is None:
                dropped += 1
                continue
            ndisp, nkey = r
            if nkey in seen:
                dropped += 1
                continue
            seen.add(nkey)
            if ndisp != disp:
                refreshed += 1
            kept.append((ndisp, nkey))

        # Preserve the original closing-bracket padding (e.g. "\n  " before ]).
        close_pad = re.search(r'(\n[ \t]*)$', body)
        close = close_pad.group(1) if close_pad else "\n"
        if kept:
            new_body = "".join(f'\n{indent}"{d}", # term:{k}' for d, k in kept) + close
        else:
            new_body = ""
        new_fm = fm_text[:m.start()] + head + new_body + tail + fm_text[m.end():]
        return new_fm, {"refreshed": refreshed, "dropped": dropped}
