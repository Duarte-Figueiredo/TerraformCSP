import logging
from typing import Set

import hcl2

from download_manager import download_file
from tcsp.utils import parse_resource_path_and_name

OUTPUT_FOLDER = "/home/duarte/Documents/Personal/Code/TerraformCSP/resources"
MODULE = "module"
MODULE_SOURCE = "source"
TF_SUFFIX = ".tf"
TF_MAIN_FILE_NAME = "main.tf"

logging.basicConfig(level=logging.INFO)


def sanitize_module_dependency(source: str) -> str:
    source = source.replace("./", "")

    if TF_SUFFIX not in source:
        source += f"/{TF_MAIN_FILE_NAME}"

    return source


def hcl_dependencies(tf: dict) -> Set[str]:
    dependencies: Set[str] = set()

    if MODULE in tf:
        modules: dict = tf[MODULE]
        for module in modules:
            resources: dict
            for resource in module.values():
                dependencies.add(sanitize_module_dependency(resource[MODULE_SOURCE]))

    return dependencies


def cenas(main_file_url: str, output_folder_path: str):
    resource_root_url_path, main_file_name = parse_resource_path_and_name(main_file_url)

    files_fetched: Set[str] = set()
    files_to_fetch: Set[str] = {main_file_name}

    while files_to_fetch:
        next_file = files_to_fetch.pop()

        logging.info(f"Processing {next_file}")

        if next_file in files_fetched:
            raise RuntimeError(f"Detected circular dependency with {next_file}")

        output_file_path = download_file(resource_root_url_path, next_file, output_folder_path)

        hcl_dict: dict
        with open(output_file_path, 'r') as file:
            hcl_dict = hcl2.load(file)

        detected_dependencies = hcl_dependencies(hcl_dict)
        logging.info(f"Detected the following dependencies for {next_file} '{detected_dependencies}'")

        cur_path, _ = parse_resource_path_and_name(next_file)

        s1 = list(map(lambda dep: f"{cur_path}{dep}", detected_dependencies))
        files_to_fetch.update(s1)
        # grab variables.tf if exist

        # for each "module" grab the file
        # for each import grab the file

        # test for circular dependency
        # Max nº of jumps?


# RESOURCE = "https://raw.githubusercontent.com/enterpriseih/kubespray-5/c40b43de019d43aba431f7dd9e3b9545702ec004/contrib/terraform/gcp/main.tf"
RESOURCE = "https://raw.githubusercontent.com/nargetdev/outserv/502e611e5e12c502f3e96ab1f09744a096900ab9/contrib/config/terraform/kubernetes/main.tf"

if __name__ == '__main__':
    cenas(RESOURCE, OUTPUT_FOLDER)
