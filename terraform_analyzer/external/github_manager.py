import logging
import re
from enum import Enum
from typing import List, Optional, Union

from github import Repository, Branch
from github.ContentFile import ContentFile
from pydantic import BaseModel

from terraform_analyzer.core import RemoteResource, GitHubReference
from terraform_analyzer.external import github_client

DOT_COM_REGEX = r".*?\.com\/"

logger = logging.getLogger("github_manager")


class GithubContextResource(BaseModel):
    author: str
    project: str
    commit_hash: str
    path: str


class GithubFileType(str, Enum):
    DIR = 'dir'
    FILE = 'file'


class GithubResourceResponse(BaseModel):
    name: str
    download_url: Optional[str]
    html_url: str
    url: str
    type: GithubFileType


def _map_github_folder_response_to_remote_resource(github_folder_response: GithubResourceResponse,
                                                   parent_resource: RemoteResource) -> RemoteResource:
    relative_path: tuple[str, ...] = parent_resource.relative_path + (parent_resource.name,)

    return RemoteResource(remote_reference=parent_resource.remote_reference,
                          is_directory=github_folder_response.type == GithubFileType.DIR,
                          relative_path=relative_path,
                          name=github_folder_response.name)


def _map_github_content_file_to_remote_resource(github_content: ContentFile,
                                                parent_resource: RemoteResource) -> RemoteResource:
    relative_path: tuple[str, ...] = parent_resource.relative_path + (parent_resource.name,)

    return RemoteResource(remote_reference=parent_resource.remote_reference,
                          is_directory=github_content.type == GithubFileType.DIR.value,
                          relative_path=relative_path,
                          name=github_content.name)


def repo_project_extract(github_project_url: str) -> GitHubReference:
    url_path = re.sub(DOT_COM_REGEX, "", github_project_url)
    (author, project) = url_path.split("/")

    repo: Repository = github_client.get_repo(f"{author}/{project}")

    main_branch: Branch = repo.get_branch(repo.default_branch)

    commit_hash = main_branch.commit.sha

    return GitHubReference(author=author,
                           project=project,
                           commit_hash=commit_hash,
                           path="")


# unused for now, might come handy when passing a main.tf url into analizer
def _repo_extract(resource_full_url_path: str) -> GithubContextResource:
    url_path = re.sub(DOT_COM_REGEX, "", resource_full_url_path)
    author: str
    project: str
    commit_hash: str
    path: str
    (author, project, commit_hash, *path) = url_path.split("/")

    return GithubContextResource(author=author,
                                 project=project,
                                 commit_hash=commit_hash,
                                 path='/'.join(path))


def list_files_in_remote_folder(remote_resource: RemoteResource, git_proj: GitHubReference) -> List[RemoteResource]:
    path_with_name: str = remote_resource.get_remote_abs_path_with_name()
    logger.info(f"Fetching '{remote_resource}'")

    repo: Repository = github_client.get_repo(f"{git_proj.author}/{git_proj.project}")
    contents: Union[list[ContentFile], ContentFile] = repo.get_contents(path_with_name, git_proj.commit_hash)

    if type(contents) is not list:
        contents = [contents]

    remote_resources: list[RemoteResource] = list(
        map(lambda gr: _map_github_content_file_to_remote_resource(gr, remote_resource), contents))

    return remote_resources


def is_resource_link_type_a_dir(resource_path: str, ghr: GitHubReference) -> bool:
    repo: Repository = github_client.get_repo(f"{ghr.author}/{ghr.project}")
    contents: Union[list[ContentFile], ContentFile] = repo.get_contents(resource_path, ghr.commit_hash)

    return isinstance(contents, list)


def dependency_builder(dependency: str, parent_rr: RemoteResource, ghr: GitHubReference) -> RemoteResource:
    path = parent_rr.get_remote_abs_path_with_name() if parent_rr.is_directory else parent_rr.get_remote_abs_path()
    relative_path: tuple[str, ...] = parent_rr.relative_path + (
        parent_rr.name,) if parent_rr.is_directory else parent_rr.relative_path
    resource_path = f"{path}/{dependency}"

    is_dir = is_resource_link_type_a_dir(resource_path, ghr)

    return RemoteResource(remote_reference=ghr,
                          is_directory=is_dir,
                          relative_path=relative_path,
                          name=dependency)

# https://github.com/nargetdev/outserv/blob/main/contrib/config/terraform/kubernetes/modules/aws/main.tf
# https://api.github.com/repos/nargetdev/outserv/contents/contrib/config/terraform/kubernetes/modules/aws
# relative_path= /contrib/config/terraform/kubernetes/modules/aws/main.tf
