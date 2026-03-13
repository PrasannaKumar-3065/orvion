import json
import re
import os

# --- CONFIGURATION ---
INPUT_FILE = "marker_dataset_10k.jsonl"
OUTPUT_FILE = "marker_dataset_10k_normalized.jsonl"

IMAGE_WIDTH = 1920
IMAGE_HEIGHT = 1080
# ---------------------

def normalize_dataset():
    processed_records = 0
    negatives = 0
    positives = 0
    out_of_bounds = 0

    with open(INPUT_FILE, 'r') as infile, open(OUTPUT_FILE, 'w') as outfile:
        for line in infile:
            if not line.strip(): continue
            
            record = json.loads(line)
            assistant_msg = record['messages'][-1]['content'].strip()
            
            # 1. Handle explicit Hard Negatives
            if assistant_msg == "(-1, -1)":
                record['messages'][-1]['content'] = "<|not_found|>"
                negatives += 1
            else:
                # 2. Updated Regex to handle negative numbers like -12
                # The r'(-?\d+)' part allows an optional minus sign
                match = re.search(r'\((-?\d+),\s*(-?\d+)\)', assistant_msg)
                
                if match:
                    x_abs = int(match.group(1))
                    y_abs = int(match.group(2))
                    
                    # 3. Check if coordinate is actually on the screen
                    if x_abs < 0 or y_abs < 0 or x_abs > IMAGE_WIDTH or y_abs > IMAGE_HEIGHT:
                        # If it's off-screen, it's effectively "Not Found" for a Vision model
                        record['messages'][-1]['content'] = "<|not_found|>"
                        out_of_bounds += 1
                    else:
                        # 4. Normalize valid on-screen coordinates
                        x_norm = max(0, min(1000, int((x_abs / IMAGE_WIDTH) * 1000)))
                        y_norm = max(0, min(1000, int((y_abs / IMAGE_HEIGHT) * 1000)))
                        record['messages'][-1]['content'] = f"<|point_start|>({x_norm}, {y_norm})<|point_end|>"
                        positives += 1
                else:
                    # This will catch anything that doesn't fit the (x, y) pattern
                    record['messages'][-1]['content'] = "<|not_found|>"
                    negatives += 1
                
            outfile.write(json.dumps(record) + '\n')
            processed_records += 1

    print(f"\nDone! Processed {processed_records} records.")
    print(f"Valid Points: {positives}")
    print(f"Hard Negatives: {negatives}")
    print(f"Off-screen elements moved to 'not_found': {out_of_bounds}")

if __name__ == "__main__":
    normalize_dataset()