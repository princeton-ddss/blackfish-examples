#!/usr/bin/env python3
import os
import csv
import time
import requests
from pathlib import Path

# Environment (from env.sh)
LOCAL_DIR = Path(os.getenv("LOCAL_DIR", "data"))
REMOTE_DIR = os.getenv("REMOTE_DIR", "")

# Configuration
API_URL = "http://localhost:8080/v1/chat/completions"
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": "Bearer image-classification-example"
}

ANIMALS_DIR = LOCAL_DIR / "animals"
OUTPUT_CSV = LOCAL_DIR / "responses" / "meta-llama-Llama-3.2-11B-Vision-Instruct-responses.csv"
OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)

ANIMAL_NAMES = [
    "antelope","badger","bat","bear","bee","beetle","bison","boar","butterfly",
    "cat","caterpillar","chimpanzee","cockroach","cow","coyote","crab","crow",
    "deer","dog","dolphin","donkey","dragonfly","duck","eagle","elephant",
    "flamingo","fly","fox","goat","goldfish","goose","gorilla","grasshopper",
    "hamster","hare","hedgehog","hippopotamus","hornbill","horse","hummingbird",
    "hyena","jellyfish","kangaroo","koala","ladybugs","leopard","lion","lizard",
    "lobster","mosquito","moth","mouse","octopus","okapi","orangutan","otter",
    "owl","ox","oyster","panda","parrot","pelecaniformes","penguin","pig",
    "pigeon","porcupine","possum","raccoon","rat","reindeer","rhinoceros",
    "sandpiper","seahorse","seal","shark","sheep","snake","sparrow","squid",
    "squirrel","starfish","swan","tiger","turkey","turtle","whale","wolf",
    "wombat","woodpecker","zebra"
]

PROMPT = (
    "Identify the main animal in this image. Respond with only one word "
    f"from this list: {', '.join(ANIMAL_NAMES)}. If none match, respond with 'unknown'."
)

def predict(img_path: Path, remote_path: str) -> str:
    print(f"\nSending request for: {img_path.name} with remote file path: {remote_path}")

    payload = {
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": PROMPT},
                {"type": "image_url", "image_url": {"url": f"file:{remote_path}"}}
            ]
        }],
        "max_tokens": 50,
        "temperature": 0.1,
        "stream": False
    }

    try:
        r = requests.post(API_URL, headers=HEADERS, json=payload, timeout=15)
        r.raise_for_status()
        return (
            r.json().get("choices", [{}])[0]
            .get("message", {}).get("content", "").strip() or "unknown"
        )
    except Exception as e:
        print(f"Request failed for {img_path.name}: {e}")
        return "error"

def main():
    start_time = time.time()

    if not ANIMALS_DIR.exists():
        raise SystemExit(f"{ANIMALS_DIR} not found. Run download.sh first.")

    print(f"Processing images in {ANIMALS_DIR}")
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["image", "remote_path", "prediction"])

        for cls_dir in sorted(ANIMALS_DIR.iterdir()):
            if not cls_dir.is_dir():
                continue
            print(f"\nProcessing {cls_dir.name}")

            for img_path in sorted(cls_dir.glob("*.[jp][pn]g")):
                remote_path = f"{REMOTE_DIR.rstrip('/')}/{img_path}"
                prediction = predict(img_path, remote_path)
                writer.writerow([img_path, remote_path, prediction])

    total_time = time.time() - start_time
    print(f"\nDone. Results saved to {OUTPUT_CSV}")
    print(f"Total run time: {total_time:.2f} seconds")

if __name__ == "__main__":
    main()