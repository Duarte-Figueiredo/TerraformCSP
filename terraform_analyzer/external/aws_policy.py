import functools
import json
import logging
import re
from typing import Optional

from github import GithubException, UnknownObjectException
from github.ContentFile import ContentFile

from terraform_analyzer.external import github_client

URL = "https://raw.githubusercontent.com/zoph-io/MAMIP/master/policies/"

_ZOPH_IO_REPO = None

POLICY_NAME_REGEX = re.compile(".*\/(.*)")

logger = logging.getLogger("aws_policy")


# arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess
@functools.cache
def get_aws_managed_policy(policy_arn: str) -> Optional[dict]:
    global _ZOPH_IO_REPO
    if _ZOPH_IO_REPO is None:
        _ZOPH_IO_REPO = github_client.get_repo("zoph-io/MAMIP")

    policy_name_match = POLICY_NAME_REGEX.fullmatch(policy_arn)

    if policy_name_match is None:
        return None

    policy_name = policy_name_match.group(1)

    try:
        content_file: ContentFile = _ZOPH_IO_REPO.get_contents(f"policies/{policy_name}")

        policy_dict: dict = json.loads(content_file.decoded_content)
        return policy_dict["PolicyVersion"]["Document"]
    except UnknownObjectException:
        pass
    except GithubException:
        logging.error(f"Failed to fetch policy {policy_arn}")
    return None


if __name__ == '__main__':
    print(get_aws_managed_policy("arn:aws:iam::aws:policy/AmazonDynamDBFullAccess"))
    print(get_aws_managed_policy("arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess"))
    print(get_aws_managed_policy("arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"))
