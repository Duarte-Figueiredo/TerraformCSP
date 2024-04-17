import logging
import os
from typing import Any

from terraform_analyzer.core import LocalResource
from terraform_analyzer.core.hcl import hcl_file_parser, hcl_resolver

logger = logging.getLogger("hcl_project_parser")


def _list_local_resource(path: str) -> [LocalResource]:
    tmp: [LocalResource] = []
    for name in os.listdir(path):
        is_dir = os.path.isdir(f"{path}/{name}")

        tmp.append(LocalResource(parent_dir=path,
                                 name=name,
                                 is_directory=is_dir))

    return tmp


def parse_project(main: LocalResource) -> list[dict[str, Any]]:
    # breath-first search
    main_folder = main.get_parent_folder()

    folders_to_parse: list[LocalResource] = [main_folder]

    hcl_resources: list[dict[str, any]] = []

    while folders_to_parse:
        next_file = folders_to_parse.pop()
        logger.debug(f"Parsing {next_file.get_full_path()}")
        next_to_parse: list[LocalResource] = _list_local_resource(next_file.get_full_path())

        files_to_parse = [lr for lr in next_to_parse if not lr.is_directory]
        folders_to_parse.extend([lr for lr in next_to_parse if lr.is_directory])

        local_res: LocalResource
        for local_res in files_to_parse:
            tmp: list[dict[str, Any]] = hcl_file_parser.list_hcl_resources(local_res)
            hcl_resources.extend(tmp)

    logger.info(f"Finish crawling successfully tf project at {main_folder.parent_dir}")

    return hcl_resolver.resolve(hcl_resources)
