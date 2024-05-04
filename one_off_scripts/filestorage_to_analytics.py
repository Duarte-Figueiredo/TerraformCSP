import logging
import os
import subprocess
from typing import Optional

from pydantic import BaseModel

from one_off_scripts import OUTPUT_FOLDER
from terraform_analyzer import LocalResource
from terraform_analyzer.core.hcl import hcl_project_parser
from terraform_analyzer.core.hcl.hcl_obj import TerraformResource
from terraform_analyzer.core.hcl.hcl_obj.hcl_resources import AwsLambda, AwsDynamoDb, AWSApiGatewayRestApi

logger = logging.getLogger("repo_tf_fetcher")
logging.basicConfig(level=logging.CRITICAL)

# WORTHY_CLASSES: set[str] = set(x.__name__ for x in [AwsLambdaTerraformPermission, AwsLambda, AwsDynamoDb])
WORTHY_CLASSES: set[str] = set(x.__name__ for x in [AWSApiGatewayRestApi, AwsLambda, AwsDynamoDb])


class Node(BaseModel):
    terraform_resource: TerraformResource
    connections: list[any] = []

    class Config:
        arbitrary_types_allowed = True


class Connection(BaseModel):
    connects_to: Node
    justification: set[str]


class Graph(BaseModel):
    nodes: [Node]

    def get_all_connections(self) -> [Connection]:
        conn = []
        node: Node
        for node in self.nodes:
            conn.extend(node.connections)
        return conn

    class Config:
        arbitrary_types_allowed = True


class RepoAnalytics(BaseModel):
    total_file_count: int
    repo_id: str
    num_of_resources: int
    type_of_resources: set[str]
    terraform_resources: [TerraformResource]

    def is_worthy(self) -> bool:
        return any(map(lambda x: "aws" in x.lower(), self.type_of_resources))

    def get_num_of_resources(self, resource_type: set[type(TerraformResource)]):
        count = 0
        for res in self.terraform_resources:
            if type(res) in resource_type:
                count += 1
        return count

    def __str__(self) -> str:
        return f"repo_id={self.repo_id} num_resource={self.num_of_resources} types={self.type_of_resources} " \
               f"file_count={self.total_file_count} "

    class Config:
        arbitrary_types_allowed = True


def _build_graph(terraform_resources: [TerraformResource]) -> Graph:
    nodes: [Node] = list(map(lambda x: Node(terraform_resource=x), terraform_resources))

    # todo add a node for each terraform_resource
    node: Node
    for node in nodes:
        references: set[str] = node.terraform_resource.get_references()

        other_node: Node
        for other_node in nodes:
            if node == other_node:
                continue

            other_resource_ids = other_node.terraform_resource.get_identifiers()

            if references.intersection(other_resource_ids):
                node.connections.append(other_node)

    return Graph(nodes=nodes)


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


def analyze_repo(repo_id: str) -> bool:
    project_path = f"{OUTPUT_FOLDER}/{repo_id}"
    file_count: int = _get_file_count(project_path)

    root_main_path = _get_root_main_path(project_path)

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

    repo_analytics = RepoAnalytics(total_file_count=file_count,
                                   repo_id=repo_id,
                                   num_of_resources=len(component_list),
                                   type_of_resources={x.__class__.__name__ for x in component_list},
                                   terraform_resources=component_list)
    if repo_analytics.is_worthy():
        graph: Graph = _build_graph(repo_analytics.terraform_resources)
        connection_size = len(graph.get_all_connections())
        if connection_size > 0:
            print(f"{repo_analytics.repo_id}\t conn={connection_size}")

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
        repo_id: str = _get_repo_id(author_path)

        try:
            success = analyze_repo(repo_id)
        except Exception as e:
            logger.error(f"Failed to analyze {repo_id}")
            raise e

        if success:
            unskiped_repos += 1
        else:
            skiped_repos += 1

        count += 1

        if count % 1000 == 0:
            per = "{:.2f}".format(count / repo_count * 100)
            print(f"{per}%")

    print(f"count={count}\nunskiped_repos={unskiped_repos}\nskiped_repos={skiped_repos}")


if __name__ == '__main__':
    main()
    # analyze_repo(f"CLDNT/terraform-iam-mfa-enforcement")
    # analyze_repo('logesh81098/copy-files-from-S3-to-EFS-using-lambda')
    # analyze_repo('psifas-org-rnd/terraform-aws-control_tower_account_factory')
    # analyze_repo('toolforge/tf-infra-test')
    # psifas-org-rnd/terraform-aws-control_tower_account_factory
