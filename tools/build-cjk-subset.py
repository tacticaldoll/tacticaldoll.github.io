#!/usr/bin/env python3
"""Build a content-driven IBM Plex Sans TC web subset for the blog.

WHY: the site self-hosts fonts (no CDN, per theme GUIDE). The full IBM Plex
Sans TC is ~2.5MB/weight; the blog uses only a small slice of CJK glyphs. This
subsets it to exactly the characters that appear in the site's CJK-rendering
surfaces (post bodies + front matter, hugo.toml, data/ UI strings) plus a safety
set of CJK/Latin punctuation, and emits woff2 into static/fonts/.

(IBM Plex Mono — the Latin side — is tiny and used whole; not subset here.)

RE-RUN whenever new posts add characters (or wire into a pre-build hook):
    python3 tools/build-cjk-subset.py
Requires: pip install fonttools brotli ; source woff2 under tools/plexsrc/
    (fetch: cdn.jsdelivr.net/npm/@ibm/plex-sans-tc/fonts/complete/woff2/hinted/IBMPlexSansTC-{Regular,Bold}.woff2)
"""
import glob, os, sys, subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "tools", "plexsrc")
OUT = os.path.join(ROOT, "static", "fonts")
WEIGHTS = ["Regular", "Bold"]

GLOBS = ["content/**/*.md", "hugo.toml", "data/**/*.*", "themes/slotify/data/**/*.*"]
SAFE_UNICODES = "U+0020-007E,U+00A0-00FF,U+2000-206F,U+3000-303F,U+FF00-FFEF,U+2460-24FF"


def collect_cjk():
    chars = set()
    for g in GLOBS:
        for p in glob.glob(os.path.join(ROOT, g), recursive=True):
            if os.path.isfile(p):
                try:
                    chars |= set(open(p, encoding="utf-8").read())
                except (UnicodeDecodeError, IsADirectoryError):
                    pass
    return {c for c in chars if "一" <= c <= "鿿" or "㐀" <= c <= "䶿"}


def main():
    cjk = collect_cjk()
    os.makedirs(OUT, exist_ok=True)
    txt = os.path.join(SRC, "_subset_chars.txt")
    open(txt, "w", encoding="utf-8").write("".join(sorted(cjk)))
    print(f"CJK glyphs to keep: {len(cjk)}")
    for w in WEIGHTS:
        src = os.path.join(SRC, f"IBMPlexSansTC-{w}.woff2")
        out = os.path.join(OUT, f"IBMPlexSansTC-{w}.subset.woff2")
        if not os.path.exists(src):
            print(f"  MISSING source: {src}", file=sys.stderr); sys.exit(1)
        subprocess.run([
            sys.executable, "-m", "fontTools.subset", src,
            f"--text-file={txt}", f"--unicodes={SAFE_UNICODES}",
            "--flavor=woff2", "--desubroutinize", "--no-hinting",
            "--name-IDs=", "--notdef-outline", "--recalc-bounds",
            f"--output-file={out}",
        ], check=True)
        print(f"  {w:8} -> {os.path.relpath(out, ROOT)}  ({os.path.getsize(out)/1024:.0f} KB)")


if __name__ == "__main__":
    main()
