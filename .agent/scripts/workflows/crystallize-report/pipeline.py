## Authored by Schema: .agent/schemas/crystallize-report.schema.yaml
## Reference Workflow: .agent/workflows/crystallize-report.md

import json
import sys
import os
import argparse
import re
from datetime import datetime

# Ensure UTF-8 output on Windows
sys.stdout.reconfigure(encoding='utf-8')

# Make the shared infra package importable (.agent/scripts on sys.path)
scripts_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if scripts_root not in sys.path:
    sys.path.append(scripts_root)
from infra.telemetry import detect_agent_telemetry, has_version, UNKNOWN_AGENT


def resolve_agent(declared):
    """Resolve the **Agent** front-matter value, enforcing the schema's
    "代理平台/IDE + 版本號" requirement.

    Explicit declaration is authoritative: a declaration that already carries a
    version is used verbatim. A versionless (or empty) declaration is enriched
    from vendor-neutral detection — but only when detection identifies the SAME
    platform, so we never fabricate or cross-stamp a different vendor. If a
    version still cannot be established, we abort rather than publish versionless
    or guessed telemetry.
    """
    declared = (declared or "").strip()
    if has_version(declared):
        return declared

    detected = detect_agent_telemetry()

    if not declared:
        # No declaration: trust detection only if it produced a real, versioned id.
        if detected != UNKNOWN_AGENT and has_version(detected):
            print(f"[OK] Agent auto-detected: {detected}")
            return detected
        _abort_agent(declared, detected)

    # Declared but versionless: complete it only from the same detected platform.
    if (detected != UNKNOWN_AGENT
            and has_version(detected)
            and declared.split()[0].lower() in detected.lower()):
        print(f"[OK] Agent version completed from detection: '{declared}' -> '{detected}'")
        return detected

    _abort_agent(declared, detected)


def _abort_agent(declared, detected):
    print("[ERROR] Quality Gate (Agent telemetry): schema requires '代理平台/IDE + 版本號'.")
    print(f"        Declared: '{declared or '(empty)'}'  |  Detected: '{detected}'")
    print("        Fix: set front_matter.agent to include a version "
          "(e.g. 'Claude Code VSCode Extension 2.1.168'), or run the pipeline "
          "in the authoring environment so the version can be auto-detected.")
    sys.exit(1)


def load_handoff(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"[ERROR] Handoff file {filepath} not found.")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"[ERROR] Invalid JSON in handoff file: {e}")
        sys.exit(1)

def render_front_matter(fm, structure_type):
    # Map structure_type back to readable name
    structure_map = {
        "experience_report": "Experience Report",
        "analytical_essay": "Analytical Essay",
        "technical_note": "Technical Note"
    }
    struct_name = structure_map.get(structure_type, structure_type)
    
    out = "<!-- front matter -->\n"
    out += f"**Structure**: {struct_name}\n"
    out += f"**Date**: {fm.get('date', '')}\n"
    out += f"**Model**: {fm.get('model', '')}\n"
    out += f"**Agent**: {fm.get('agent', '')}\n"
    out += f"**Source**: {fm.get('source', '')}\n"
    if 'tags' in fm and fm['tags']:
        out += f"**Tags**: {', '.join(fm['tags'])}\n"
    out += "\n---\n\n"
    return out

def render_decision_callout(decision):
    out = f"> **Decision Point**: {decision.get('decision', '')}\n"
    out += f"> — Alternatives: {decision.get('alternatives', '')}\n"
    out += f"> — Outcome: {decision.get('outcome', '')}\n"
    return out

def process_section(section):
    out = f"## {section['title']}\n\n"
    
    # Process prose
    prose = section.get('prose', [])
    for p in prose:
        out += f"{p}\n\n"
        
    # Process decisions
    decisions = section.get('decisions', [])
    if decisions:
        dec_count = len(decisions)
        if dec_count <= 4:
            # 2-4: All callouts
            for d in decisions:
                out += render_decision_callout(d) + "\n"
        else:
            # > 4: Render first 2 as callouts, rest as list (simplified narrative weave)
            for d in decisions[:2]:
                out += render_decision_callout(d) + "\n"
            out += "### 次要決策\n\n"
            for d in decisions[2:]:
                out += f"- **{d.get('decision', '')}**: 考量過 {d.get('alternatives', '')}，最終 {d.get('outcome', '')}。\n"
            out += "\n"
            
    # Process diagrams
    diagrams = section.get('mermaid_diagrams', [])
    for mm in diagrams:
        out += "```mermaid\n"
        out += f"{mm}\n"
        out += "```\n\n"
        
    return out

