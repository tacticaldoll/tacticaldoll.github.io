import os
import sys
import subprocess
import re
import json

# Add scripts root to path
scripts_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if scripts_root not in sys.path:
    sys.path.append(scripts_root)

from infra.utils import get_python_executable, log_info, log_error

def run_command(cmd_args):
    """Thin wrapper around subprocess for batch orchestration."""
    log_info(f"Executing: {' '.join(cmd_args)}")
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    result = subprocess.run(cmd_args, capture_output=True, text=True, env=env, encoding='utf-8', errors='replace')
    if result.returncode != 0:
        log_error(result.stderr)
        return False
    else:
        lines = result.stdout.splitlines()
        for line in lines[-2:]:
            print(f"    {line}")
        return True

def orchestrate():
    python_exe = sys.executable
    scratch_dir = ".agent-scratch"
    # Filter sessions to match patterns like YYYY-MM-DD-a
    sessions = sorted([d for d in os.listdir(scratch_dir) if os.path.isdir(os.path.join(scratch_dir, d)) and re.match(r'\d{4}-\d{2}-\d{2}', d)])
    
    print(f"Found {len(sessions)} sessions for regeneration.")
    
    for session_id in sessions:
        print(f"\n======= Orchestrating Session: {session_id} (Publish Pipeline Only) =======")

        handoff_path = os.path.join(scratch_dir, session_id, "handoff.posts.json")
        if not os.path.exists(handoff_path):
            print(f"      SKIP: Missing handoff.posts.json for {session_id}. Run /init-handoff first.")
            continue

        try:
            with open(handoff_path, "r", encoding="utf-8") as f:
                handoff = json.load(f)
        except Exception as exc:
            print(f"      SKIP: Invalid handoff.posts.json for {session_id}: {exc}")
            continue

        if handoff.get("status") != "refined":
            print(f"      SKIP: Handoff status is '{handoff.get('status', 'initiated')}', expected 'refined'.")
            continue

        # Publish-only batch mode. Handoff preparation/refinement belongs to /init-handoff.
        if not run_command([python_exe, ".agent/scripts/workflows/generate-article/pipeline.py", session_id, "--mode", "ultimate"]):
            print(f"      FAILURE: Pipeline ultimate run failed for {session_id}")
            continue

    print("\n======= Publish Batch Complete =======")

if __name__ == "__main__":
    orchestrate()
