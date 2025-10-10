#!/usr/bin/env python3
import csv
import os
from pathlib import Path

LOCAL_DIR = Path(os.getenv("LOCAL_DIR"))
RESPONSES_DIR = LOCAL_DIR / "responses"
LABELS_FILE = LOCAL_DIR / "labels.csv"

labels = {}
with open(LABELS_FILE, newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        image_path = Path(row["image"]).as_posix()
        label = row["label"].strip().lower()
        labels[image_path] = label

if not labels:
    print("No labels found in labels.csv.")
    exit(1)

csv_files = sorted(RESPONSES_DIR.glob("*.csv"))
if not csv_files:
    print(f"No response CSVs found in {RESPONSES_DIR}")
    exit(1)

print(f"\nFound {len(csv_files)} output file(s) in {RESPONSES_DIR}.")

for response_file in csv_files:
    print(f"\nEvaluating: {response_file.name}")

    total = 0
    correct = 0
    unmatched = 0

    with open(response_file, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            image_rel = Path(row["image"]).as_posix()
            prediction = row["prediction"].strip().lower()

            if image_rel not in labels:
                unmatched += 1
                continue

            total += 1
            true_label = labels[image_rel]
            if prediction == true_label:
                correct += 1

    accuracy = (correct / total * 100) if total else 0.0

    print(f"Correct: {correct}/{total} ({accuracy:.2f}%)")
    if unmatched:
        print(f"{unmatched} images not found in labels.csv")
