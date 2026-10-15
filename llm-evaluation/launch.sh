#!/bin/bash
# Start a Blackfish text-generation service for evaluation.
# The service is protected by BLACKFISH_API_KEY, and exposes the model under a
# short name (--served-model-name) so that Inspect model strings stay readable.
#
# Optional environment variables:
#   BLACKFISH_ACCOUNT  Slurm account to charge, e.g. export BLACKFISH_ACCOUNT=myaccount

if [ $# -lt 2 ]; then
    echo "Usage: $0 <model> <time> [profile]"
    echo "Available models: tinyllama, apertus, llama, qwen"
    exit 1
fi

if [ -z "$BLACKFISH_API_KEY" ]; then
    echo "Set BLACKFISH_API_KEY first, e.g. export BLACKFISH_API_KEY=\$(openssl rand -hex 16)"
    exit 1
fi

model=$1
time=$2
profile=${3:-default}

account=()
if [ -n "$BLACKFISH_ACCOUNT" ]; then
    account=(--account "$BLACKFISH_ACCOUNT")
fi

# run <gpus> <repo-id> <served-name>
run() {
    blackfish run --profile "$profile" "${account[@]}" \
        --gres "$1" --mem 16 --ntasks-per-node 4 --time "$time" \
        text-generation "$2" \
        --api-key "$BLACKFISH_API_KEY" --served-model-name "$3"
}

case "$model" in
    "tinyllama")
        run 1 TinyLlama/TinyLlama-1.1B-Chat-v1.0 tinyllama
        ;;
    "apertus")
        run 1 swiss-ai/Apertus-8B-Instruct-2509 apertus
        ;;
    "llama")
        run 4 meta-llama/Llama-3.3-70B-Instruct llama
        ;;
    "qwen")
        run 4 Qwen/Qwen2.5-72B-Instruct qwen
        ;;
    *)
        echo "Unknown model: $model"
        echo "Available models: tinyllama, apertus, llama, qwen"
        exit 1
        ;;
esac
