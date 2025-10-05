#!/bin/bash
set -euo pipefail
source ./env.sh

if [ ! -f "$KAGGLE_KEY" ]; then
  echo "Kaggle API key not found at $KAGGLE_KEY."
  echo "Download your Kaggle API key from https://www.kaggle.com/<your-username>/account"
  echo "and place it at $KAGGLE_KEY with permissions 600."
  exit 1
fi

mkdir -p "$LOCAL_DATA_DIR"
cd "$LOCAL_DATA_DIR"

echo "Downloading dataset..."
curl -L -O "$KAGGLE_URL"

ZIP_FILE=$(ls *.zip | head -n 1)

echo "Extracting dataset..."
unzip -qo "$ZIP_FILE" -d "$LOCAL_DATA_DIR"

echo "Transferring files to Della..."
scp -r "$LOCAL_DATA_DIR"/* "$NETID@della.princeton.edu:$REMOTE_DATA_DIR"

echo "Done."