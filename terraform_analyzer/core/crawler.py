import logging
from typing import Set, List

from terraform_analyzer.core import Resource, RemoteResource, GitHubReference, RemoteReference, \
    remote_reference_resolution
from terraform_analyzer.core.hcl import hcl_file_parser
from terraform_analyzer.external import download_manager, github_manager, terraform_registry

logger = logging.getLogger("crawler")


def grab_relevant_tf_files_from_root_folder(root_remote_resource: RemoteResource) -> set[RemoteResource]:
    if isinstance(root_remote_resource.remote_reference, GitHubReference):
        rr_list: list[RemoteResource] = github_manager.list_files_in_remote_folder(root_remote_resource,
                                                                                   root_remote_resource.remote_reference)

        return set(filter(lambda rr: not rr.is_directory and rr.name.endswith('.tf'), rr_list))
    else:
        raise RuntimeError(f"I don't know how to download ${type(root_remote_resource.remote_reference)}")
    pass


def extract_dependency_reference(dependency: str, rr: RemoteReference, next_file: RemoteResource) -> RemoteResource:
    source_url: str
    if dependency.startswith("."):
        # is local resource
        if isinstance(rr, GitHubReference):
            return github_manager.dependency_builder(dependency, next_file, rr)
        else:
            raise RuntimeError(f"I don't know how to download {type(rr)}")
    elif dependency.startswith("git::") or dependency.startswith("http"):
        source_url = dependency
    else:
        source_url = terraform_registry.get_source_code(dependency)

    reference: RemoteReference = remote_reference_resolution.resolve(source_url)

    if isinstance(reference, GitHubReference):
        return RemoteResource(remote_reference=reference,
                              is_directory=True,
                              relative_path=(),
                              name="")

    raise RuntimeError(f"I don't know how to handle {type(rr)}")


def crawl_download(root_remote_resource: RemoteResource, output_folder_path: str):
    logger.info("Starting crawling")

    relevant_root_tf_files = grab_relevant_tf_files_from_root_folder(root_remote_resource)

    files_parsed: Set[RemoteResource] = set()
    files_to_parse: Set[RemoteResource] = relevant_root_tf_files

    while files_to_parse:
        next_file: RemoteResource = files_to_parse.pop()

        if next_file in files_parsed:
            logger.warning(f"'{next_file.name}' has already been processed")
            continue

        files_parsed.add(next_file)

        resources: List[Resource] = download_manager.download_file_or_folder(next_file,
                                                                             output_folder_path)

        resource: Resource
        for resource in resources:
            dependencies: set[str] = hcl_file_parser.list_hcl_dependencies(resource)

            if dependencies:
                logger.info(f"Detected the following dependencies for {resource.local_resource.name} '{dependencies}'")
            else:
                logger.info(f"No dependencies detected for {resource.local_resource.name}")
                continue

            rrr: RemoteReference = resource.remote_resource.remote_reference

            for dependency in dependencies:
                rr: RemoteResource = extract_dependency_reference(dependency, rrr, next_file)

                files_to_parse.add(rr)

    logger.info(f"Finish crawling successfully, tf files stored at {output_folder_path}")
