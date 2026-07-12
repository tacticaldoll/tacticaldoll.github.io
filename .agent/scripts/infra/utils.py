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
