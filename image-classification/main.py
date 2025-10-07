import os
import requests
import json
from pathlib import Path

url = "http://localhost:8080/v1/chat/completions"
headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer image-classification-example"
}

LOCAL_DIR = os.getenv("LOCAL_DATA_DIR", "./data")
REMOTE_DIR = os.getenv("REMOTE_DATA_DIR", "/home/your_netid/image-classification-example")
OUTPUT_DIR = "./responses"

if __name__ == "__main__":
    local_path = Path(LOCAL_DIR)
    output_path = Path(OUTPUT_DIR)

    if not local_path.exists():
        print(f"Local directory {LOCAL_DIR} does not exist.")
        exit(1)

    output_path.mkdir(parents=True, exist_ok=True)

    for idx, filename in enumerate(sorted(local_path.iterdir())):
        if not filename.suffix.lower() in (".png", ".jpg", ".jpeg", ".gif"):
            continue

        remote_path = os.path.join(REMOTE_DIR, filename.name)
        print(f"[{idx}] Sending request for: {filename.name}")

        payload = {
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "What animal is in this image?"},
                        {"type": "image_url", "image_url": {"url": f"file:{remote_path}"}}
                    ]
                }
            ],
            "max_tokens": 200,
            "temperature": 0.1,
            "stream": False
        }

        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Request failed for {filename.name}: {e}")
            continue

        out_data = {
            "image": filename.name,
            "remote_path": remote_path,
            "prediction": response.json()
        }

        out_file = output_path / f"{filename.stem}.json"
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(out_data, f, indent=2)

        print(f"Saved: {out_file}")
        