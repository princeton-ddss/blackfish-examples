#!/bin/bash
set -euo pipefail
source ./env.sh

if [ $# -ne 1 ]; then
    echo -e "Usage: $0 [MODEL]\nAvailable models: gemma, llama"
    exit 1
fi

MODEL=$1

case $MODEL in
    llama)
        blackfish run \
            --gres 4 \
            --mem 16 \
            --ntasks-per-node 4 \
            --time 00:30:00 \
            text-generation meta-llama/Llama-3.2-11B-Vision-Instruct \
            --allowed-local-media-path "$REMOTE_DATA_DIR"
        ;;
    gemma)
        blackfish run \
            --gres 1 \
            --mem 16 \
            --ntasks-per-node 4 \
            --time 00:30:00 \
            text-generation google/gemma-3-4b-it \
            --allowed-local-media-path "$REMOTE_DATA_DIR"
        ;;
    *)
        echo "Unknown model: $MODEL"
        echo "Available models: llama, gemma"
        exit 1
        ;;
esac
