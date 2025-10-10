#!/bin/bash
set -euo pipefail
source ./env.sh

if [ ! -f "$KAGGLE_KEY" ]; then
  echo "Kaggle API key not found at $KAGGLE_KEY."
  echo "Download your Kaggle API key from https://www.kaggle.com/<your-username>/account"
  echo "and place it at $KAGGLE_KEY with permissions 600."
  exit 1
fi

TMP_DIR=".tmp_extract"
ZIP_FILE_NAME="dataset.zip"

echo "Downloading dataset..."
mkdir -p "$TMP_DIR"
curl -L -o "$TMP_DIR/$ZIP_FILE_NAME" "$KAGGLE_URL"

echo "Extracting dataset..."
unzip -qo "$TMP_DIR/$ZIP_FILE_NAME" -d "$TMP_DIR"

# Find the actual 'animals' directory
ANIMALS_SRC=$(find "$TMP_DIR" -type d -name "animals" | head -n 1)

if [ -z "$ANIMALS_SRC" ]; then
  echo "Error: could not find 'animals' directory in the unzip archive."
  exit 1
fi

# Move it to the final local dataset location
rm -rf "$LOCAL_DIR"
mkdir -p "$LOCAL_DIR"
mv "$ANIMALS_SRC" "$LOCAL_DIR/animals"

# Clean up temporary files
rm -rf "$TMP_DIR"

# Generate labels.csv locally
echo "Generating labels.csv..."
LABELS_FILE="$LOCAL_DIR/labels.csv"
echo "image,label" > "$LABELS_FILE"
find "$LOCAL_DIR/animals" -type f \( -iname "*.jpg" -o -iname "*.png" -o -iname "*.jpeg" \) | while read -r img; do
  label=$(basename "$(dirname "$img")")
  rel_path=$(realpath --relative-to="$LOCAL_DIR" "$img")
  echo "$rel_path,$label" >> "$LABELS_FILE"
done

# Ensure remote directory exists
ssh "$NETID@della.princeton.edu" "mkdir -p '$REMOTE_DIR'"

echo "Transferring images to Della..."
scp -r "$LOCAL_DIR/animals" "$NETID@della.princeton.edu:$REMOTE_DIR"

echo "----------------------------------------"
echo "Download complete."
echo "Local dataset: $(pwd)/$LOCAL_DIR/animals"
echo "Remote dataset: $REMOTE_DIR/animals"
echo "Local labels: $(pwd)/$LABELS_FILE"
echo "----------------------------------------"
