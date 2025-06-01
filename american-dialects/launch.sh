#/bin/bash

blackfish run --mount $pwd/data --gres 1 --mem 8 --ntasks-per-node 4 --time 00:30:00 --constraint 'amd&gpu40' speech-recognition openai/whisper-large-v3
