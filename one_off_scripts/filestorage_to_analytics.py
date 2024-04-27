import logging
import os
import subprocess
# from one_off_scripts import OUTPUT_FOLDER
from typing import Optional

from terraform_analyzer import LocalResource, TerraformResource
from terraform_analyzer.core.hcl import hcl_project_parser

OUTPUT_FOLDER = "/home/duarte/Documents/Personal/Code/TerraformCSP/output"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("repo_tf_fetcher")


def get_label_names() -> {str}:
    pass


def get_iam_types() -> [str]:
    pass


def get_service_list() -> [str]:
    pass


def get_file_count(full_path: str) -> int:
    cmd = f"find {full_path} | wc -l"
    result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, text=True)

    file_count = int(result.stdout.removesuffix('\n'))

    return file_count


def get_repo_id(path: str) -> str:
    repo_name = os.listdir(path)[0]
    author_name = os.path.basename(path)

    return f"{author_name}/{repo_name}"


# noinspection PyUnboundLocalVariable
def get_root_main_path(project_path: str) -> Optional[str]:
    cmd = f"find {project_path} | grep -i main.tf"
    result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, text=True)

    mains: [str] = result.stdout.split('\n')

    root_main: Optional[str] = None
    min_level = 100
    for main_tf in mains:
        if not main_tf:
            continue
        level = main_tf.count('/')

        if min_level > level:
            min_level = level
            root_main = main_tf

    return root_main


def main():
    count = 0
    for author_name in os.listdir(OUTPUT_FOLDER):
        author_path = f"{OUTPUT_FOLDER}/{author_name}"
        repo_id: str = get_repo_id(author_path)

        project_path = f"{OUTPUT_FOLDER}/{repo_id}"
        file_count: int = get_file_count(project_path)

        root_main_path = get_root_main_path(project_path)

        if not root_main_path:
            # https://github.com/mbrydak/glowing-couscous/tree/main/task2/terraform/net
            # https://github.com/CMS-Enterprise/batcave-tf-eso
            # https://github.com/aspaceincloud/IAC/blob/master/env/dev/main.tf

            logger.warning(f"Failed to find {repo_id} 'main.tf' file")
            continue

        parent_dir = os.path.dirname(root_main_path)
        name = os.path.basename(root_main_path)

        main_resource = LocalResource(parent_dir=parent_dir,
                                      name=name,
                                      is_directory=False)

        component_list: list[TerraformResource] = hcl_project_parser.parse_project(main_resource)

        if component_list:
            print(f"{repo_id}:\n\t{file_count}\n\t{root_main_path}\n\t{component_list}")
        count += 1
    print(f"count={count}")


if __name__ == '__main__':
    main()
