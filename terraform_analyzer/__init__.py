import logging
import os

from terraform_analyzer.core import RemoteResource, GitHubReference, LocalResource, crawler
from terraform_analyzer.core.hcl import hcl_project_parser
from terraform_analyzer.core.hcl.hcl_obj import TerraformResource
from terraform_analyzer.core.hcl.hcl_obj.hcl_resources import TerraformComputeResource

RESOURCE_OUTPUT_FOLDER = "/home/duarte/Documents/Personal/Code/TerraformCSP/resources"
HCL_RAW_OUTPUT = "/home/duarte/Documents/Personal/Code/TerraformCSP/hcl_output_raw.json"

logger = logging.getLogger("terraform_analyzer/__init__")


def download_terraform(author: str,
                       project: str,
                       commit_hash: str,
                       path: str,
                       tf_main_file_name: str,
                       output_folder: str):
    root_tf_folder_name = os.path.basename(path)
    root_tf_folder_parent_path = os.path.dirname(path)
    rrr = RemoteResource(remote_reference=GitHubReference(author=author,
                                                          project=project,
                                                          commit_hash=commit_hash,
                                                          path=root_tf_folder_parent_path),
                         is_directory=True,
                         relative_path=(),
                         name=root_tf_folder_name)

    crawler.crawl_download(rrr, output_folder)


def run_terraform_analyzer(github_author: str,
                           github_project: str,
                           github_commit_hash: str,
                           tf_root_parent_folder_path: str,
                           tf_main_file_name: str = "main.tf",
                           force_download: bool = False) -> [TerraformResource]:

    # if force_download or not os.listdir(RESOURCE_OUTPUT_FOLDER):
    download_terraform(author=github_author,
                       project=github_project,
                       commit_hash=github_commit_hash,
                       path=tf_root_parent_folder_path,
                       tf_main_file_name=tf_main_file_name,
                       output_folder=RESOURCE_OUTPUT_FOLDER)

    main_resource = LocalResource(full_path=RESOURCE_OUTPUT_FOLDER,
                                  name=tf_main_file_name,
                                  is_directory=False)

    component_list: list[TerraformResource] = hcl_project_parser.parse_project(main_resource)

    return component_list


if __name__ == '__main__':
    # run_terraform_analyzer(github_author="nargetdev",
    #                        github_project="outserv",
    #                        github_commit_hash="502e611e5e12c502f3e96ab1f09744a096900ab9",
    #                        tf_root_parent_folder_path="contrib/config/terraform/kubernetes")
    run_terraform_analyzer(github_author="terraform-aws-modules",
                           github_project="terraform-aws-eks",
                           github_commit_hash="afadb14e44d1cdbd852dbae815be377c4034e82a",
                           tf_root_parent_folder_path="")
    # run_terraform_analyzer(github_author="kumarkartikmk57",
    #                        github_project="terraform_modules",
    #                        github_commit_hash="917a22d76d6ff6ee865d1291eba71538165cde74",
    #                        tf_root_parent_folder_path="")

# kumarkartikmk57/terraform_modules this blows when pa