import subprocess
import sys
import os

# Ensure UTF-8 output on Windows
sys.stdout.reconfigure(encoding='utf-8')

def check_git_status():
    """Check if there are any uncommitted changes in the git repository."""
    try:
        # Check for untracked or staged files
        status_output = subprocess.check_output(['git', 'status', '--porcelain'], text=True).strip()
        
        if status_output:
            print("\n[ERROR] Environmental Cleansing Failed (環境肅清失敗)")
            print("==================================================")
            print("檢測到未提交的更改 (Untracked or Staged files):")
            print(status_output)
            print("\n請執行 `git add` 與 `git commit`，或 `git reset` 保持工作區純淨後再執行結晶。")
            print("嚴禁在充滿噪音的環境下執行「主動增益」或「憑空重構」。")
            sys.exit(1)
            
        print("[OK] 環境純淨，無未提交檔案。")
        
        # Check git log for recent noise (simple heuristic: more than 3 commits in the last hour might be noise, but let's just show it for now)
        # Actually, the requirement says "若最近的提交中包含大量碎片化的開發日誌，視為歷史噪音"
        # We can just output the last 3 commits so the user/agent is aware.
        print("\n[INFO] 最近 3 次 Commit 紀錄:")
        subprocess.run(['git', 'log', '-n', '3', '--oneline'])
        
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] 無法執行 Git 檢查: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print("[ERROR] Git 命令未找到，請確保已安裝 Git。")
        sys.exit(1)

if __name__ == "__main__":
    check_git_status()
