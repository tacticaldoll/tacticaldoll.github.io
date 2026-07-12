## Authored by Schema: .agent/schemas/terminology.schema.yaml
## Reference Workflow: .agent/workflows/publish-article.md
## Role: CLI interface for TerminologyEngine (SRP: business logic stays in engine.py)

import argparse
import json
import os
import sys

# Add scripts root to path
scripts_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if scripts_root not in sys.path:
    sys.path.append(scripts_root)

from domain.terminology.engine import TerminologyEngine
from infra.utils import normalize_path


def main():
    parser = argparse.ArgumentParser(description="Terminology Engine CLI")
    parser.add_argument("file_path", nargs="?", help="Path to markdown file to process")
    parser.add_argument("--mode", choices=["anchor_first", "anchor_all", "remove_all"], default="anchor_first")
    parser.add_argument("--handoff", help="Path to handoff.terms.json to scope terms strictly")
    parser.add_argument("--query", help="Lookup information for a specific term")
    parser.add_argument("--list-forbidden", action="store_true", help="List all forbidden terms")
    parser.add_argument("--fix-string", help="Apply terminology corrections to a string")
    parser.add_argument("--validate-tags", help="Validate a comma-separated list of tags")
    parser.add_argument("--json", action="store_true", dest="output_json", help="Output results in JSON format")

    args = parser.parse_args()
    engine = TerminologyEngine()

    if args.handoff:
        engine.enable_handoff_mode(args.handoff)

    if args.query:
        result = engine.lookup(args.query)
        if args.output_json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            if not result:
                print(f"Term '{args.query}' not found.")
            elif result["status"] == "forbidden":
                print(f"FORBIDDEN: '{args.query}' -> Use '{result['correction']}'")
            else:
                print(f"STANDARD: {result['zh']} ({'/'.join(result['en'])})")

    elif args.list_forbidden:
        forbidden = engine.get_all_forbidden()
        if args.output_json:
            print(json.dumps(forbidden, ensure_ascii=False))
        else:
            for f, z in sorted(forbidden.items()):
                print(f"{f:<10} -> {z}")

    elif args.fix_string:
        print(engine.replace_forbidden(args.fix_string))

    elif args.validate_tags:
        tag_list = [t.strip() for t in args.validate_tags.split(",")]
        issues = engine.validate_tags(tag_list)
        if args.output_json:
            print(json.dumps({"issues": issues}, ensure_ascii=False))
        else:
            for issue in issues:
                print(f"ISSUE: {issue}")

    elif args.file_path:
        file_path = normalize_path(args.file_path)
        if not os.path.exists(file_path):
            print(f"Error: {file_path} not found.")
            sys.exit(1)

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        if args.mode == "remove_all":
            processed = engine.remove_all_anchors(content)
        else:
            processed = engine.process_content(content, mode=args.mode)

        if processed != content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(processed)
            print(f"Processed {file_path} with mode {args.mode}.")
        else:
            print(f"No changes for {file_path}.")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
