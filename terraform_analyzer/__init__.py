import json
import logging
import os
from typing import Any

from terraform_analyzer.core import RemoteResource, GitHubReference, LocalResource, crawler
from terraform_analyzer.core.hcl import hcl_project_parser

RESOURCE_OUTPUT_FOLDER = "/home/duarte/Documents/Personal/Code/TerraformCSP/resources"
HCL_RAW_OUTPUT = "/home/duarte/Documents/Personal/Code/TerraformCSP/hcl_output_raw.json"
RESOURCE = "https://raw.githubusercontent.com/nargetdev/outserv/502e611e5e12c502f3e96ab1f09744a096900ab9/contrib/config/terraform/kubernetes/main.tf"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("terraform_analyzer/__init__")


def download_terraform(author: str,
                       project: str,
                       commit_hash: str,
                       path: str,
                       tf_main_file_name: str,
                       output_folder: str):
    rrr = RemoteResource(remote_reference=GitHubReference(author=author,
                                                          project=project,
                                                          commit_hash=commit_hash,
                                                          path=path),
                         is_directory=False,
                         relative_path=(),
                         name=tf_main_file_name)

    crawler.crawl_download(rrr, output_folder)


def run_terraform_analyzer(github_author: str,
                           github_project: str,
                           github_commit_hash: str,
                           tf_root_parent_folder_path: str,
                           tf_main_file_name: str = "main.tf",
                           force_download: bool = False):
    if force_download or not os.listdir(RESOURCE_OUTPUT_FOLDER):
        download_terraform(author=github_author,
                           project=github_project,
                           commit_hash=github_commit_hash,
                           path=tf_root_parent_folder_path,
                           tf_main_file_name=tf_main_file_name)

    main_resource = LocalResource(parent_dir=RESOURCE_OUTPUT_FOLDER,
                                  name=tf_main_file_name,
                                  is_directory=False)

    component_list: list[dict[str, Any]] = hcl_project_parser.parse_project(main_resource)

    component_list_json: str = json.dumps(component_list)
    print(component_list_json)

    if os.path.exists(HCL_RAW_OUTPUT):
        os.remove(HCL_RAW_OUTPUT)

    with open(HCL_RAW_OUTPUT, 'w') as file:
        file.write(component_list_json)


if __name__ == '__main__':
    run_terraform_analyzer(github_author="nargetdev",
                           github_project="outserv",
                           github_commit_hash="502e611e5e12c502f3e96ab1f09744a096900ab9",
                           tf_root_parent_folder_path="contrib/config/terraform/kubernetes")
