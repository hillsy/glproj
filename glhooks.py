#!/usr/bin/env python

import json
import sys
import asyncio
import logging
from aiohttp_retry import RetryClient, ExponentialRetry

# Load JSON input from stdin
json_input = sys.stdin.read()
data = json.loads(json_input)

# Load GitLab auth token from token.txt
with open('token.txt', 'r') as f:
    gitlab_private_token = f.read().strip()

# Set GitLab API endpoint
gitlab_api_endpoint = "https://gitlab.com/api/v4"

# Set up basic logging to stderr
# TODO: more like glproj.py - levels etc
logging.basicConfig(stream=sys.stderr, level=logging.ERROR)

async def fetch_project_webhooks(session, project_id):
    url = f"{gitlab_api_endpoint}/projects/{project_id}/hooks"
    headers = {"Private-Token": gitlab_private_token}
    try:
        async with session.get(url, headers=headers) as response:
            response.raise_for_status()
            return await response.json()
    except Exception as e:
        logging.error(f"Failed to fetch webhooks for project {project_id}: {e}")
        return []  # Return empty list if all retries fail

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
    retry_options = ExponentialRetry(
        attempts=10,
        # some codes aren't retriable by default; GitLab API returns a lot of 429s in particular
        statuses={429, 500, 502, 503, 504}
    )
    async with RetryClient(raise_for_status=False, retry_options=retry_options) as session:
        tasks = [process_project(session, project) for project in data["projects"]]
        results = await asyncio.gather(*tasks)
        # results is a list of lists, where each sublist is the hooks for
        # one project. We use extend to flatten this list of lists into
        # a single list of hooks.
        hooks = []
        for sublist in results:
            hooks.extend(sublist)
        print(json.dumps({"hooks": hooks}, indent=2))

asyncio.run(main())
