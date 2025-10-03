##!/bin/bash

#activate the blackfish virtual environment
# source .venv/bin/activate
# echo "VE activated. Starting"

echo "Enter api-key:"
read api_key

#start a blackfish service for embeddings
echo "starting TinyLlama/TinyLlama-1.1B-Chat-v1.0 model for embeddings..."
blackfish run --gres 1 --mem 16 --ntasks-per-node 4 --time 00:30:00 --constraint 'amd&gpu40' text-generation TinyLlama/TinyLlama-1.1B-Chat-v1.0 --api-key $api_key --task embed

#start a regular text generation service
echo "starting meta-llama/Llama-3.3-70B-Instruct model for text generation..."
blackfish run --grace-period 600 --gres 4 --mem 16 --ntasks-per-node 4 --time 00:30:00  --constraint gpu80 text-generation meta-llama/Llama-3.3-70B-Instruct --api-key $api_key --revision 6f6073b423013f6a7d4d9f39144961bfbfbc386b

echo "Continue once both services are healthy!"
blackfish ls
