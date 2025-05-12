#!/usr/bin/env python
import requests
import os
import logging
import asyncio
import aiohttp
from aiohttp_retry import RetryClient, ExponentialRetry
import json

# Setup logging to file and stdout
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger()
file_handler = logging.FileHandler('script.log')
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Setup a separate logger for project list without timestamp
project_logger = logging.getLogger('project_logger')
project_file_handler = logging.FileHandler('projects.log')
project_file_handler.setLevel(logging.INFO)
project_logger.addHandler(project_file_handler)

# Read the access token from a file
def read_token(file_path):
    with open(file_path, 'r') as file:
        return file.read().strip()

# Read the group path from a file
def read_group_path(file_path):
    with open(file_path, 'r') as file:
        return file.read().strip()

# Replace with your GitLab instance URL
GITLAB_URL = 'https://gitlab.com/api/graphql'
TOKEN_FILE = 'token.txt'
GROUP_PATH_FILE = 'group_path.txt'

# GraphQL query to get projects and subgroups with pagination
query = """
query($fullPath: ID!, $projectsCursor: String, $groupsCursor: String) {
  group(fullPath: $fullPath) {
    name
    webUrl
    projects(after: $projectsCursor) {
      pageInfo {
        endCursor
        hasNextPage
      }
      nodes {
        id
        name
        description
        webUrl
      }
    }
    descendantGroups(after: $groupsCursor) {
      pageInfo {
        endCursor
        hasNextPage
      }
      nodes {
        fullPath
      }
    }
  }
}
"""

async def fetch(session, url, headers, json):
    try:
        async with session.post(url, headers=headers, json=json, timeout=60) as response:
            response.raise_for_status()
            return await response.json()
    except aiohttp.ClientError as e:
        logger.error(f"HTTP error occurred: {e}")
        raise
    except asyncio.TimeoutError as e:
        logger.error(f"Connection timeout occurred: {e}")
        raise

async def get_projects(full_path, access_token, projects_cursor=None, groups_cursor=None):
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    variables = {'fullPath': full_path, 'projectsCursor': projects_cursor, 'groupsCursor': groups_cursor}
    retry_options = ExponentialRetry(attempts=10)
    async with RetryClient(raise_for_status=False, retry_options=retry_options) as session:
        result = await fetch(session, GITLAB_URL, headers, {'query': query, 'variables': variables})
        return result

async def retrieve_all_projects(full_path, projects_list, projects_set, access_token):
    projects_cursor = None
    groups_cursor = None
    while True:
        try:
            result = await get_projects(full_path, access_token, projects_cursor, groups_cursor)
        except Exception as e:
            logger.error(f"Failed to fetch projects: {e}")
            break

        group_data = result['data']['group']

        # Log information about the current group to stdout (URL instead of name)
        logger.info(f"Evaluating Group URL: {group_data['webUrl']}")

        # Add unique projects of the current group
        for project in group_data['projects']['nodes']:
            if project['webUrl'] not in projects_set:
                projects_set.add(project['webUrl'])
                projects_list.append(project)

        # Check if there are more projects to fetch
        if group_data['projects']['pageInfo']['hasNextPage']:
            projects_cursor = group_data['projects']['pageInfo']['endCursor']
        else:
            projects_cursor = None

        # Add projects from descendant groups
        tasks = []
        for subgroup in group_data['descendantGroups']['nodes']:
            tasks.append(retrieve_all_projects(subgroup['fullPath'], projects_list, projects_set, access_token))

        await asyncio.gather(*tasks)

        # Check if there are more subgroups to fetch
        if group_data['descendantGroups']['pageInfo']['hasNextPage']:
            groups_cursor = group_data['descendantGroups']['pageInfo']['endCursor']
        else:
            groups_cursor = None

        if not projects_cursor and not groups_cursor:
            break

async def main():
    full_path = read_group_path(GROUP_PATH_FILE)
    access_token = read_token(TOKEN_FILE)
    projects_list = []
    projects_set = set()

    try:
        await retrieve_all_projects(full_path, projects_list, projects_set, access_token)

        # Log all projects to both stdout and file in JSON format without duplicates and timestamps
        logged_projects_set = set()

        for project in projects_list:
            project_info = {
                "Project ID": project['id'],
                "Project Name": project['name'],
                "Project Description": project.get('description', ''),
                "Project URL": project['webUrl']
            }

            if project_info["Project URL"] not in logged_projects_set:
                logged_projects_set.add(project_info["Project URL"])
                logger.info(json.dumps(project_info))
                project_logger.info(json.dumps(project_info))

    except Exception as e:
        logger.error(f"An error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(main())
