import os
import sys
import subprocess

def main():
    # Find the real engine
    script_dir = os.path.dirname(os.path.abspath(__file__)) # .agent/scripts/domain/lexicon
    engine_path = os.path.normpath(os.path.join(script_dir, "..", "..", "domain", "terminology", "engine.py"))
    
    if not os.path.exists(engine_path):
        print(f"Error: Terminology Engine not found at {engine_path}")
        sys.exit(1)
        
    # Standardize environment for UTF-8
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    
    # Pass all arguments to the real engine
    cmd = [sys.executable, engine_path] + sys.argv[1:]
    
    try:
        # Run and capture output to handle encoding properly if needed, 
        # but for a wrapper, just spanning is usually enough.
        result = subprocess.run(cmd, env=env)
        sys.exit(result.returncode)
    except Exception as e:
        print(f"Error executing terminology engine: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
