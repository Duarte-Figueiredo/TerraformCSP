import asyncio
import logging
import os.path

from beanie.odm.operators.update.general import Set, Unset
from github import Repository, Branch

import terraform_analyzer
from one_off_scripts import initialize_db, GithubSearchResult, DRY_RUN, OUTPUT_FOLDER, MONGO_QUERY
from terraform_analyzer.external import github_client

PAGE_SIZE = 50

logger = logging.getLogger("repo_tf_fetcher")
logging.basicConfig(level=logging.INFO)

if not MONGO_QUERY:
    DEFAULT_QUERY = {'main_tf': {'$ne': [], '$exists': True}, 'downloaded': {'$exists': False}}
    logger.warning(f"QUERY env not set, falling back to '{DEFAULT_QUERY}'")
    MONGO_QUERY = DEFAULT_QUERY

RESET_QUERY = {'downloaded': {'$exists': True}}


# OUTPUT_FOLDER = "/home/duarte/Documents/Personal/Code/TerraformCSP/output"


class AmbiguousRootMain(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


def get_most_root_main_tf(main_tfs: [str]) -> str:
    tmp: dict[int, list[str]] = {}

    min_slash_count = 100
    main_tf: str
    for main_tf in main_tfs:
        slash_count = main_tf.count('/')

        if min_slash_count > slash_count:
            min_slash_count = slash_count

        if slash_count in tmp:
            tmp[slash_count].append(main_tf)
        else:
            tmp[slash_count] = [main_tf]

    if len(tmp[min_slash_count]) > 1:
        raise AmbiguousRootMain(f"Ambiguous root main.tf between '{tmp[min_slash_count]}'")

    return tmp[min_slash_count][0]


async def fetch_repo(github_search_result: GithubSearchResult):
    logger.info(f"@fetch_repo {github_search_result.id}")
    author, repo_name = github_search_result.id.split('/')

    try:
        root_main_tf_path: str = get_most_root_main_tf(github_search_result.main_tf)
    except AmbiguousRootMain as e:
        logger.error(f"Failed to download {github_search_result.id} due to {e.message}")
        if not DRY_RUN:
            await github_search_result.update(Set({GithubSearchResult.downloaded: False}))
        return

    tf_root_parent_folder_path = os.path.dirname(root_main_tf_path)
    tf_main_file_name = os.path.basename(root_main_tf_path)

    try:
        commit_hash = fetch_hash(github_search_result.id, github_search_result.all_attributes["default_branch"])
        terraform_analyzer.download_terraform(author,
                                              repo_name,
                                              commit_hash,
                                              tf_root_parent_folder_path,
                                              tf_main_file_name,
                                              OUTPUT_FOLDER)
    except Exception as e:
        logger.error(f"Failed to download {github_search_result.id}", exc_info=e)

        if not DRY_RUN:
            await github_search_result.update(Set({GithubSearchResult.downloaded: False}))
        return

    if not DRY_RUN:
        await github_search_result.update(Set({GithubSearchResult.downloaded: True}))


def fetch_hash(repo_id: str, default_branch: str) -> str:
    logger.info(f"@fetch_hash {repo_id}:{default_branch}")
    repo: Repository = github_client.get_repo(repo_id)

    branch: Branch = repo.get_branch(default_branch)

    return branch.commit.sha


async def main():
    await initialize_db()

    index = 0

    while True:
        logger.info(f"Processed {index}")

        results = await GithubSearchResult.find(MONGO_QUERY) \
            .skip(index) \
            .limit(PAGE_SIZE) \
            .to_list()

        for result in results:
            index += 1
            logger.info(f"Processed {index}")
            await fetch_repo(result)

        if not results:
            logger.info("Finished")
            break


async def reset_downloaded():
    await initialize_db()

    while True:
        results = await GithubSearchResult.find(RESET_QUERY) \
            .limit(PAGE_SIZE) \
            .to_list()

        result: GithubSearchResult

        for result in results:
            logger.info(f"Reset {result.id}")
            await result.update(Unset({GithubSearchResult.downloaded: None}))

        # if not results:
        break


if __name__ == '__main__':
    # asyncio.run(reset_downloaded())
    asyncio.run(main())
    # commit_hash = fetch_hash("Anil-Nadikuda/vpc-test", "main")
    # terraform_analyzer.download_terraform("Anil-Nadikuda",
    #                                       "vpc-test",
    #                                       commit_hash,
    #                                       "",
    #                                       "main.tf",
    #                                       OUTPUT_FOLDER)
