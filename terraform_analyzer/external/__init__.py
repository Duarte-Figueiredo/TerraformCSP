import logging
import os

import requests
from github import Auth
from github import Github

GITHUB_ACCESS_TOKEN: str = os.environ.get('ACCESS_TOKEN')
logger = logging.getLogger("external/__init__")

github_session = requests.Session()

if GITHUB_ACCESS_TOKEN:
    auth = Auth.Token(GITHUB_ACCESS_TOKEN)
    github_client = Github(auth=auth)
else:
    github_client = Github()
    logger.info("No github auth provided, making requests in anonymous way (may get rate limited)")
