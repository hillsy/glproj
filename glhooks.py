#!/usr/bin/env python

import json
import sys
import asyncio
import aiohttp
from aiohttp_retry import RetryClient, ExponentialRetry

# Load JSON input from stdin
json_input = sys.stdin.read()
data = json.loads(json_input)

# Load GitLab auth token from token.txt
with open('token.txt', 'r') as f:
    gitlab_private_token = f.read().strip()

# Set GitLab API endpoint
gitlab_api_endpoint = "https://gitlab.com/api/v4"

# TODO: implement logging to stderr & with levels
async def fetch_project_webhooks(session, project_id):
    url = f"{gitlab_api_endpoint}/projects/{project_id}/hooks"
    headers = {"Private-Token": gitlab_private_token}
    try:
        async with session.get(url, headers=headers) as response:
                response.raise_for_status()
                return await response.json()
    except (aiohttp.ClientError, aiohttp.ClientResponseError) as e:
        print(f"HTTP error occurred: {e}")
        raise
    except asyncio.TimeoutError as e:
        print(f"Connection timeout occurred: {e}")
        raise

async def process_project(session, project):
    project_id = project["id"]
    project_url = project["url"]
    webhooks = await fetch_project_webhooks(session, project_id)
    hooks = []
    for webhook in webhooks:
        hook = webhook.copy()
        hook["project_url"] = project_url
        hooks.append(hook)
    return hooks

async def main():
    retry_options = ExponentialRetry(attempts=10)
    async with RetryClient(raise_for_status=False, retry_options=retry_options) as session:
        tasks = [process_project(session, project) for project in data["projects"]]
        results = await asyncio.gather(*tasks)
        # flatten the list of lists into a single list
        # this is necessary because asyncio.gather returns a list of lists
        # and we want a single list of all the webhooks
        hooks = [hook for sublist in results for hook in sublist]
        print(json.dumps({"hooks": hooks}))

asyncio.run(main())
