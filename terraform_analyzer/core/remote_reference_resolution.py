import re

from terraform_analyzer.core import RemoteReference, GitHubReference, RepoReference
from terraform_analyzer.external import github_manager

GIT_REF = "git::"
GITHUB_URL = "github.com"

GIT_GITHUB_REGEX = re.compile('github\.com\/([^\/]*)\/([^\/]*)\.git(?:\/\/([^\?]*))?\?(?:.*)ref=([^&\n]*)&?')
SHA_REGEX = re.compile('^[A-Fa-f0-9]{40}$')


def parse_git(git_url: str) -> RepoReference:
    if GITHUB_URL in git_url:
        (author, project, path, tag_or_sha_or_branch) = GIT_GITHUB_REGEX.findall(git_url)[0]

        if not SHA_REGEX.match(tag_or_sha_or_branch):
            tag_or_sha_or_branch = github_manager.get_branch_or_tag_commit_hash(f"{author}/{project}",
                                                                                tag_or_sha_or_branch)

        return GitHubReference(author=author,
                               project=project,
                               commit_hash=tag_or_sha_or_branch,
                               path=path)

    raise RuntimeError(f"Unsupported 'git::' reference {git_url}")


def parse_github(url: str) -> GitHubReference:
    return github_manager.repo_project_extract(url)


def resolve(url: str) -> RemoteReference:
    if url.startswith(GIT_REF):
        return parse_git(url)
    elif GITHUB_URL in url:
        return parse_github(url)

    raise RuntimeError(f"Unable to resolve reference for '{url}'")
