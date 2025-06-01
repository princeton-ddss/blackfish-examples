from openai import OpenAI
import pandas as pd
import sys

openai_api_key = "EMPTY"
openai_api_base = "http://localhost:8080/v1"

client = OpenAI(
    api_key=openai_api_key,
    base_url=openai_api_base,
)

system_message = "You are a helpful assistant that helps to understand data. The text you'll have to provide an explanation for is extracted from building permit filings. You have to return a clear sentence that describes what the construction work was about according to the text."

models = {
    "gemma": "GEMMA_3_27B_IT",
    "llama": "LLAMA_3_70B_INSTRUCT",
    "qwen": "QWEN_2.5_72b_INSTRUCT",
}

if __name__ == "__main__":
    df = pd.read_csv("./corrected_chunk_1.csv", index_col=0)
    df.columns = ["ID", "DESCRIPTION", "CHATGPT"]

    if len(sys.argv) > 1:
        model_key = sys.argv[1]
        if model_key in models:
            model = models[model_key]
        else:
            print(f"Unknown model: {model_key}. Available models: {list(models.keys())}")
            sys.exit(1)
    else:
        print(f"Please provide a model name. Available models: {list(models.keys())}")
        sys.exit(1)

    df[model] = None
    
    for idx, row in df.iterrows():
        text = row["DESCRIPTION"]
        print(f"[{idx}] Processing text: {text}")
        response = client.chat.completions.create(
            model=None,
            messages=[
                {
                    "role": "system",
                    "content": system_message
                },
                {
                    "role": "user",
                    "content": f"Provide a single sentence description of the following: {text}",
                },
            ],
            max_tokens=100,
            temperature=0.7,
        )
        df.at[idx, model] = response.choices[0].message.content.strip()

    df.to_csv("./corrected_chunk_1_comparison.csv", index=False)
