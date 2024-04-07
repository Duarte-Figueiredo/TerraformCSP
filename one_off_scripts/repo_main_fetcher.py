import asyncio
import logging
from typing import List

from github.ContentFile import ContentFile
from github.PaginatedList import PaginatedList

from one_off_scripts import initialize_db, GithubSearchResult, github_client, DRY_RUN

logger = logging.getLogger("mongo_git_fetcher")
logging.basicConfig(level=logging.INFO)


def find_github_main_root_tf(github_search_result: GithubSearchResult) -> List[ContentFile]:
    repo_name = github_search_result.id
    search_query = f"filename:main.tf repo:{repo_name}"

    files: PaginatedList[ContentFile] = github_client.search_code(
        query=search_query
    )

    mains: [ContentFile] = []

    if files.totalCount == 0:
        logger.info(f"{repo_name}:\tnothing")
        return mains

    for file in files:
        mains.append(file)

    logger.info(f"{repo_name}\t:extracted {len(mains)} main.tf files")

    return mains


async def fetch_repo(github_search_result: GithubSearchResult):
    logger.info(f"{github_search_result.id}\t--------")

    main_files: List[ContentFile] = find_github_main_root_tf(github_search_result)

    main_paths: [str] = []
    for content_file in main_files: main_paths.append(content_file.path)

    github_search_result.main_tf = main_paths

    if not DRY_RUN:
        await github_search_result.update()


# query = {'$or': [{'downloaded': False}, {'downloaded': {'$exists': False}}]}
query = {'main_tf': {'$exists': False}}


async def main():
    await initialize_db()

    while True:
        results = await GithubSearchResult.find(query) \
            .limit(10) \
            .to_list()

        for result in results:
            await fetch_repo(result)


if __name__ == '__main__':
    asyncio.run(main())
