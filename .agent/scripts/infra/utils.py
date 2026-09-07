## Authored by Schema: none (infrastructure)
## Reference Workflow: Shared Infrastructure

import os
import re
import sys
import json
from datetime import datetime

try:
    import tomllib
except ImportError:
    import tomli as tomllib

# Try to import config if possible, fallback for standalone use
try:
    from infra import config
except ImportError:
    config = None

def get_python_executable():
    """Returns the active Python 3 executable for child script calls."""
    return sys.executable

def parse_toml_front_matter(content):
    """
    Parses TOML front matter from markdown content.
    Returns a tuple of (metadata_dict, body_text).
    """
    parts = re.split(r'^\+\+\+\s*$', content, maxsplit=2, flags=re.MULTILINE)
    if len(parts) >= 3:
        try:
            metadata = tomllib.loads(parts[1])
            return metadata, parts[2]
        except Exception as e:
            log_error(f"Error parsing TOML front matter: {e}")
            return {}, parts[2]
    return {}, content

def build_toml_front_matter(metadata):
    """
    Builds a TOML front matter string from a dictionary, ensuring
    dictionaries (tables) are serialized last to prevent TOML parsing nesting bugs.
    Uses recursive serialization to support arbitrary nesting depth.
    """
    lines = ["+++"]
    
    def _serialize_value(value):
        """Serialize a single TOML value (non-table)."""
        if isinstance(value, str):
            return f'"{value}"'
        elif isinstance(value, bool):
            return "true" if value else "false"
        elif isinstance(value, (list, tuple)):
            # Detect commented tag list (list of tuples: (value, comment))
            if value and isinstance(value[0], tuple) and len(value[0]) == 2:
                items = []
                for v, comment in value:
                    if comment:
                        items.append(f'\n    "{v}", # term:{comment}')
                    else:
                        items.append(f'\n    "{v}",')
                return "[" + "".join(items) + "\n  ]"
            else:
                items = ", ".join([_serialize_value(v) for v in value])
                return f'[{items}]'
        else:
            return str(value)
    
    def _serialize_table(data, prefix="", indent=0):
        """Recursively serialize a dict, emitting scalars first then sub-tables."""
        pad = "    " * indent
        # First pass: non-dictionary fields
        for key, value in data.items():
            if isinstance(value, dict):
                continue
            lines.append(f'{pad}{key} = {_serialize_value(value)}')
        # Second pass: dictionary fields (sub-tables)
        for key, value in data.items():
            if isinstance(value, dict):
                table_key = f"{prefix}.{key}" if prefix else key
                lines.append(f'{pad}[{table_key}]')
                _serialize_table(value, prefix=table_key, indent=indent + 1)
    
    _serialize_table(metadata)
    lines.append("+++\n")
    return "\n".join(lines)

def load_json(path):
    """Safely loads a JSON file with utf-8 encoding."""
    if not os.path.exists(path):
        return None
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        log_error(f"Failed to load JSON from {path}: {e}")
        return None

# Bold keys the report template writes into its provenance header. Restricted to
# those: a prose body can open with a bold pair of its own, and `**Session**` /
# `**Reports**` / `**Series**` belong to guides and series-maps, which are not
# reports and must not be mistaken for one.
_PROVENANCE_KEYS = ("Structure", "Date", "Model", "Agent", "Source", "Tags", "Description")

_PROVENANCE_MARKER_RE = re.compile(r'^[ \t]*<!--[ \t]*front matter[ \t]*-->', re.M | re.I)
_PROVENANCE_PAIR_RE = re.compile(
    r'^[ \t]*\*\*(?:%s)\*\*[ \t]*:' % "|".join(_PROVENANCE_KEYS), re.M)


def opens_provenance_header(text):
    """True when `text` opens with a crystallized report's provenance header block.

    The signature is the front-matter marker, or one of the keys the report template
    writes, within the head of the document. Shape alone is not enough: `**前提**: ...`
    is a bold pair too, and it is prose.
    """
    head = text[:800]
    return bool(_PROVENANCE_MARKER_RE.search(head) or _PROVENANCE_PAIR_RE.search(head))


