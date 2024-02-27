import logging

from tcsp.core import crawler, RemoteResource, GitHubReference

OUTPUT_FOLDER = "/home/duarte/Documents/Personal/Code/TerraformCSP/resources"

RESOURCE = "https://raw.githubusercontent.com/nargetdev/outserv/502e611e5e12c502f3e96ab1f09744a096900ab9/contrib/config/terraform/kubernetes/main.tf"

logging.basicConfig(level=logging.INFO)

if __name__ == '__main__':
    rrr = RemoteResource(remote_reference=GitHubReference(author="nargetdev",
                                                          project="outserv",
                                                          commit_hash="502e611e5e12c502f3e96ab1f09744a096900ab9",
                                                          path="contrib/config/terraform/kubernetes"),
                         is_directory=False,
                         relative_path=(),
                         name="main.tf")

    crawler.crawl(rrr, OUTPUT_FOLDER)
