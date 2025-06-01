#!/bin/bash

if [ $# -lt 2 ]; then
    echo "Usage: $0 <model> <time>"
    echo "Available models: llama, qwen, gemma"
    exit 1
fi

model=$1
time=$2

if [ $# -ge 3 ]; then
    profile=$3
else
    profile="default"
fi

case "$model" in
    "llama")
        blackfish run --profile "$profile" --gres 4 --mem 16 --ntasks-per-node 4 --time "$time" --constraint 'gpu80' text-generation meta-llama/Llama-3.3-70B-Instruct
        ;;
    "qwen")
        blackfish run --profile "$profile" --gres 4 --mem 16 --ntasks-per-node 4 --time "$time" --constraint 'gpu80' text-generation Qwen/Qwen2.5-72B-Instruct
        ;;
    "gemma")
        blackfish run --profile "$profile" --gres 1 --mem 16 --ntasks-per-node 4 --time "$time" --constraint 'gpu80' text-generation google/gemma-3-27b-it
        ;;
    *)
        echo "Unknown model: $model"
        echo "Available models: llama, qwen, gemma"
        exit 1
        ;;
esac
