## Authored by Schema: none (utility)
## Reference Workflow: .agent/workflows/calibrate-guidelines.md

import datetime
import json
import os
import subprocess
import re
import sys

# Add scripts root to path
scripts_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if scripts_root not in sys.path:
    sys.path.append(scripts_root)

from infra.utils import normalize_path
from infra.taxonomy import TaxonomyEngine


def published_domain(index_path, bare_to_category):
    """The AI domain tag a published post currently carries, or None.

    Read out of the front matter rather than recomputed, because the point is to
    compare what shipped against what the current taxonomy says.
    """
    with open(index_path, "r", encoding="utf-8") as f:
        src = f.read()
    fm = re.match(r'^\+\+\+[ \t]*\n(.*?)\n\+\+\+', src, re.DOTALL)
    if not fm:
        return None
    tags = re.search(r'^tags[ \t]*=[ \t]*\[(.*?)\]', fm.group(1), re.DOTALL | re.MULTILINE)
    if not tags:
        return None
    for tag in re.findall(r'"([^"]+)"', tags.group(1)):
        if tag in bare_to_category:
            return bare_to_category[tag]
    return None

def main():
    import glob
    scratch_dir = normalize_path(".agent-scratch")
    if not os.path.exists(scratch_dir):
        print(".agent-scratch directory not found.")
        sys.exit(1)

    engine = TaxonomyEngine()
    categories = engine.data.get("ai_taxonomy", {}).get("categories", [])
    bare_to_category = {re.sub(r'\s*[(（].*?[)）]', '', c).strip(): c for c in categories}
    divergences = []

    report_lines = [
        "# Article Compliance & Correction Report",
        f"Generated at: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "The `Domain` column compares the domain tag a post shipped with against what",
        "the current taxonomy says about its source report. A divergence is a question,",
        "not a defect: it means either the post is stale or the classifier is wrong for",
        "that post, and only reading it tells you which. This report does not block.",
        "",
        "| Session | Article ID | Status | Domain | Issues Found |",
        "| :--- | :--- | :--- | :--- | :--- |"
    ]

    python_exe = sys.executable
    safeguard_script = normalize_path(".agent/scripts/workflows/calibrate-guidelines/safeguard.py")

    # Scan session directories in .agent-scratch (e.g. 2026-03-10-a, recrystal-2026-09-06-a).
    # The recrystal- prefix was not admitted here, so every post produced by
    # /recrystallize-post-series was silently outside this sweep — which by now is all
    # 36 of the published posts.
    session_dirs = sorted([d for d in os.listdir(scratch_dir)
                           if os.path.isdir(os.path.join(scratch_dir, d))
                           and re.match(r'^(?:recrystal-)?\d{4}-\d{2}-\d{2}', d)])

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
                report_lines.append(f"| {session_id} | {article_id} | 🟡 SKIP | — | Missing Target ({target_path}) |")
                continue

            with open(source_report, "r", encoding="utf-8") as f:
                computed = engine.classify_domain(f.read())
            shipped = published_domain(target_path, bare_to_category)
            short = lambda c: (c.split(" (")[0] if c else "(none)")
            if shipped == computed:
                domain_cell = f"✅ {short(shipped)}"
            else:
                domain_cell = f"⚠️ {short(shipped)} → {short(computed)}"
                divergences.append((session_id, article_id, short(shipped), short(computed)))

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
            
            report_lines.append(f"| {session_id} | {article_id} | {status} | {domain_cell} | {issue_str} |")

    if divergences:
        report_lines += ["", f"## Domain divergences ({len(divergences)})", "",
                         "| Session | Article ID | Shipped | Current taxonomy |",
                         "| :--- | :--- | :--- | :--- |"]
        for session_id, article_id, a, b in divergences:
            report_lines.append(f"| {session_id} | {article_id} | {a} | {b} |")

    report_path = normalize_path("audit_report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))
    
    print(f"Audit report generated: {report_path}")
    if divergences:
        print(f"Domain divergences needing adjudication: {len(divergences)}")
        for session_id, article_id, a, b in divergences:
            print(f"  {session_id}/{article_id}: {a} -> {b}")

if __name__ == "__main__":
    main()
