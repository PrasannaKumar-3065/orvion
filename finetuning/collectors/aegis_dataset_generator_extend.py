"""
AEGIS DATASET GENERATOR — Extended (New Sites)
================================================
Runs ONLY the new site flows from aegis_flows_new_sites.py.
Output appends to aegis_generated_new_sites.jsonl — keep separate
from your existing dataset until you've reviewed the records.

Usage:
  pip install playwright && playwright install chromium
  python3 aegis_generator_extended.py

Then merge:
  cat aegis_generated_fixed.jsonl aegis_generated_new_sites.jsonl > aegis_merged.jsonl

Sites covered:
  1. the-internet.herokuapp.com   (~86 records)
  2. practice.expandtesting.com   (~60 records)
  3. uitestingplayground.com      (~61 records)

NOTE: uitestingplayground.com uses http:// not https://.
      The generator is configured to allow this.
"""

import asyncio
import sys
import os

# ── Import the core generator engine ────────────────────────────────────────
# We re-use everything from aegis_dataset_generator.py except we swap the flows.
# This avoids duplicating 300 lines of browser/DOM/record-building code.

sys.path.insert(0, os.path.dirname(__file__))

from aegis_dataset_generator import (
    execute_flow,
    async_playwright,
)
from aegis_flows_new_sites import ALL_NEW_FLOWS

OUTPUT_FILE = "aegis_generated_new_sites.jsonl"


async def main():
    flows = ALL_NEW_FLOWS
    total_steps = sum(len(f["steps"]) for f in flows)

    print(f"\n🚀 AEGIS Dataset Generator — New Sites Extension")
    print(f"   Output:  {OUTPUT_FILE}")
    print(f"   Flows:   {len(flows)}")
    print(f"   Records: ~{total_steps} (one per step)")
    print(f"\n   Sites:")
    print(f"     • the-internet.herokuapp.com")
    print(f"     • practice.expandtesting.com")
    print(f"     • uitestingplayground.com\n")

    total_records = 0
    failed_flows = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            ignore_https_errors=True,   # needed for uitestingplayground.com (http)
        )
        page = await context.new_page()

        with open(OUTPUT_FILE, "w") as f:
            for i, flow in enumerate(flows):
                print(f"\n[{i+1}/{len(flows)}] {flow['name']}")
                try:
                    count = await execute_flow(page, flow, f)
                    total_records += count
                    print(f"  → {count} records written")
                except Exception as e:
                    print(f"  ✗ FAILED: {e}")
                    failed_flows.append((flow["name"], str(e)))
                    continue

        await browser.close()

    print(f"\n{'='*60}")
    print(f"✅ Done!  {total_records} records written to {OUTPUT_FILE}")

    if failed_flows:
        print(f"\n⚠  {len(failed_flows)} flow(s) failed:")
        for name, err in failed_flows:
            print(f"   • {name}: {err}")

    print(f"""
Next steps:
  1. Review a sample:
       head -n 5 {OUTPUT_FILE} | python3 -m json.tool | head -60

  2. Merge with existing dataset:
       cat aegis_generated_fixed.jsonl {OUTPUT_FILE} > aegis_merged.jsonl

  3. Weighted merge (2x Aegis-specific, 1x perfect):
       cat aegis_merged.jsonl aegis_merged.jsonl aegis_final_perfect.jsonl > aegis_train_final.jsonl

  4. Shuffle:
       python3 -c "
       import json, random
       lines = open('aegis_train_final.jsonl').readlines()
       random.shuffle(lines)
       open('aegis_train_shuffled.jsonl','w').writelines(lines)
       print(f'Final training set: {{len(lines)}} records')
       "
{'='*60}
""")


if __name__ == "__main__":
    asyncio.run(main())