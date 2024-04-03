import logging
from typing import Set, List

from tcsp.core import Resource, RemoteResource, GitHubReference, RemoteReference
from tcsp.core.hcl import hcl_parser
from tcsp.external import download_manager, github_manager

logger = logging.getLogger("crawler")


def crawl(root_remote_resource: RemoteResource, output_folder_path: str) -> list[dict[str, any]]:
    logger.info("Starting crawling")
    files_parsed: Set[RemoteResource] = set()
    files_to_parse: Set[RemoteResource] = {root_remote_resource}

    hcl_resources: list[dict[str, any]] = []

    while files_to_parse:
        next_file: RemoteResource = files_to_parse.pop()

        if next_file in files_parsed:
            raise RuntimeError(f"Detected circular dependency with '{next_file}'")

        resources: List[Resource] = download_manager.download_file_or_folder(next_file,
                                                                             output_folder_path)

        resource: Resource
        for resource in resources:
            dependencies: set[str] = hcl_parser.list_hcl_dependencies(resource, hcl_resources)

            if dependencies:
                logger.info(f"Detected the following dependencies for {resource.name} '{dependencies}'")
            else:
                logger.info(f"No dependencies detected for {resource.name}")
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

    logger.info("Finish crawling successfully")
    return hcl_resources
