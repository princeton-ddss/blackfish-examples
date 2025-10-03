##!/bin/bash

#activate the blackfish virtual environment
# source .venv/bin/activate
# echo "VE activated. Starting"

echo -n "Enter api-key (or press enter for none):"
read api_key


#start a blackfish service for embeddings
echo -e "\nstarting TinyLlama/TinyLlama-1.1B-Chat-v1.0 model for embeddings..."

if [ -z "$api_key" ]
then
	blackfish run --gres 1 --mem 16 --ntasks-per-node 4 --time 00:30:00 --constraint 'amd&gpu40' text-generation TinyLlama/TinyLlama-1.1B-Chat-v1.0 --task embed --name embedding-model	
else
	blackfish run --gres 1 --mem 16 --ntasks-per-node 4 --time 00:30:00 --constraint 'amd&gpu40' text-generation TinyLlama/TinyLlama-1.1B-Chat-v1.0 --api-key $api_key --task embed --name embedding-model
fi

#start a regular text generation service
echo -e "\nstarting meta-llama/Llama-3.3-70B-Instruct model for text generation..."

if [ -z "$api_key" ]
then
	blackfish run --grace-period 600 --gres 4 --mem 16 --ntasks-per-node 4 --time 00:30:00  --constraint gpu80 text-generation meta-llama/Llama-3.3-70B-Instruct --revision 6f6073b423013f6a7d4d9f39144961bfbfbc386b --name text-gen-model
else
	blackfish run --grace-period 600 --gres 4 --mem 16 --ntasks-per-node 4 --time 00:30:00  --constraint gpu80 text-generation meta-llama/Llama-3.3-70B-Instruct --api-key $api_key --revision 6f6073b423013f6a7d4d9f39144961bfbfbc386b --name text-gen-model
fi


echo -e "\nContinue once both services are healthy!\n"
blackfish ls
