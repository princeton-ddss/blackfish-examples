import pandas as pd
from openai import OpenAI
from typing import Callable
import concurrent.futures
import sys
import os
import time


client = OpenAI(
    api_key="EMPTY",
    base_url="http://localhost:8080/v1",
)


def worker(df: pd.DataFrame, worker_id: int, batch_size: int, do_task: Callable) -> None:
    """
    Worker that processes a subset of items based on worker_id and batch_size.
    
    Args:
        df: DataFrame containing items to process
        worker_id: ID of the worker (0-indexed)
        batch_size: Number of indices each worker should process
        do_task: Function to process each index
    """
    start_idx = worker_id * batch_size
    end_idx = min(start_idx + batch_size, len(df))
    
    print(f"Worker {worker_id} processing items from {start_idx} to {end_idx-1}")
    
    for idx in range(start_idx, end_idx):
        do_task(df, idx)

def process_in_parallel(df: pd.DataFrame, num_workers: int, do_task: Callable) -> None:
    """
    Process items in parallel using multiple workers.
    
    Args:
        items: List of items to process
        num_workers: Number of workers to use
        do_task: Function to process each item
    """
    if len(df) == 0:
        print("No items to process")
        return
    
    batch_size = (len(df) + num_workers - 1) // num_workers  # Ceiling division

    print(f"Processing {len(df)} items with {num_workers} workers and batch size {batch_size}.\n")

    start = time.time()
    start_utc = time.gmtime(start)
    print(f"Start time: {time.strftime('%Y-%m-%d %H:%M:%S', start_utc)}")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = [
            executor.submit(worker, df, worker_id, batch_size, do_task)
            for worker_id in range(num_workers)
        ]
        
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"Worker error: {e}")

    end = time.time()
    end_utc = time.gmtime(end)
    print(f"End time: {time.strftime('%Y-%m-%d %H:%M:%S', end_utc)}")
    print(f"Elapsed time: {end - start:.2f} seconds")


