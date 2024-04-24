import itertools
import logging
import os
from typing import List

from github import Repository, ContentFile

from terraform_analyzer.core import Resource, RemoteResource, GitHubReference, LocalResource
from terraform_analyzer.external import github_manager, github_client

GITHUB_RESOURCE = "github"

logger = logging.getLogger("download_manager")


def create_required_folders(file_path: str):
    logging.info(f"creating folder path {file_path}")
    if not os.path.exists(file_path):
        os.makedirs(os.path.dirname(file_path), exist_ok=True)


def download_file_or_folder(remote_resource: RemoteResource, output_path: str) -> List[Resource]:
    if remote_resource.is_directory:
        return download_folder(remote_resource, output_path)
    else:
        return [download_file(remote_resource, output_path)]


def download_folder(remote_resource: RemoteResource, output_path: str) -> List[Resource]:
    logging.info(f"Visiting folder '{remote_resource.get_remote_abs_path_with_name()}'")

    if isinstance(remote_resource.remote_reference, GitHubReference):
        github_r: GitHubReference = remote_resource.remote_reference
        r_resources: List[RemoteResource] = github_manager.list_files_in_remote_folder(remote_resource,
                                                                                       github_r)

        resources: list[list[Resource]] = list(
            map(lambda rr: download_file_or_folder(rr, output_path), r_resources))

        return list(itertools.chain.from_iterable(resources))
    else:
        raise RuntimeError(f"I don't know how to download ${type(remote_resource.remote_reference)}")


def download_file(rr: RemoteResource, output_path: str) -> Resource:
    if isinstance(rr.remote_reference, GitHubReference):
        github_r: GitHubReference = rr.remote_reference
        return download_github_file(rr, github_r, output_path)
    else:
        raise RuntimeError(f"I don't know how to download ${type(rr.remote_reference)}")


# https://raw.githubusercontent.com/nargetdev/outserv/main/contrib/config/terraform/kubernetes/modules/aws/main.tf
def download_github_file(rr: RemoteResource, github_r: GitHubReference, output_path: str) -> Resource:
    repo_file_ref = f"{github_r.author}/" \
                    f"{github_r.project}/" \
                    f"{github_r.commit_hash}/" \
                    f"{rr.get_remote_abs_path_with_name()}"

    local_file_path = f"{output_path}/{github_r.author}/{github_r.project}/{rr.get_remote_abs_path_with_name()}"

    logging.info(f"Downloading file '{repo_file_ref}' into '{local_file_path}'")

    if os.path.exists(local_file_path):
        logger.info(f"Skipping download of {rr.get_remote_abs_path_with_name()} since it already exists")

    repo: Repository = github_client.get_repo(f"{github_r.author}/{github_r.project}")
    content_file: ContentFile = repo.get_contents(rr.get_remote_abs_path_with_name(), github_r.commit_hash)

    os.makedirs(os.path.dirname(local_file_path), exist_ok=True)

    open(local_file_path, 'wb').write(content_file.decoded_content)

    return Resource(remote_resource=rr,
                    local_resource=LocalResource(parent_dir=local_file_path,
                                                 name=rr.name,
                                                 is_directory=rr.is_directory))
