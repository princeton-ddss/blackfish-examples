##!/bin/bash

#activate the blackfish virtual environment
# source .venv/bin/activate
# echo "VE activated. Starting"

echo "Enter api-key:"
read api_key

#start a blackfish service for embeddings
blackfish run --gres 1 --mem 16 --ntasks-per-node 4 --time 00:30:00 --constraint 'amd&gpu40' text-generation TinyLlama/TinyLlama-1.1B-Chat-v1.0 --api-key sealsaretasty --task embed

#wait until one of the services is healthy to proceed
while true; do
  if blackfish ls | grep -q "HEALTHY"; then
    echo "Service is HEALTHY. Proceeding..."
    break
  else
    echo "Service not yet HEALTHY. Waiting..."
    sleep 45
  fi
done

blackfish ls

echo "Continue momentarily"