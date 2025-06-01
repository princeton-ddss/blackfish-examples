# Stochastic Parrot
Replication code for "How to train your stochastic parrot" () with Blackfish.

## Data
The original data is available from [Dataverse](). The files we use here are:
```shell
application1-TweetNLP.csv
application2-carlson-montgomery-2017.csv
application3-one-shot-gpt-3-ideology.csv
application4-one-shot-gpt-3.csv
```

## Usage
1. Start an LLM service using the launch script, e.g.:
```shell
./launch.sh qwen 00:59:00
```
2. Once the service is ready, run the python script:
```shell
python main.py tweets qwen-2.5-72b-it
```