#!/usr/bin/env python
import json
import sys
import asyncio
import aiohttp
from aiohttp_retry import RetryClient, ExponentialRetry

# Read the access token from a file
def read_token(file_path):
    with open(file_path, 'r') as file:
        return file.read().strip()

# Read the group path from a file
def read_group_path(file_path):
    with open(file_path, 'r') as file:
        return file.read().strip()

# Default values for config variables
# TODO: override these defaults with command-line arguments, if provided
# GITLAB_URL = 'https://gitlab.com/api/graphql'
TOKEN_FILE = 'token.txt'
GROUP_PATH_FILE = 'group_path.txt'

# Load JSON input from stdin
json_input = sys.stdin.read()
data = json.loads(json_input)

# Set your GitLab private token and API endpoint
gitlab_private_token = read_token(TOKEN_FILE)
gitlab_api_endpoint = "https://gitlab.com/api/v4"

# Set up retry policy
retry_options = ExponentialRetry(attempts=10)
    # attempts=10,
    # factor=2,  # exponential backoff factor
    # min_timeout=1,  # minimum timeout between retries
    # max_timeout=32,  # maximum timeout between retries
    # statuses=(429,)  # retry on 429 Too Many Requests status code
#)

async def fetch_project_webhooks(session, project_id):
    url = f"{gitlab_api_endpoint}/projects/{project_id}/hooks"
    headers = {"Private-Token": gitlab_private_token}
    async with session.get(url, headers=headers) as response:
        if response.status == 200:
            return await response.json()
        else:
            print(f"Failed to retrieve webhooks for project {project_id}: {response.status}")
            return []

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
    async with RetryClient(raise_for_status=False, retry_options=retry_options) as session:
        tasks = [process_project(session, project) for project in data["projects"]]
        results = await asyncio.gather(*tasks)
        hooks = [hook for sublist in results for hook in sublist]
        print(json.dumps({"hooks": hooks}))

asyncio.run(main())
