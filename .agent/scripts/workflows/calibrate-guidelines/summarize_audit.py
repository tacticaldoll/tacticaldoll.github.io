import os
import json
import sys
import collections

if os.path.exists('audit_results.json'):
    with open('audit_results.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
else:
    print("Error: audit_results.json not found. Run audit_lexicon.py first.")
    sys.exit(1)

unanchored_total = []
all_candidates = collections.Counter()
term_stats = collections.defaultdict(lambda: {"count": 0, "anchored": 0, "total_posts": 0})

for post, results in data.items():
    for item in results["found_terms"]:
        term = item["term"]
        term_stats[term]["count"] += item["count"]
        term_stats[term]["total_posts"] += 1
        if item["is_anchored"]:
            term_stats[term]["anchored"] += 1
        else:
            unanchored_total.append((post, term))
            
    for cand in results["possible_candidates"]:
        all_candidates[cand] += 1

print("--- UNANCHORED FIRST-OCCURRENCES ---")
for post, term in unanchored_total:
    print(f"{post}: {term}")

print("\n--- TOP CANDIDATES (Frequency > 3) ---")
for cand, count in all_candidates.most_common():
    if count > 3:
        print(f"{cand}: {count}")

print("\n--- TERM USAGE STATS ---")
for term, stats in term_stats.items():
    print(f"{term}: {stats['count']} occurrences across {stats['total_posts']} posts (Anchored first-use in {stats['anchored']}/{stats['total_posts']} posts)")

# Clean up audit_results.json after consumption
try:
    os.remove('audit_results.json')
    print("\nINFO: Cleaned up temporary audit_results.json")
except Exception as e:
    pass

