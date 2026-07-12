## Authored by Schema: none (infrastructure)
## Reference Workflow: Shared Infrastructure
"""Agent / model telemetry detection.

Vendor-neutral by design. Identity is resolved by trying a *registry* of
self-contained probes; each probe recognises exactly one platform and returns
``None`` when it cannot identify itself. No probe is the "default": when every
probe misses we honestly report ``Unknown`` rather than guessing a vendor — a
confidently-wrong default is an implicit dependency that bleeds the wrong
identity into published telemetry.

Detection is a *fallback*. The authoritative source of "which agent / model am
I" is explicit self-declaration (the ``--agent`` / ``--model`` flags and the
crystallize ``agent`` field); this module only fills the gap when no
declaration is supplied. Adding a new platform means adding one probe function
— never editing the existing ones.
"""

import os
import json
import re

UNKNOWN_AGENT = "Unknown Agent"
UNKNOWN_MODEL = "Unknown Model"


def _read_product_json(root):
    """Load <root>/product.json, or None if absent/unreadable."""
    if not root:
        return None
    path = os.path.join(root, "product.json")
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _join(name, version):
    """Compose 'Name Version', or just the name, or None — never a bare version."""
    name = (name or "").strip()
    version = (version or "").strip()
    if name and version:
        return f"{name} {version}"
    return name or None


# --- Agent probes ----------------------------------------------------------
# Each returns "Name X.Y.Z" (with a version whenever one is derivable) or None.

def _probe_antigravity():
    """Antigravity IDE — declared via ANTIGRAVITY_EDITOR_APP_ROOT/product.json."""
    data = _read_product_json(os.environ.get("ANTIGRAVITY_EDITOR_APP_ROOT", ""))
    if not data:
        return None
    name = data.get("nameShort") or "Antigravity IDE"
    version = data.get("ideVersion") or data.get("version")
    return _join(name, version)


def _probe_claude_code():
    """Claude Code — CLAUDECODE env present; version derived from the binary path / AI_AGENT."""
    if not os.environ.get("CLAUDECODE"):
        return None
    entrypoint = os.environ.get("CLAUDE_CODE_ENTRYPOINT", "").lower()
    in_vscode = (
        "vscode" in entrypoint
        or os.environ.get("__CFBundleIdentifier", "").endswith("VSCode")
        or bool(os.environ.get("VSCODE_PID"))
    )
    name = "Claude Code VSCode Extension" if in_vscode else "Claude Code"

    version = None
    # Prefer the version embedded in the extension binary path:
    #   .../anthropic.claude-code-2.1.168-darwin-arm64/...
    m = re.search(r"claude-code-(\d+\.\d+\.\d+)", os.environ.get("CLAUDE_CODE_EXECPATH", ""))
    if m:
        version = m.group(1)
    else:
        # Fall back to AI_AGENT="claude-code_2-1-168_agent"
        m = re.search(r"(\d+)-(\d+)-(\d+)", os.environ.get("AI_AGENT", ""))
        if m:
            version = ".".join(m.groups())
    return _join(name, version)


def _probe_vscode_host():
    """Generic VSCode-family host — records the real editor when no AI-agent probe matched."""
    cwd = os.environ.get("VSCODE_CWD", "")
    data = _read_product_json(os.path.join(cwd, "resources/app")) if cwd else None
    if not data:
        return None
    name = data.get("nameLong") or data.get("nameShort")
    version = data.get("version")
    return _join(name, version)


# Most specific (AI agents) first; generic editor host last.
_AGENT_PROBES = [_probe_antigravity, _probe_claude_code, _probe_vscode_host]


def detect_agent_telemetry():
    """Resolve the active agent / IDE identity, or UNKNOWN_AGENT if unidentifiable."""
    for probe in _AGENT_PROBES:
        try:
            result = probe()
        except Exception:
            result = None
        if result:
            return result
    return UNKNOWN_AGENT


# --- Model probes ----------------------------------------------------------

def _probe_model_antigravity():
    """Antigravity injects the active model into ANTIGRAVITY_SOURCE_METADATA."""
    meta = os.environ.get("ANTIGRAVITY_SOURCE_METADATA")
    if not meta:
        return None
    try:
        data = json.loads(meta)
        if isinstance(data, dict):
            if data.get("model"):
                return data["model"]
            tool = data.get("tool")
            if isinstance(tool, dict) and tool.get("model"):
                return tool["model"]
    except Exception:
        pass
    m = re.search(r'"model"\s*:\s*"([^"]+)"', meta)
    return m.group(1) if m else None


_MODEL_PROBES = [_probe_model_antigravity]


def detect_model_telemetry():
    """Resolve the active model id, or UNKNOWN_MODEL.

    Most agents do not expose the chosen LLM via the environment; the model is
    therefore best supplied explicitly (e.g. refine_handoff.py --model).
    """
    for probe in _MODEL_PROBES:
        try:
            result = probe()
        except Exception:
            result = None
        if result:
            return result
    return UNKNOWN_MODEL


def has_version(label):
    """True if an agent / model label already carries an X.Y(.Z) version token."""
    return bool(label) and bool(re.search(r"\d+\.\d+", label))


if __name__ == "__main__":
    try:
        from infra.utils import format_model_id
    except ImportError:
        def format_model_id(x):
            return x

    print(f"Agent: {detect_agent_telemetry()}")
    print(f"Model: {format_model_id(detect_model_telemetry())}")
