#!/usr/bin/env python

import json
import sys
import asyncio
import aiohttp

# Load JSON input from stdin
json_input = sys.stdin.read()
data = json.loads(json_input)

# Load GitLab auth token from token.txt
with open('token.txt', 'r') as f:
    gitlab_private_token = f.read().strip()

# Set GitLab API endpoint
gitlab_api_endpoint = "https://gitlab.com/api/v4"

async def fetch_project_webhooks(session, project_id):
    url = f"{gitlab_api_endpoint}/projects/{project_id}/hooks"
    headers = {"Private-Token": gitlab_private_token}
    async with session.get(url, headers=headers) as response:
        if response.status == 200:
            return await response.json()
        else:
            print(f"Failed to retrieve webhooks for project {project_id}: {response.status} {response.reason}")
            print(f"Response headers: {response.headers}")
            print(f"Response text: {await response.text()}")
            return []

async def process_project(session, project):
    project_id = project["id"]
    project_url = project["web_url"]
    webhooks = await fetch_project_webhooks(session, project_id)
    hooks = []
    for webhook in webhooks:
        hook = webhook.copy()
        hook["project_url"] = project_url
        hooks.append(hook)
    return hooks

async def main():
    async with aiohttp.ClientSession() as session:
        tasks = [process_project(session, project) for project in data["projects"]]
        results = await asyncio.gather(*tasks)
        # flatten the list of lists into a single list
        # this is necessary because asyncio.gather returns a list of lists
        # and we want a single list of all the webhooks
        hooks = [hook for sublist in results for hook in sublist]
        print(json.dumps({"hooks": hooks}))

asyncio.run(main())