def strip_report_provenance(source_text):
    """Strips a crystallized report's provenance header, leaving only the prose body.

    A `report.zh-TW.md` opens with generation provenance — an H1, an optional
    `<!-- front matter -->` marker, bold `**Key**: Value` lines (Structure / Date /
    Model / Agent / Source) and a closing horizontal rule. That header is a pipeline
    artifact: `publish-article` strips it rather than publishing it.

    It must also be stripped before any semantic read of the report. `**Agent**:
    Codex VS Code extension ...` contains the substring 'agent', which is a
    detection keyword for the `AI 代理人 (AI Agent)` domain, so classifying the raw
    text lets provenance metadata decide the article's domain. Callers that classify
    or scan report prose consume this function; `HugoPost.from_source` uses it to
    build the published body, keeping both paths on one definition.

    Idempotent, and it has to be: `from_source` strips a report to build the body and
    `classify_domain` strips again whatever it is handed, so a clean body passes
    through a second time. Every line this removes is provenance only in the context
    of a header block — a leading H1 is otherwise the document's title, a bold pair is
    otherwise prose, a rule is otherwise a section break — so the whole strip is
    conditional on that block being present. Without the guard the second pass ate the
    body's own first line, and those lines carry detection keywords: the title of a
    report on boundary governance contains 治理, which decides a domain.
    """
    if not source_text:
        return ""
    # YAML front matter is machine metadata in any document, never prose, so it goes
    # before the question of whether a provenance header follows is even asked.
    content = re.sub(r'^---\s*\n.*?\n---\s*\n', '', source_text, flags=re.DOTALL)
    if not opens_provenance_header(content):
        return content.strip()
    # Strip the very first H1 if it exists
    content = re.sub(r'^[ \t]*#[ \t]+.*?\n', '', content).lstrip()
    # Strip the HTML front matter comment marker
    content = re.sub(r'^[ \t]*<!--\s*front matter\s*-->\s*\n', '', content, flags=re.IGNORECASE)
    # Strip standard top-level bold Key: Value pairs if they exist at the top
    while True:
        match = re.match(r'^[ \t]*\*\*.*?\*\*:\s*.*?\n', content)
        if not match:
            break
        content = content[match.end():]
    # The bold-pair loop above stops at the first line that is not a header pair,
    # which leaves the blank line separating the header block from the rule that
    # closes it. Consume those blank lines explicitly. Letting the rule's own
    # anchor absorb them means `^\s*`, the broad form the header rules forbid
    # because it eats the line break the anchor is there to assert.
    content = re.sub(r'\A(?:[ \t]*\n)+', '', content)
    # Strip the horizontal rule that closes the report's front-matter block.
    # Without this it survives into the post body and, being neither a heading
    # nor an alert, blocks relocate_alerts_after_more() from lifting the first
    # section past <!--more-->, leaving a stray <hr> as the whole summary.
    content = re.sub(r'^[ \t]*(?:-{3,}|\*{3,}|_{3,})[ \t]*\n', '', content)
    return content.strip()

def normalize_path(path):
    """Normalizes path for the current OS."""
    return os.path.normpath(path)

def log_info(message):
    """Standardized info logger."""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] INFO: {message}")

def log_error(message):
    """Standardized error logger."""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] ERROR: {message}", file=sys.stderr)

def format_model_id(model_id):
    """Dynamic Heuristic Formatter: Converts raw model IDs into human-readable display names.
    Handles common AI model naming conventions: strips date suffixes, capitalizes known names.
    Shared utility to avoid duplication across refine_handoff.py and pipeline.py.
    """
    if not model_id:
        return "Unknown"
    # Strip date suffix (e.g. -20241022 or _20260330)
    model_id = re.sub(r'[-_]\d{8,}', '', model_id)
    # Normalize version separators: digit-dash-digit → digit.digit (e.g. 3-5 → 3.5)
    model_id = re.sub(r'(\d)-(\d)', r'\1.\2', model_id)
    parts = model_id.replace('-', ' ').replace('_', ' ').split()
    # Known acronyms / mixed-case tokens that plain .capitalize() would mangle
    # (e.g. "VSCode" -> "Vscode"). Keyed by lowercase form.
    acronyms = {
        "gpt": "GPT", "llm": "LLM", "ai": "AI",
        "ide": "IDE", "oss": "OSS", "cli": "CLI", "sdk": "SDK",
        "vscode": "VSCode",
    }
    normalized = []
    for part in parts:
        lower = part.lower()
        if lower in acronyms:
            normalized.append(acronyms[lower])
        elif lower in ["gemini", "claude", "pro", "flash", "opus", "sonnet", "haiku"]:
            normalized.append(part.capitalize())
        else:
            # Handle short version suffixes like "4o"
            if part.endswith('o') and len(part) <= 3:
                normalized.append(part)
            else:
                normalized.append(part.capitalize())
    return " ".join(normalized)
