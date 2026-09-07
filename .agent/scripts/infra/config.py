## Authored by Schema: none (infrastructure)
## Reference Workflow: Shared Infrastructure

import os
import sys

# Base Directories
# This file is in .agent/scripts/infra/config.py
INFRA_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_DIR = os.path.dirname(INFRA_DIR)
AGENT_DIR = os.path.dirname(SCRIPTS_DIR)
ROOT_DIR = os.path.dirname(AGENT_DIR)

# Reference & Governance
REFERENCE_DIR = os.path.join(AGENT_DIR, "reference")
LEXICON_CORE_DIR = os.path.join(AGENT_DIR, "lexicon-core")
DATABASES_DIR = os.path.join(LEXICON_CORE_DIR, "databases")
LEXICON_SCRIPTS_DIR = os.path.join(LEXICON_CORE_DIR, "scripts")

# Add lexicon scripts to sys.path for direct imports
if LEXICON_SCRIPTS_DIR not in sys.path:
    sys.path.append(LEXICON_SCRIPTS_DIR)

TERMINOLOGY_JSON = os.path.join(DATABASES_DIR, "terminology.json")
TERMINOLOGY_DRAFT_JSON = os.path.join(DATABASES_DIR, "terminology.draft.json")
TERMINOLOGY_ARCHIVE_JSON = os.path.join(DATABASES_DIR, "terminology.archive.json")
TAXONOMY_JSON = os.path.join(DATABASES_DIR, "taxonomy.json")
TAXONOMY_MD = os.path.join(DATABASES_DIR, "taxonomy.md")
RULES_JSON = os.path.join(DATABASES_DIR, "rules.json")


# Content
POSTS_DIR = os.path.join(ROOT_DIR, "content", "posts")

# Scratch Area
SCRATCH_DIR = os.path.join(ROOT_DIR, ".agent-scratch")


def resolve_path(rel_path):
    """Resolves a relative path against the project root."""
    return os.path.normpath(os.path.join(ROOT_DIR, rel_path))

def get_session_dir(session_id):
    """Returns the absolute path to a session's scratch directory."""
    return os.path.join(SCRATCH_DIR, session_id)

# Genre published when a report declares no **Structure** header. Lives here so the
# handoff preparer and the post assembler cannot disagree about what an undeclared
# genre becomes; both log when they fall back to it.
GENRE_FALLBACK_SCOPE = "Technical Note"

# Tag assembly limits. Named here rather than left inline because both silently
# discard candidates: TAG_SCAN_LIMIT caps how many harvested candidates are even
# considered, TAG_CAP caps how many survive into the front matter. The assembler
# reports what each one drops, and the audit reads these rather than holding a copy.
TAG_SCAN_LIMIT = 15
TAG_CAP = 8
