"""
I want a system that allows me to submit HTTP requests at a given rate, e.g., 10 requests per second, and collect the results into a single object.

"""

import time
import aiohttp
import asyncio


async def main():
    results = []
    rate_limit = 10
    num_requests = 0
    num_initial_requests = 10
    data = []
    url = "https://..."

    async def fetch(session, url, body):
        print(f"> Sending request to {url}: {body}")
        async with session.get(url, body) as res:
            callback(await res.json())

    async def callback(res):
        """Called after a request completes."""
        results.append(res)
        elapsed_time = time.time() - start_time
        avg_rate = num_requests / elapsed_time
        print(f"[{elapsed_time}] requests={num_requests}, avg_rate={avg_rate}")
        if (num_requests + 1) / (time.time() - start_time) < rate_limit:
            if i < len(data):
                fetch(url, data[i])
                i += 1

    start_time = time.time()
    time.sleep(1)
    async with aiohttp.ClientSession() as session:
        i = 0
        while i < num_initial_requests:
            fetch(session, url, data[i])
            num_requests += 1


if __name__ == "__main__":
    asyncio.run(main())
