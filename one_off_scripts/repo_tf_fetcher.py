import asyncio
import logging
import os.path

from beanie.odm.operators.update.general import Set
from github import Repository, Branch

import terraform_analyzer
from one_off_scripts import initialize_db, GithubSearchResult, DRY_RUN
from terraform_analyzer.external import github_client

query = {'main_tf': {'$ne': [], '$exists': True}, 'downloaded': {'$ne': True}}

OUTPUT_FOLDER = "/output"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("repo_tf_fetcher")


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
        raise RuntimeError(f"Ambiguous root main.tf between '{tmp[min_slash_count]}'")

    return tmp[min_slash_count][0]


async def fetch_repo(github_search_result: GithubSearchResult, commit_hash: str):
    logger.info(f"@fetch_repo {github_search_result.id}:{commit_hash}")
    author, repo_name = github_search_result.id.split('/')

    root_main_tf_path: str = get_most_root_main_tf(github_search_result.main_tf)

    tf_root_parent_folder_path = os.path.dirname(root_main_tf_path)
    tf_main_file_name = os.path.basename(root_main_tf_path)

    if not DRY_RUN:
        try:
            terraform_analyzer.download_terraform(author,
                                                  repo_name,
                                                  commit_hash,
                                                  tf_root_parent_folder_path,
                                                  tf_main_file_name,
                                                  f"{OUTPUT_FOLDER}/{github_search_result.id}")
        except Exception as e:
            logger.error(f"Failed to download {github_search_result.id}", e)

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

    while True:
        results = await GithubSearchResult.find(query) \
            .limit(10) \
            .to_list()

        for result in results:
            commit_hash = fetch_hash(result.id, result.all_attributes["default_branch"])
            await fetch_repo(result, commit_hash)


if __name__ == '__main__':
    asyncio.run(main())
