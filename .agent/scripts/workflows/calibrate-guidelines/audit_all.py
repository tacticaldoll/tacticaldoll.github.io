## Authored by Schema: none (utility)
## Reference Workflow: .agent/workflows/calibrate-guidelines.md

import datetime
import json
import os
import subprocess
import re
import sys
import os

# Add scripts root to path
scripts_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if scripts_root not in sys.path:
    sys.path.append(scripts_root)

from infra.utils import normalize_path

def main():
    import glob
    scratch_dir = normalize_path(".agent-scratch")
    if not os.path.exists(scratch_dir):
        print(".agent-scratch directory not found.")
        sys.exit(1)

    report_lines = [
        "# Article Compliance & Correction Report",
        f"Generated at: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "| Session | Article ID | Status | Issues Found |",
        "| :--- | :--- | :--- | :--- |"
    ]

    python_exe = sys.executable
    safeguard_script = normalize_path(".agent/scripts/workflows/calibrate-guidelines/safeguard.py")

    # Scan session directories in .agent-scratch (e.g. 2026-03-10-a)
    session_dirs = sorted([d for d in os.listdir(scratch_dir) if os.path.isdir(os.path.join(scratch_dir, d)) and re.match(r'^\d{4}-\d{2}-\d{2}', d)])

    for session_id in session_dirs:
        base_path = os.path.join(scratch_dir, session_id)
        # Scan subdirectories under the session directory (each representing an article/slug)
        subdirs = sorted([d for d in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, d))])
        
        for article_id in subdirs:
            # Source report path
            source_report = normalize_path(os.path.join(base_path, article_id, "report.zh-TW.md"))
            if not os.path.exists(source_report):
                continue
                
            # Find matching generated post directory in content/posts
            target_path = ""
            posts_pattern = os.path.join("content", "posts", f"gen-{session_id}*--{article_id}")
            matching_dirs = glob.glob(posts_pattern)
            if matching_dirs:
                target_path = normalize_path(os.path.join(matching_dirs[0], "index.md"))
                
            if not target_path or not os.path.exists(target_path):
                report_lines.append(f"| {session_id} | {article_id} | 🟡 SKIP | Missing Target ({target_path}) |")
                continue

            # Run safeguard.py
            cmd = [python_exe, safeguard_script, source_report, target_path]
            result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
            
            output = result.stdout
            issues = []
            if output:
                for line in output.splitlines():
                    if "ALERT:" in line or "CRITICAL:" in line or "FAILURE:" in line:
                        issues.append(line.split(":", 1)[1].strip())

            status = "✅ PASS" if result.returncode == 0 else "❌ FAIL"
            issue_str = "<br>".join(issues) if issues else "None"
            
            report_lines.append(f"| {session_id} | {article_id} | {status} | {issue_str} |")

    report_path = normalize_path("audit_report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))
    
    print(f"Audit report generated: {report_path}")

if __name__ == "__main__":
    main()
