import logging
import os

import requests

logger = logging.getLogger("external/__init__")

github_session = requests.Session()

github_token = os.environ.get("GITHUB_TOKEN")

if github_token:
    github_session.headers.update({
        'Authorization': f'Bearer {os.environ.get("GITHUB_TOKEN")}',
    })
else:
    logger.info("No github auth provided, making requests in anonymous way (may get rate limited)")
