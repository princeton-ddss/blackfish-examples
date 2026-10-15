# Evaluating LLMs with Blackfish and Inspect

Before you build a research pipeline on an LLM, you should measure how well it does your task. [Inspect](https://inspect.aisi.org.uk/) is an open-source framework for writing and running LLM evaluations. Blackfish runs the model on your HPC cluster. This example connects the two: you define an evaluation on your own data, run it against a model served by Blackfish, and compare models side by side.

The task is small on purpose: classify the sentiment (positive, negative, neutral) of 30 short texts about public transit. Replace `data/transit.csv` with your own labeled data and the rest of the workflow stays the same.

## Files

| File | Purpose |
|------|---------|
| `launch.sh` | Starts a protected vLLM service on your cluster |
| `task.py` | The Inspect task: dataset, prompt, and scorer |
| `data/transit.csv` | Labeled examples (`input`, `target` columns) |
| `pyproject.toml` | Python dependencies |

## Prerequisites

- Blackfish installed and running, with a Slurm profile and the models below downloaded (see the [Blackfish docs](https://princeton-ddss.github.io/blackfish/))
- Python 3.12+ and [uv](https://docs.astral.sh/uv/) (or pip)

## 1. Start a service

Choose an API key. Blackfish passes it to the service and requires it on every request.

```shell
export BLACKFISH_API_KEY=$(openssl rand -hex 16)
export BLACKFISH_ACCOUNT=<your-slurm-account>   # optional
./launch.sh apertus 00:30:00
```

`launch.sh` knows four models: `tinyllama` (1.1B), `apertus` (8B), `llama` (70B) and `qwen` (72B). Each model must already be downloaded for your Blackfish profile (`blackfish model ls`). The small models fit on a single GPU, which makes them a cheap way to try the workflow. `launch.sh` also sets `--served-model-name apertus`. Without it, vLLM reports the model under an internal path like `/data/snapshots/<revision>`, and that path is what you would have to give Inspect.

Check on the service with `blackfish ls`. When its status is `HEALTHY`, continue.

## 2. Point Inspect at the service

Inspect talks to any OpenAI-compatible server through its `openai-api` provider. The name between the slashes (here `blackfish`) determines which environment variables it reads:

```shell
export BLACKFISH_BASE_URL=http://localhost:8080/v1
# BLACKFISH_API_KEY is already set from step 1
```

Install dependencies:

```shell
uv sync
```

## 3. Run the evaluation

```shell
uv run inspect eval task.py --model openai-api/blackfish/apertus --max-connections 16
```

`--max-connections` sets how many requests Inspect sends at once. vLLM batches concurrent requests efficiently, so raising it is the easiest way to speed up large evaluations. While developing, add `--limit 5` to run only a few samples.

Inspect prints the score (here, the fraction of texts labeled correctly, with a standard error) and saves a log of every prompt, response, and score. This run takes a few seconds.

## 4. Inspect the results

```shell
uv run inspect view
```

This opens a browser viewer where you can read individual responses and see which items the model got wrong. Reading the failures is usually the most useful part: a low score often points at an ambiguous label or a prompt problem, not just a weak model.

## 5. Compare models

Stop the first service (`blackfish stop <service-id>`), start another (`./launch.sh tinyllama 00:30:00`), and run the same task:

```shell
uv run inspect eval task.py --model openai-api/blackfish/tinyllama --max-connections 16
```

Both runs are saved in `logs/`. `inspect view` lists them together, so you can compare scores and read the responses side by side. In our run on Della (one GPU each):

| Model | Accuracy | Std. error |
|-------|----------|------------|
| `swiss-ai/Apertus-8B-Instruct-2509` | 0.97 | 0.03 |
| `TinyLlama/TinyLlama-1.1B-Chat-v1.0` | 0.53 | 0.09 |

Open the TinyLlama log and read its failures. It rarely answers with a single word. Instead it writes things like "Sentiment: Negative" or starts an explanation and never reaches a label. That is why `task.py` scores with a regular expression that takes the first label mentioned, rather than demanding an exact match. An exact-match scorer would have given TinyLlama 0.00 here, even though many of its answers contain the right label. Choosing the scorer is part of the evaluation design.

## 6. Clean up

```shell
blackfish stop <service-id>
```

Check `blackfish ls` to confirm the job has ended.

## Using your own data

1. Create a CSV with an `input` column and a `target` column.
2. Pass it to the task: `inspect eval task.py -T data=data/my_data.csv --model ...`
3. Adjust the system prompt in `task.py`, and change the `pattern()` scorer for a different [scorer](https://inspect.aisi.org.uk/scorers.html) if your answers are not one of a few labels. For free-text answers, `model_graded_qa()` uses another model as the grader, and that grader can itself be a Blackfish service.

## Notes

- Set `temperature` to 0 (the default here) for repeatable results, and record the model revision you ran. `blackfish ls` shows it.
- This example uses a tiny dataset to stay quick. For reliable comparisons, use enough samples that the standard error Inspect reports is small relative to the differences you care about.
- If a request fails with a 401 error, `BLACKFISH_API_KEY` does not match the key the service was started with.
