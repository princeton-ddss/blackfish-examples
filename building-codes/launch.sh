#/bin/bash

if [ $# -ne 1 ]; then
    echo "Usage: $0 [MODEL]>\n"
    echo "Available models: llama, qwen, gemma"
    exit 1
fi

MODEL=$1

case $MODEL in
    llama)
        blackfish run --gres 4 --mem 16 --ntasks-per-node 4 --time 00:30:00 --constraint 'gpu80' text-generation meta-llama/Llama-3.3-70B-Instruct
        ;;
    qwen)
        blackfish run --gres 4 --mem 16 --ntasks-per-node 4 --time 00:30:00 --constraint 'gpu80' text-generation Qwen/Qwen2.5-72B-Instruct
        ;;
    gemma)
        blackfish run --gres 1 --mem 16 --ntasks-per-node 4 --time 00:30:00 --constraint 'gpu80' text-generation google/gemma-3-27b-it
        ;;
    *)
        echo "Unknown model: $MODEL"
        echo "Available models: llama, qwen, gemma"
        exit 1
        ;;
esac
