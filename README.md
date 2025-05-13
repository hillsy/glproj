# glproj - simple but performant GitLab PROJect lister

This script is a Python utility that uses the GitLab GraphQL API to list all
projects within a specified group and its subgroups. It handles pagination and
outputs the project details (ID, name, description, and URL) in JSON format.

## Requirements

- Python 3.12+ (developed on 3.12 - other versions may work)
- The necessary Python packages listed in `requirements.txt`

## Installation and Running

1. Clone/download the repository, which will give you both the script
   `glproj.py` and the pip requirements file `requirements.txt`

2. `cd` to your download/clone directory e.g.

   `cd ~/glproj`

3. Create a Python 3 Virtual Environment:

   `python3.12 -m venv .`

4. Activate the Virtual Environment:

   `source bin/activate`

5. Install Dependencies:

   With the virtual environment activated, install the required packages using
   pip:

   `pip install -r requirements.txt`

6. Create Configuration Files

   The script requires two files in the same directory to read your GitLab
   access token and the group path:

   - `token.txt`: Create this file and paste your GitLab Personal Access Token
     inside. Ensure the token has the api scope.

     **Keep this file secure and do not commit it to version control.**

   - `group_path.txt`: Create this file and paste the full path of the GitLab
     group you want to list projects from (e.g. my-group/my-subgroup)

7. Run the Script

   Execute the script from your terminal with the virtual environment
   activated:

   `python glproj.py`

   The script will print the JSON output to standard output. You can redirect
   this output to a file:

   `python glproj.py > projects.json`

## Command-Line Arguments

- `--loglevel {DEBUG, INFO, WARNING, ERROR, CRITICAL}`: Sets the logging level.
  Defaults to `ERROR`.

- `--logfile [FILENAME]`: Logs messages to a file. If FILENAME is not provided,
  it defaults to `glproj.log`. If this argument is omitted, logs are sent to
  stderr.

  Example:

  `python glproj.py --loglevel INFO --logfile my_log.txt > projects.json`

## Output

The script outputs a JSON object to standard output with a single key projects
which is a list of project objects. Each project object contains:

- id: The integer ID of the project.
- name: The name of the project.
- description: The description of the project.
- url: The web URL of the project.

## Technical Details and Resilience

The script is built using Python's asynchronous programming capabilities to
efficiently handle communication with the GitLab API:

- **asyncio**: The script leverages asyncio to perform concurrent operations.
  This means it can initiate multiple API requests to fetch data from different
  subgroups or paginated results simultaneously, significantly speeding up the
  data retrieval process compared to sequential requests.

- **aiohttp**: Asynchronous HTTP requests are handled by the aiohttp library.
  This library is specifically designed for use with asyncio, providing a
  non-blocking way to make network calls without waiting for each response
  before moving to the next task.

- **aiohttp-retry with ExponentialRetry**: To enhance resilience against
  transient network issues and GitLab API rate limiting, the script uses
  aiohttp-retry with an ExponentialRetry strategy. This automatically retries
  failed HTTP requests with increasing delays between attempts.

  This approach helps to:

  - Recover from temporary network glitches.
  - Respect API rate limits by backing off gracefully when the server indicates
    it is being overwhelmed. The retry mechanism attempts up to 10 times with
    exponential backoff, improving the chances of successful completion even
    under challenging network conditions or heavy API load.
