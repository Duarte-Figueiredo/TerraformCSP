import logging
from typing import Set, List

from terraform_analyzer.core import Resource, RemoteResource, GitHubReference, RemoteReference
from terraform_analyzer.core.hcl import hcl_file_parser
from terraform_analyzer.external import download_manager, github_manager

logger = logging.getLogger("crawler")


def crawl_download(root_remote_resource: RemoteResource, output_folder_path: str):
    logger.info("Starting crawling")
    files_parsed: Set[RemoteResource] = set()
    files_to_parse: Set[RemoteResource] = {root_remote_resource}

    while files_to_parse:
        next_file: RemoteResource = files_to_parse.pop()

        if next_file in files_parsed:
            raise RuntimeError(f"Detected circular dependency with '{next_file}'")

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
                rr: RemoteResource
                # todo dependency can be outside of rrr
                if isinstance(rrr, GitHubReference):
                    rr = github_manager.dependency_builder(dependency, next_file, rrr)
                else:
                    raise RuntimeError(f"I don't know how to download {type(rrr)}")
                files_to_parse.add(rr)

    logger.info(f"Finish crawling successfully, tf files stored at {output_folder_path}")
