import re
from typing import Pattern

__name_regex_pattern: Pattern[str] = re.compile("(.*/)(.*)")


def parse_resource_path_and_name(file_url: str) -> (str, str):
    if "/" not in file_url:
        return "", file_url

    match = __name_regex_pattern.match(file_url)

    return match.group(1), match.group(2)
