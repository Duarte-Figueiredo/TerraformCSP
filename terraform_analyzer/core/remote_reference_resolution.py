from terraform_analyzer.core import RemoteReference, GitHubReference
from terraform_analyzer.external import github_manager

GITHUB_URL = "github.com"


def parse_github(url: str) -> GitHubReference:
    return github_manager.repo_project_extract(url)


def resolve(url: str) -> RemoteReference:
    if GITHUB_URL in url:
        return parse_github(url)

    raise RuntimeError(f"Unable to resolve reference for '{url}'")
