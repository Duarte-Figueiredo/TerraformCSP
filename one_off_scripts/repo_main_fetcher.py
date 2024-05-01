import asyncio
import logging
from typing import List, Union

from beanie.odm.operators.update.general import Set
from github import Repository
from github.ContentFile import ContentFile
from github.PaginatedList import PaginatedList

from one_off_scripts import initialize_db, GithubSearchResult, DRY_RUN, MONGO_QUERY
from terraform_analyzer.external import github_client
from terraform_analyzer.external.github_manager import GithubFileType

logger = logging.getLogger("repo_main_fetcher")
# logging.basicConfig(level=logging.ERROR)

FILE_SEARCH_NAME = "main.tf"
PAGE_SIZE = 50

if not MONGO_QUERY:
    DEFAULT_QUERY = {'main_tf': {'$exists': False}}
    logger.warning(f"QUERY env not set, falling back to '{DEFAULT_QUERY}'")
    MONGO_QUERY = DEFAULT_QUERY


def find_github_main_root_tf_bfs(repo_name: str) -> List[ContentFile]:
    logger.info(f"Breath first search '{FILE_SEARCH_NAME}' in '{repo_name}'")

    repo: Repository
    try:
        repo = github_client.get_repo(repo_name)
    except Exception as e:
        logger.error(f"Failed to fetch {repo_name}", exc_info=e)
        return []

    root_contents = repo.get_contents("/")

    folder_to_visit: [ContentFile] = root_contents if type(root_contents) is list else [root_contents]

    main_tf_found: bool = False
    mains: [ContentFile] = []

    while folder_to_visit:
        content: ContentFile = folder_to_visit.pop(0)
        logger.debug(f"Visiting {content.path}/{content.name}")

        if content.type == GithubFileType.DIR.value:
            if not main_tf_found:
                tmp: Union[list[ContentFile], ContentFile] = repo.get_contents(content.path)
                if type(tmp) is list:
                    folder_to_visit.extend(tmp)
                else:
                    folder_to_visit.append(tmp)
        elif content.type == GithubFileType.FILE.value:
            if content.name == FILE_SEARCH_NAME:
                mains.append(content)
                main_tf_found = True
        elif content.type == GithubFileType.SYMLINK.value:
            continue
        else:
            raise RuntimeError(f"Unrecognized github file type '{content.type}'")

    return mains


def find_github_main_root_tf(repo_name: str) -> List[ContentFile]:
    search_query = f"filename:{FILE_SEARCH_NAME} repo:{repo_name}"

    files: PaginatedList[ContentFile] = github_client.search_code(
        query=search_query
    )

    mains: [ContentFile] = []

    if files.totalCount == 0:
        return find_github_main_root_tf_bfs(repo_name)

    for file in files:
        mains.append(file)

    return mains


def fetch_repo_mains(repo: str) -> [str]:
    main_files: List[ContentFile] = find_github_main_root_tf(repo)

    logger.info(f"{repo}\t:extracted {len(main_files)} main.tf files")

    main_paths: [str] = []
    for content_file in main_files:
        main_paths.append(content_file.path)

    return main_paths


async def main():
    await initialize_db()

    index = 0

    while True:
        # noinspection PyTypeChecker,PyUnresolvedReferences
        results: [GithubSearchResult] = await GithubSearchResult.find(MONGO_QUERY) \
            .sort(-GithubSearchResult.star_gazers, -GithubSearchResult.last_pushed_at, -GithubSearchResult.created_at) \
            .skip(index) \
            .limit(PAGE_SIZE) \
            .to_list()

        for result in results:
            logger.info(f"{result.id}")

            mains = fetch_repo_mains(result.id)

            if not DRY_RUN:
                await result.update(Set({GithubSearchResult.main_tf: mains}))

            logger.info(f"{result.id}:{mains}")

        if not results:
            logger.info("Finished")
            break
        index += PAGE_SIZE


if __name__ == '__main__':
    asyncio.run(main())
