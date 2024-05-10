import logging
import os
from typing import Any

from terraform_analyzer.core import LocalResource, utils
from terraform_analyzer.core.hcl import hcl_file_parser, hcl_resolver, TerraformSyntax, ModuleTf
from terraform_analyzer.core.hcl.hcl_obj import TerraformResource

logger = logging.getLogger("hcl_project_parser")


def _list_local_resource(path: str) -> [LocalResource]:
    tmp: [LocalResource] = []

    if os.path.exists(path) and not os.path.isdir(path):
        return []

    for name in os.listdir(path):
        full_path = f"{path}/{name}"
        is_dir = os.path.isdir(full_path)

        tmp.append(LocalResource(full_path=full_path,
                                 name=name,
                                 is_directory=is_dir))

    return tmp


def parse_project(main: LocalResource) -> list[TerraformResource]:
    main_folder = main.get_parent_folder()

    resources_path_parsed: set[str] = set()
    folders_to_parse: list[LocalResource] = [main_folder]

    hcl_resources: list[TerraformSyntax] = []

    while folders_to_parse:
        next_folder = folders_to_parse.pop()

        logger.debug(f"Parsing {next_folder.get_full_path()}")
        folder_content: list[LocalResource] = _list_local_resource(next_folder.get_full_path())

        resources_path_parsed.add(next_folder.get_full_path())
        files_to_parse = [lr for lr in folder_content if not lr.is_directory]

        local_res: LocalResource
        for local_res in files_to_parse:
            detected_res: list[TerraformSyntax] = hcl_file_parser.list_hcl_resources(local_res)

            res: dict[str, Any]

            module: ModuleTf
            for module in filter(lambda x: type(x) is ModuleTf, detected_res):
                source = module.source

                resolved_path = utils.resolve_path_local_reference(next_folder.get_full_path(),
                                                                   source)
                if resolved_path not in resources_path_parsed:
                    folders_to_parse.append(LocalResource(full_path=resolved_path,
                                                          name=os.path.basename(resolved_path),
                                                          is_directory=os.path.isdir(resolved_path)))
                else:
                    logger.warning(f"Skipping already parsed resource {resolved_path}")

            hcl_resources.extend(detected_res)

    logger.info(f"Finish crawling successfully tf project at {main_folder.full_path}")

    return hcl_resolver.resolve(hcl_resources)
