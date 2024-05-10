import logging
import os
import subprocess
import time
from typing import Optional

from pydantic import BaseModel

from one_off_scripts import OUTPUT_FOLDER
from terraform_analyzer import LocalResource, ui
from terraform_analyzer.core.hcl import hcl_project_parser
from terraform_analyzer.core.hcl.hcl_obj import TerraformResource
from terraform_analyzer.core.hcl.hcl_obj.hcl_resources import AwsLambda, AwsDynamoDb, AwsApiGatewayRestApi
from terraform_analyzer.core.schema import schema_factory, GraphTf

logger = logging.getLogger("repo_tf_fetcher")
logging.basicConfig(level=logging.WARNING)

# WORTHY_CLASSES: set[str] = set(x.__name__ for x in [AwsLambdaTerraformPermission, AwsLambda, AwsDynamoDb])
WORTHY_CLASSES: set[str] = set(x.__name__ for x in [AwsApiGatewayRestApi, AwsLambda, AwsDynamoDb])

ERRORS = 0
TOTAL_CONNECTIONS = 0


class RepoAnalytics(BaseModel):
    total_file_count: int
    repo_id: str
    num_of_resources: int
    type_of_resources: set[str]
    terraform_resources: list[TerraformResource]

    def is_worthy(self) -> bool:
        # return any(map(lambda x: "aws" in x.lower(), self.type_of_resources))
        return WORTHY_CLASSES.issubset(self.type_of_resources)

    def get_num_of_resources(self, resource_type: set[type(TerraformResource)]):
        count = 0
        for res in self.terraform_resources:
            if type(res) in resource_type:
                count += 1
        return count

    def get_res_names(self):
        res_names: set[str] = set()

        for res in self.terraform_resources:
            res_names.add(f"{res.get_cloud_resource_type().value}:{res.get_identifiers()}")

        return res_names

    def __str__(self) -> str:
        return f"repo_id={self.repo_id} num_resource={self.num_of_resources} types={self.type_of_resources} " \
               f"file_count={self.total_file_count} "

    class Config:
        arbitrary_types_allowed = True




def _get_file_count(full_path: str) -> int:
    cmd = f"find {full_path} | wc -l"
    result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, text=True)

    file_count = int(result.stdout.removesuffix('\n'))

    return file_count


def _get_repo_id(path: str) -> str:
    repo_name = os.listdir(path)[0]
    author_name = os.path.basename(path)

    return f"{author_name}/{repo_name}"


# noinspection PyUnboundLocalVariable
def _get_root_main_path(project_path: str) -> Optional[str]:
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


def analyze_repo(repo_id: str) -> Optional[RepoAnalytics]:
    project_path = f"{OUTPUT_FOLDER}/{repo_id}"
    file_count: int = _get_file_count(project_path)

    root_main_path = _get_root_main_path(project_path)

    if not root_main_path:
        # https://github.com/mbrydak/glowing-couscous/tree/main/task2/terraform/net
        # https://github.com/CMS-Enterprise/batcave-tf-eso
        # https://github.com/aspaceincloud/IAC/blob/master/env/dev/main.tf

        logger.warning(f"Failed to find {repo_id} 'main.tf' file")
        return None

    name = os.path.basename(root_main_path)

    main_resource = LocalResource(full_path=root_main_path,
                                  name=name,
                                  is_directory=False)

    component_list: list[TerraformResource] = hcl_project_parser.parse_project(main_resource)

    return RepoAnalytics(total_file_count=file_count,
                         repo_id=repo_id,
                         num_of_resources=len(component_list),
                         type_of_resources={x.__class__.__name__ for x in component_list},
                         terraform_resources=component_list)


def analyze_single_repo(repo_id: str) -> bool:
    try:
        repo_analytics: RepoAnalytics = analyze_repo(repo_id)

        # if repo_analytics is None or not repo_analytics.is_worthy():
        #     return False

        graph: GraphTf = schema_factory.build_graph(repo_analytics.terraform_resources)
        connections = graph.connections

        # if len(connections) == 0:
        #     return False

        print(f"{repo_analytics.repo_id}:\n\t"
              f"conn_count={len(connections)}\n\t"
              f"conn_types={graph.get_connections_types_str()}\n\t"
              f"conn={graph.get_connections_str()}\n\t"
              f"res_count={len(repo_analytics.terraform_resources)}\n\t"
              f"res_types={repo_analytics.type_of_resources}\n\t"
              f"res_names={repo_analytics.get_res_names()}\n")

        ui.show_graph(graph)

        global TOTAL_CONNECTIONS
        TOTAL_CONNECTIONS += len(connections)
        return True

    except FileNotFoundError as e:

        logger.error(f"Missing files for {repo_id}\t{os.path.basename(str(e.filename))}")
        global ERRORS
        ERRORS += 1
    except Exception as e:
        logger.error(f"Failed to analyze {repo_id}")
        raise e


# philyang07/hhc-auth-verify
# ethanmick/minecraft
# bespinian/serverless-testing-workshop
def main():
    count = 0
    repo_list = []  # os.listdir(OUTPUT_FOLDER)
    repo_count = 0  # len(repo_list)

    skiped_repos = 0
    unskiped_repos = 0

    with open("/home/duarte/Documents/Personal/Code/TerraformCSP/tf_repos_with_docker.txt", 'r') as file:
        author_repo = file.readline()

        while author_repo:
            author, _ = author_repo.split("/", 1)

            repo_list.append(author)
            author_repo = file.readline()

    for author_name in repo_list:
        author_path = f"{OUTPUT_FOLDER}/{author_name}"
        repo_id: str = _get_repo_id(author_path)

        if analyze_single_repo(repo_id):
            unskiped_repos += 1
        else:
            skiped_repos += 1

        count += 1

        # if count % 1000 == 0:
        #     per = "{:.2f}".format(count / repo_count * 100)
        #     print(f"{per}%")

    output_str = f"\n### {time.asctime()} ###\n" \
                 f"count={count}\n" \
                 f"unskiped_repos={unskiped_repos}\n" \
                 f"skiped_repos={skiped_repos}\n" \
                 f"total_connections_count={TOTAL_CONNECTIONS}\n" \
                 f"Missing files:{ERRORS}\n######"
    print(output_str)
    # open("/home/duarte/Documents/Personal/Code/TerraformCSP/output.log", 'a').write(output_str)


if __name__ == '__main__':
    main()
    # analyze_repo(f"CLDNT/terraform-iam-mfa-enforcement")
    # analyze_repo('logesh81098/copy-files-from-S3-to-EFS-using-lambda')
    # analyze_repo('psifas-org-rnd/terraform-aws-control_tower_account_factory')
    # analyze_repo('toolforge/tf-infra-test')
    # psifas-org-rnd/terraform-aws-control_tower_account_factory
