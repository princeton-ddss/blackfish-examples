import requests
import os

url = "https://localhost:8080/transcribe"

if __name__ == "__main__":

    if not os.path.exists("./data/"):
        print("Data directory does not exist. Run the download script and re-try.")
        exit(1)

    if not os.path.exists("./text/"):
        os.mkdir("./text/")
        print("Created directory ./text/")

    for idx, filename in enumerate(os.listdir("./data/")):
        print(f"[{idx}] Processing filename: {filename}")
        root, ext = os.path.splitext(filename)
        response = requests.get(url, data={
            "audio_file": os.path.join("/data/audio/", filename),
            "response_format": "json",
            "language": "en",
        })

        if response.status_code == 200:
            with open(f"./data/{root}.json", "w", encoding="utf-8") as f:
                f.write(response.text)
            print("File transcribed successfully.")
        else:
            print(f"Failed to transcribe file. Status code: {response.status_code}")
