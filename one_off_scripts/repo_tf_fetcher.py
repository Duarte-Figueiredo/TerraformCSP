import asyncio
import logging
import os.path

from beanie.odm.operators.update.general import Set
from github import Repository, Branch

import terraform_analyzer
from one_off_scripts import initialize_db, GithubSearchResult, DRY_RUN, OUTPUT_FOLDER
from terraform_analyzer.external import github_client

PAGE_SIZE = 50

# QUERY = {'main_tf': {'$ne': [], '$exists': True}, 'downloaded': {'$exists': False}}
QUERY = {'main_tf': {'$ne': [], '$exists': True}, 'downloaded': {'$exists': True}}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("repo_tf_fetcher")


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
        await github_search_result.update(Set({GithubSearchResult.downloaded: False}))
        return

    tf_root_parent_folder_path = os.path.dirname(root_main_tf_path)
    tf_main_file_name = os.path.basename(root_main_tf_path)

    if not DRY_RUN:
        try:
            commit_hash = fetch_hash(github_search_result.id, github_search_result.all_attributes["default_branch"])
            terraform_analyzer.download_terraform(author,
                                                  repo_name,
                                                  commit_hash,
                                                  tf_root_parent_folder_path,
                                                  tf_main_file_name,
                                                  f"{OUTPUT_FOLDER}/{github_search_result.id}")
        except Exception as e:
            logger.error(f"Failed to download {github_search_result.id}", exc_info=e)

            await github_search_result.update(Set({GithubSearchResult.downloaded: False}))
            return

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

        results = await GithubSearchResult.find(QUERY) \
            .skip(index) \
            .limit(PAGE_SIZE) \
            .to_list()

        for result in results:
            await fetch_repo(result)

        if not results:
            break

        index += PAGE_SIZE


if __name__ == '__main__':
    asyncio.run(main())