def generate_report(handoff_data, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    report_path = os.path.join(output_dir, 'report.zh-TW.md')
    
    with open(report_path, 'w', encoding='utf-8') as f:
        # Title (derived from tags or just default)
        f.write("# 知識結晶報告\n\n")
        
        # Front matter
        fm = handoff_data.get('front_matter', {})
        f.write(render_front_matter(fm, handoff_data.get('structure_type', '')))
        
        # Sections
        sections = handoff_data.get('sections', [])
        
        # Quality Gate Check
        valid_sections = 0
        for sec in sections:
            if len(sec.get('prose', [])) >= 2 or len(sec.get('decisions', [])) > 0:
                valid_sections += 1
                
        if valid_sections < 3:
            print("[WARNING] Quality Gate: 報告總體實質章節 < 3 個。請確認內容是否足夠充實。")
            
        for sec in sections:
            f.write(process_section(sec))
            
    print(f"[OK] Report generated at {report_path}")
    
def generate_deploy_kit(handoff_data, output_dir):
    deploy_kit = handoff_data.get('deploy_kit', {})
    tools = deploy_kit.get('tools', [])
    if not tools:
        return
        
    deploy_dir = os.path.join(output_dir, 'deploy')
    os.makedirs(deploy_dir, exist_ok=True)
    
    for tool in tools:
        t_type = tool.get('type')
        t_name = tool.get('name', 'untitled')
        content = tool.get('content', '')
        
        if t_type == 'rule':
            rules_dir = os.path.join(deploy_dir, 'rules')
            os.makedirs(rules_dir, exist_ok=True)
            with open(os.path.join(rules_dir, f"{t_name}.md"), 'w', encoding='utf-8') as f:
                f.write(content)
        elif t_type == 'skill':
            skills_dir = os.path.join(deploy_dir, 'skills', t_name)
            os.makedirs(skills_dir, exist_ok=True)
            with open(os.path.join(skills_dir, 'SKILL.md'), 'w', encoding='utf-8') as f:
                f.write(content)
                
    print(f"[OK] Deploy kit generated at {deploy_dir}")

def update_index(session_id, output_dir):
    # Simplified index update
    index_path = os.path.join('.agent-scratch', 'index.md')
    os.makedirs('.agent-scratch', exist_ok=True)
    
    mode = 'a' if os.path.exists(index_path) else 'w'
    with open(index_path, mode, encoding='utf-8') as f:
        if mode == 'w':
            f.write("# 報告全域索引\n\n")
        f.write(f"- [{datetime.now().strftime('%Y-%m-%d %H:%M')}] Session: {session_id} - [Report]({os.path.join(output_dir, 'report.zh-TW.md')})\n")
    print(f"[OK] Index updated at {index_path}")

def slugify(value):
    value = (value or "").strip().lower()
    value = re.sub(r'[^a-z0-9\u4e00-\u9fff]+', '-', value)
    value = value.strip('-')
    return value or "untitled-report"

def resolve_topic_slug(handoff_data, explicit_slug):
    if explicit_slug:
        return slugify(explicit_slug)
    if handoff_data.get("topic_slug"):
        return slugify(handoff_data["topic_slug"])
    fm = handoff_data.get("front_matter", {})
    tags = fm.get("tags") or []
    if tags:
        return slugify(str(tags[0]))
    return "untitled-report"

def main():
    parser = argparse.ArgumentParser(description="Render crystallize report from handoff JSON.")
    parser.add_argument("session_id", help="Session ID (e.g. YYYY-MM-DD-a)")
    parser.add_argument("--topic-slug", help="Topic directory slug under the session directory")
    args = parser.parse_args()
    
    handoff_path = 'handoff.report.json'
    data = load_handoff(handoff_path)
    
    topic_slug = resolve_topic_slug(data, args.topic_slug)
    output_dir = os.path.join('.agent-scratch', args.session_id, topic_slug)

    print(f"=== Starting Report Pipeline for {args.session_id} ===")
    # Gate the Agent telemetry BEFORE any file is written, so an abort never
    # leaves a truncated report on disk.
    fm = data.setdefault('front_matter', {})
    fm['agent'] = resolve_agent(fm.get('agent'))
    generate_report(data, output_dir)
    generate_deploy_kit(data, output_dir)
    update_index(args.session_id, output_dir)
    
    # Clean up handoff
    os.remove(handoff_path)
    print(f"[OK] Cleaned up {handoff_path}")
    print("=== Pipeline Complete ===")

if __name__ == "__main__":
    main()
