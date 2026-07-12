import os
import sys
import subprocess

def run_script(script_rel_path, target, extra_args=None):
    print(f"--- Running {script_rel_path} ---")
    python_exe = sys.executable
    script_path = os.path.join(".agent", "scripts", script_rel_path)
    cmd = [python_exe, script_path]
    if extra_args:
        cmd += extra_args
    cmd.append(target)
    
    result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
    print(result.stdout)
    if result.stderr:
        print(f"Error in {script_rel_path}:\n{result.stderr}", file=sys.stderr)
    return result.returncode == 0

def main():
    if len(sys.argv) < 3:
        print("Usage: python3 finalize_post.py <session_id> <file_path>")
        sys.exit(1)

    session_id = sys.argv[1]
    target = sys.argv[2]
    
    # 1. Cleanup & Norm
    if not run_script("workflows/generate-article/cleanup.py", target):
        sys.exit(1)
        
    # 2. Annotation
    if not run_script("domain/terminology/annotate_terms.py", target):
        sys.exit(1)
        
    # 3. Summarization & Redaction
    if not run_script("workflows/calibrate-guidelines/summarize.py", target):
        sys.exit(1)


    print("--- Finalization Complete ---")

if __name__ == "__main__":
    main()
