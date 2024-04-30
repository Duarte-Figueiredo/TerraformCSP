import logging
import os
import subprocess
from typing import Optional

from pydantic import BaseModel

from one_off_scripts import OUTPUT_FOLDER
from terraform_analyzer import LocalResource
from terraform_analyzer.core.hcl import hcl_project_parser
from terraform_analyzer.core.hcl.hcl_obj import TerraformResource

# OUTPUT_FOLDER = "/home/duarte/Documents/Personal/Code/TerraformCSP/output"

logger = logging.getLogger("repo_tf_fetcher")


class RepoAnalytics(BaseModel):
    total_file_count: int
    repo_id: str
    num_of_resources: int
    type_of_resources: set[str]
    terraform_resources: [TerraformResource]

    class Config:
        arbitrary_types_allowed = True

    def __str__(self) -> str:
        return f"repo_id={self.repo_id} num_resource={self.num_of_resources} types={self.type_of_resources} " \
               f"file_count={self.total_file_count} "


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


def analyze_repo(repo_id: str) -> bool:
    project_path = f"{OUTPUT_FOLDER}/{repo_id}"
    file_count: int = get_file_count(project_path)

    root_main_path = get_root_main_path(project_path)

    if not root_main_path:
        # https://github.com/mbrydak/glowing-couscous/tree/main/task2/terraform/net
        # https://github.com/CMS-Enterprise/batcave-tf-eso
        # https://github.com/aspaceincloud/IAC/blob/master/env/dev/main.tf

        logger.warning(f"Failed to find {repo_id} 'main.tf' file")
        return False

    name = os.path.basename(root_main_path)

    main_resource = LocalResource(full_path=root_main_path,
                                  name=name,
                                  is_directory=False)

    component_list: list[TerraformResource] = hcl_project_parser.parse_project(main_resource)

    if len(component_list) > 2:
        repo_analytics = RepoAnalytics(total_file_count=file_count,
                                       repo_id=repo_id,
                                       num_of_resources=len(component_list),
                                       type_of_resources={x.__class__.__name__ for x in component_list},
                                       terraform_resources=component_list)

        print(f"{repo_analytics}")
        for component in component_list:
            print(f"\t\t{component.get_terraform_name()}: {component}")

        return True
    return False


def main():
    count = 0
    repo_list = os.listdir(OUTPUT_FOLDER)
    repo_count = len(repo_list)

    skiped_repos = 0
    unskiped_repos = 0
    for author_name in repo_list:
        author_path = f"{OUTPUT_FOLDER}/{author_name}"
        repo_id: str = get_repo_id(author_path)

        if analyze_repo(repo_id):
            unskiped_repos += 1
        else:
            skiped_repos += 1

        count += 1

        if count % 10 == 0:
            per = "{:.2f}".format(count / repo_count * 100)
            print(f"{per}%")

    print(f"count={count}\nunskiped_repos={unskiped_repos}\nskiped_repos={skiped_repos}")


if __name__ == '__main__':
    main()
