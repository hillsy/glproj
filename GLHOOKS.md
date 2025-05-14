# glhooks.py

## Overview

`glhooks.py` is a Python script that retrieves the list of webhooks for
multiple GitLab projects using the GitLab API. It is designed to be used in
automated workflows or scripts where you need to audit, monitor, or process
webhooks across many projects.

The script:

- Reads a list of projects from standard input in JSON format.
- Authenticates to GitLab using a personal access token stored in `token.txt`.
- Fetches webhooks for each project, with robust retry logic for transient HTTP
  errors (including rate limiting).
- Outputs a JSON object containing all discovered webhooks to standard output.

## Features

- **Asynchronous**: Uses `asyncio` and `aiohttp` for fast, concurrent API
  requests.
- **Retry Logic**: Retries failed requests (including HTTP 429, 500, 502, 503, 504) up to 10 times with exponential backoff.
- **Error Handling**: Logs errors to standard error but continues processing
  other projects.
- **Simple Output**: Returns a flat JSON array of all webhooks found.

## Requirements

- Python 3.7+
- `aiohttp`
- `aiohttp_retry`

Install dependencies with:

```sh
pip install aiohttp aiohttp_retry
```

## Usage

1. **Prepare your GitLab token**

   Place your GitLab personal access token in a file named `token.txt` in the
   same directory as `glhooks.py`.
   The file should contain only the token string.

2. **Prepare your input JSON**

   The script expects a JSON object on standard input with a `projects` key,
   which is a list of project objects.
   Each project object must have at least an `id` and a `url` field. Example:

   ```json
   {
     "projects": [
       { "id": 123456, "url": "https://gitlab.com/yourgroup/yourproject" },
       { "id": 654321, "url": "https://gitlab.com/anothergroup/anotherproject" }
     ]
   }
   ```

3. **Run the script**

   You can run the script and provide the input JSON via a file or a pipe:

   ```sh
   cat projects.json | python glhooks.py
   ```

   or

   ```sh
   python glhooks.py < projects.json
   ```

4. **Output**

   The script prints a JSON object to standard output with a single key, `hooks`, containing a list of all webhooks found.
   Each webhook object includes the original webhook data plus a `project_url` field.

   Example output:

   ```json
   {
     "hooks": [
       {
         "id": 111,
         "url": "https://example.com/webhook",
         "project_url": "https://gitlab.com/yourgroup/yourproject",
         "...": "..."
       },
       {
         "id": 222,
         "url": "https://another.com/webhook",
         "project_url": "https://gitlab.com/anothergroup/anotherproject",
         "...": "..."
       }
     ]
   }
   ```

5. **Working with the data**

You can pipe data from the script into `jq` for further processsing. For
example, to output URL, hook ID and project ID to a CSV file:

```shell
cat projects.json | ./glhooks.py | jq -r '.hooks[] | [.url, .id, .project_url] | @csv'
```

## Notes

- If a project's webhooks cannot be fetched after all retries, an error is logged to standard error, and the script continues with the next project.
- The script is intended for use with the GitLab.com API but can be adapted for self-hosted GitLab instances by changing the `gitlab_api_endpoint` variable.
