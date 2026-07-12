import sys
import os
import re

def sync_skeleton(source_path, target_path):
    if not os.path.exists(source_path):
        print(f"Error: Source file {source_path} not found.")
        sys.exit(1)
    if not os.path.exists(target_path):
        print(f"Error: Target file {target_path} not found.")
        sys.exit(1)

    # Read source
    with open(source_path, 'r', encoding='utf-8') as f:
        source_content = f.read()

    # Extract source body
    # Sources usually have +++ front matter
    source_parts = source_content.split('+++', 2)
    if len(source_parts) >= 3:
        source_body = source_parts[2].strip()
    else:
        # Fallback if no front matter
        source_body = source_content.strip()

    # Read target
    with open(target_path, 'r', encoding='utf-8') as f:
        target_content = f.read()

    # Preserving target Front Matter
    target_parts = target_content.split('+++', 2)
    if len(target_parts) >= 3:
        front_matter = f"+++{target_parts[1]}+++"
    else:
        # If target has no front matter, use a default skeleton or just the body
        front_matter = "+++\n+++"

    # Combine
    final_content = front_matter + "\n\n" + source_body + "\n"

    # Write back
    with open(target_path, 'w', encoding='utf-8') as f:
        f.write(final_content)
    
    print(f"Successfully synced skeleton from {source_path} to {target_path}.")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 sync_skeleton.py <source_path> <target_path>")
        sys.exit(1)
    
    sync_skeleton(sys.argv[1], sys.argv[2])
