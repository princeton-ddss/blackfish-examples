"""Classify the sentiment of short texts about public transit.

Bring your own data: this task reads a CSV with an `input` column (the text
shown to the model) and a `target` column (the correct answer).
"""

from pathlib import Path

from inspect_ai import Task, task
from inspect_ai.dataset import csv_dataset
from inspect_ai.scorer import pattern
from inspect_ai.solver import generate, system_message

SYSTEM = (
    "You are a careful annotator. Classify the sentiment of the text toward "
    "public transit as exactly one of: positive, negative, neutral. "
    "Respond with that single word and nothing else."
)


@task
def transit_sentiment(data: str = "data/transit.csv", temperature: float = 0.0):
    path = Path(__file__).parent / data
    return Task(
        dataset=csv_dataset(str(path)),
        solver=[system_message(SYSTEM), generate(temperature=temperature, max_tokens=32)],
        # Take the first label mentioned, so chatty answers like "Sentiment: Negative"
        # still count. Small models often ignore "respond with one word".
        scorer=pattern(r"(positive|negative|neutral)"),
    )