if __name__ == "__main__":

    if len(sys.argv) < 2:
        print("Error: Please provide a task name as an argument")
        print("Valid tasks: tweets, ads, manifestos, speeches")
        sys.exit(1)

    task = sys.argv[1]

    valid_tasks = ["tweets", "ads", "manifestos", "speeches"]
    if task not in valid_tasks:
        print(f"Error: '{task}' is not a valid task")
        print(f"Valid tasks: {', '.join(valid_tasks)}")
        sys.exit(1)

    if len(sys.argv) < 3:
        print("Error: Please provide a model name as the second argument")
        sys.exit(1)

    model = sys.argv[2]

    print(f"Running task {task} with model {model}")

    if task == "tweets":
        tweets = pd.read_csv("data/application1-TweetNLP.csv", index_col=0)
        system_message = """
        You are a helpful assistant. I will present you with tweets posted the day after the US Supreme Court ruled in favor of a baker who refused to bake a wedding cake for a same-sex couple. For each tweet, decide whether its sentiment is Positive, Neutral, or Negative as in the examples shown below. Give a one word response.

        Tweet: #SCOTUS set a dangerous precedent today. Although the Court limited the scope to which a business owner could deny services to patrons, the legal argument has been legitimized that one's subjective religious convictions trump (no pun intended) #humanrights.
        Sentiment: Negative

        Tweet: Thank you Supreme Court I take pride in your decision!!!!! #SCOTUS
        Sentiment: Positive

        Tweet: Supreme Court rules in favor of baker who would not make wedding cake for gay couple
        Sentiment: Neutral

        Tweet: Supreme Court rules in favorr of Colorado baker! This day is getting better by the minute!
        Sentiment: Positive

        Tweet: Can't escape the awful irony of someone allowed to use religion to discriminate against people in love. Not my Jesus. #opentoall #SCOTUS #Hypocrisy #MasterpieceCakeshop
        Sentiment: Negative

        Tweet: I can't believe this cake case went all the way to #SCOTUS . Can someone let me know what cake was ultimately served at the wedding? Are they married and living happily ever after?
        Sentiment: Neutral
        """

        def label_tweet(tweets: pd.DataFrame, idx: int) -> None:
            tweet = tweets.at[idx, 'raw.text']
            print(f"[{idx}] Processing tweet: {tweet}")
            
            if tweet is None:
                print("> No text found. Skipping.")
                return
            
            response = client.chat.completions.create(
                model=None,
                messages=[
                    {
                        "role": "system",
                        "content": system_message,
                    },
                    {
                        "role": "user",
                        "content": f"Tweet: {tweet}"
                    },
                ],
                max_tokens=16,
                temperature=0.0,
                logprobs=True,
                top_logprobs=3,
            )
            
            choices = response.choices[0].logprobs.content[0].top_logprobs
            tweets.at[idx, 'choice_1'] = choices[0].token
            tweets.at[idx, 'logprob_1'] = choices[0].logprob
            tweets.at[idx, 'choice_2'] = choices[1].token
            tweets.at[idx, 'logprob_2'] = choices[1].logprob
            tweets.at[idx, 'choice_3'] = choices[2].token
            tweets.at[idx, 'logprob_3'] = choices[2].logprob

        process_in_parallel(tweets, num_workers=os.cpu_count(), do_task=label_tweet)
        tweets.to_csv(f"data/tweets-{model}.csv", index=False)

    elif task == "ads":
        ads = pd.read_csv("data/application2-carlson-montgomery-2017.csv")
        system_message = """
        You are a helpful assistant. I will provide you with the text of political advertisements. For each ad, decide whether its tone is Positive, Negative, or Neutral. Give a one-word response as in the example below.

        Ad Text: [Announcer]: Mark Udall claims he voted for tax cuts 65 times.
        [Reporter]: "Actually it's not true."
        [Mark Udall]: "I'm just kidding."
        Udall claims that now he supports our troops, drilling off shore, bi-partisanship.
        [Mark Udall]: "I'm just kidding."
        [Announcer]: But through his career he has opposed them all. Udall has a lot of ads, but a shortage of truth.
        [Mark Udall]: "I'm just kidding."
        [Announcer]: Mark Udall is not honest about his past and now it's catching up with him.
        The National Republican Senatorial Committee is responsible for the content of this advertising.
        [PFB]: NATIONAL REPUBLICAN SENATORIAL COMMITTEE (9)
        Tone: Negative
        """
        def label_ad(ads: pd.DataFrame, idx: int) -> None:
            ad = ads.at[idx, 'text']
            print(f"[{idx}] Processing ad: {ad}")
            
            if ad is None:
                print("> No text found. Skipping.")
                return
            
            response = client.chat.completions.create(
                model=None,
                messages=[
                    {
                        "role": "system",
                        "content": system_message,
                    },
                    {
                        "role": "user",
                        "content": f"Ad: {ad}\nTone:"
                    },
                ],
                max_tokens=16,
                temperature=0.0,
                logprobs=True,
                top_logprobs=3,
            )
            
            choices = response.choices[0].logprobs.content[0].top_logprobs
            ads.at[idx, 'choice_1'] = choices[0].token
            ads.at[idx, 'logprob_1'] = choices[0].logprob
            ads.at[idx, 'choice_2'] = choices[1].token
            ads.at[idx, 'logprob_2'] = choices[1].logprob
            ads.at[idx, 'choice_3'] = choices[2].token
            ads.at[idx, 'logprob_3'] = choices[2].logprob

        process_in_parallel(ads, num_workers=os.cpu_count(), do_task=label_ad)
        ads.to_csv(f"data/ads-{model}.csv", index=False)

    elif task == "manifestos":
        manifestos = pd.read_csv("data/application3-one-shot-gpt-3-ideology.csv", index_col=0)
        system_message = """
        You are a helpful assistant. I will provide you with examples of British political manifestos. Classify each manifesto as either Lib (for Liberal), Con (for Conservative), or Neither. Give a one-word response as in the example below.

        Sentence: We will implement a comprehensive strategy for ending low pay, notably by the introduction of a statutory national minimum wage.
        Classification: Lib
        """

        def label_manifesto(manifestos: pd.DataFrame, idx: int) -> None:
            manifesto = manifestos.at[idx, 'sentence_text']
            print(f"[{idx}] Processing manifesto: {manifesto}")
            
            if manifesto is None:
                print("> No text found. Skipping.")
                return
            
            response = client.chat.completions.create(
                model=None,
                messages=[
                    {
                        "role": "system",
                        "content": system_message,
                    },
                    {
                        "role": "user",
                        "content": f"Sentence: {manifesto}\nClassification:"
                    },
                ],
                max_tokens=16,
                temperature=0.0,
                logprobs=True,
                top_logprobs=3,
            )
            
            choices = response.choices[0].logprobs.content[0].top_logprobs
            manifestos.at[idx, 'choice_1'] = choices[0].token
            manifestos.at[idx, 'logprob_1'] = choices[0].logprob
            manifestos.at[idx, 'choice_2'] = choices[1].token
            manifestos.at[idx, 'logprob_2'] = choices[1].logprob
            manifestos.at[idx, 'choice_3'] = choices[2].token
            manifestos.at[idx, 'logprob_3'] = choices[2].logprob

        process_in_parallel(manifestos, num_workers=os.cpu_count(), do_task=label_manifesto)
        manifestos.to_csv(f"data/manifestos-{model}.csv", index=False)

    elif task == "speeches":
        speeches = pd.read_csv("data/application4-one-shot-gpt-3.csv", index_col=0)
        system_message = """
        You are a helpful assistant. I will provide you with examples of Congressional speeches. You should return a list of virtues that they praise as in the following example.

        Speech: Mr. Speaker, I rise today to honor Reagan Myers from Poplar Bluff, Missouri for his years of service with the Salvation Army. Reagan Myers is being honored as the 2014 Mariana Islands Young Citizen of the Year. This award is not easily attained, and can only be achieved by demonstrating a selfless passion for serving and a giving heart. Reagan and his family are serving as missionaries under the auspices of General Baptist International Missions. At only 16 years old, Reagan has demonstrated his commitment to serving those in need in Saipan. Over the past year he has donated many of his own items to the Salvation Army, he has volunteered his time to help in the soup kitchen, and ring the bell at the red kettle location. Reagan has led efforts to provide relief to families who suffered from Typhoon Vongfong. With support from his church, he provides baskets to families in need filled with food, toys, and Bibles. Reagan Myers is a role model for young and old alike, and it is my pleasure to recognize his achievements before the House of Representatives.
        Virtues: service, achievement, selflessness, passion, commitment, charity, volunteerism, compassion
        """

        def categorize_speech(speeches: pd.DataFrame, idx: int) -> None:
            speech = speeches.at[idx, 'speech']
            print(f"[{idx}] Processing speech: {speech}")
            
            if speech is None:
                print("> No text found. Skipping.")
                return
            
            response = client.chat.completions.create(
                model=None,
                messages=[
                    {
                        "role": "system",
                        "content": system_message,
                    },
                    {
                        "role": "user",
                        "content": f"Ad: {speech}"
                    },
                ],
                max_tokens=16,
                temperature=0.0,
            )
            
            speeches.at[idx, 'topics'] = response.choices[0].message.content

        process_in_parallel(speeches, num_workers=os.cpu_count(), do_task=categorize_speech)
        speeches.to_csv(f"data/speeches-{model}.csv", index=False)
