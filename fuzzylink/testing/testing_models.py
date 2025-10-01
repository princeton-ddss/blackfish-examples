from openai import OpenAI


client = OpenAI(
    api_key="EMPTY",
    base_url="http://localhost:8080/v1",
)

response = client.chat.completions.create(
                model=None,
                messages=[
                    {
                        "role": "system",
                        "content": system_message,
                    },
                    {
                        "role": "user",
                        "content": user_message,
                    },
                ],
                max_tokens=16,
                temperature=0.0,
                logprobs=True,
                top_logprobs=3,
            )

