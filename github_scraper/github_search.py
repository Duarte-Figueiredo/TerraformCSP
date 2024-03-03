import asyncio
import logging
import os
from datetime import datetime, date, time, timedelta
from typing import List, Coroutine, Optional

from beanie import init_beanie
from beanie.odm.operators.update.general import Set
from github import Github
from github.PaginatedList import PaginatedList
from github.Repository import Repository
from motor.motor_asyncio import AsyncIOMotorClient

from github_scraper import GithubConfig, GithubSearchResult, GithubSearchResultDay

ACCESS_TOKEN: str = os.environ['ACCESS_TOKEN']
MONGO_DB_USER: str = os.environ['MONGO_DB_USER']
MONGO_DB_PASS: str = os.environ['MONGO_DB_PASS']
MONGO_DB_URL: str = os.environ.get('MONGO_DB_URL', '192.168.1.12:27017')
DRY_RUN: bool = bool(os.environ.get('DRY_RUN', "True"))

MONGO_DATABASE_URL = f"mongodb://{MONGO_DB_USER}:{MONGO_DB_PASS}@{MONGO_DB_URL}"

CONFIG_NAME = "github_config"
CURRENT_DATE = datetime(2024, 3, 1)
DATE_FORMAT = "%Y-%m-%d"

MONGO_DATABASE_NAME = "thesis"

g = Github(ACCESS_TOKEN)
query = ''

logger = logging.getLogger("github_search")
logging.basicConfig(level=logging.INFO)


async def initialize_db():
    mongo_client = AsyncIOMotorClient(MONGO_DATABASE_URL)

    await init_beanie(database=mongo_client.thesis,
                      document_models=[GithubConfig, GithubSearchResult, GithubSearchResultDay])


async def get_github_config() -> GithubConfig:
    result: GithubConfig = await GithubConfig.find_one(GithubConfig.config_name == CONFIG_NAME)

    if result:
        return result

    logger.warning(f"Config '{CONFIG_NAME}' not found, creating it")
    gc = GithubConfig(config_name=CONFIG_NAME,
                      last_date_queried=CURRENT_DATE,
                      total_results=0)

    if not DRY_RUN:
        await gc.create()

    return gc


async def search_code(d: date, config: GithubConfig) -> int:
    date_str = d.strftime(DATE_FORMAT)

    created_query = f"{date_str}..{date_str}"
    # Print the list of repositories
    repositories: PaginatedList[Repository] = g.search_repositories(
        query="",
        language="HCL",
        created=created_query
    )

    logger.info(f"\tFetching for date {date_str}, got {repositories.totalCount} results")

    if not DRY_RUN:
        await GithubSearchResultDay(day_date=date_str,
                                    total_results=repositories.totalCount).create()

    if repositories.totalCount >= 1000:
        logger.error(f"Found a day '{date_str}' that had more than 1000 results")

    results_count = 0
    new_db_items: List[GithubSearchResult] = []
    for repo in repositories:
        results_count += 1
        logger.info(f" {repo.created_at} - {repo.full_name}  {results_count}/{repositories.totalCount}")

        result = GithubSearchResult(
            id=repo.full_name,
            repo_name=repo.name,
            star_gazers=repo.stargazers_count,
            archived=repo.archived,
            is_fork=repo.fork,
            created_at=repo.created_at,
            last_pushed_at=repo.pushed_at,
            description=repo.description,
            all_attributes=repo.raw_data
        )

        new_db_items.append(result)

        if results_count % 10 == 0:
            if not DRY_RUN:
                task1: Coroutine = GithubSearchResult.insert_many(new_db_items)
                task2: Coroutine = config.inc({GithubConfig.total_results: len(new_db_items)})
                await asyncio.gather(task1, task2)
            new_db_items = []

    if results_count != repositories.totalCount:
        logger.error(f"Total count mismatch {repositories.totalCount}!={results_count}")

    return results_count


async def get_latest_result_day() -> Optional[GithubSearchResultDay]:
    results = await GithubSearchResultDay.find() \
        .sort(GithubSearchResultDay.day_date) \
        .limit(1) \
        .to_list()
    return results[0] if results else None


async def cleanup_interrupted_day(config: GithubConfig):
    result: Optional[GithubSearchResultDay] = await get_latest_result_day()

    if not result:
        logger.warning("No days detected, assuming this is a fresh start")
        return

    latest_fully_processed_date: date = result.day_date + timedelta(days=1)
    lasted_processed_datetime: datetime = datetime.combine(latest_fully_processed_date, time(0, 0, 0))

    # if latest_fully_processed_date <= config.last_date_queried:
    logger.warning(f"Deleting all search results before date {lasted_processed_datetime}")

    delete_results: list[GithubSearchResult] = await GithubSearchResult.find(
        GithubSearchResult.created_at < lasted_processed_datetime).to_list()

    x = input(
        f"Found {len(delete_results)} github search results that have created_at date < {lasted_processed_datetime}\n"
        f"Do you wish to delete them? y/N")

    if x and x == 'y' and not DRY_RUN:
        for delete_result in delete_results:
            logger.info(f"Deleting {delete_result.repo_name} created at {delete_result.created_at}")
            await GithubSearchResult.delete(delete_result)
        logger.info(f"Deleting github search result day {latest_fully_processed_date}")
        await result.delete()


async def main():
    await initialize_db()
    config: GithubConfig = await get_github_config()

    await cleanup_interrupted_day(config)

    total_results = config.total_results

    logger.info(f"current total results {config.total_results}")

    next_date: date = config.last_date_queried

    logger.info(f"Starting on date {next_date}")

    while True:
        total_results += await search_code(next_date, config)

        if not DRY_RUN:
            await config.update(Set({GithubConfig.last_date_queried: next_date}))

        next_date = config.last_date_queried - timedelta(days=1)


if __name__ == '__main__':
    asyncio.run(main())

# molyswu/hand_detection
# hiteshsuthar01/OK-


# for repos
# fork:true or fork:only ?
# followers:>=n ?
# stars:n..n size:<n
# created:<YYYY-MM-DD ?
# pushed:>YYYY-MM-DD ?
# language:LANGUAGE ?
# topic:terraform
# template:false ?
# archived:false ?

# sorting repos
# sort:author-date-desc
# sort:committer-date-desc
# sort:updated-desc


# for code
# path:/main.tf = 300k repo

# DB
## Code Search
### query: str  [hash_key]
### page: int
### consumed_items: int

## Repo
### author: str [hash_key]
### name: str [sort_key]
### main_path: [List[str]]
### stars: int
### created_at: date
### last_commited_at: date


# languag="HCL"

# 808
# repositories: PaginatedList[ContentFile] = g.search_code(
#     query="",
#     # path="/main",
#     filename="/main.tf",
#     extension=".tf"
# )


# 952
# repositories: PaginatedList[ContentFile] = g.search_code(
#     query="",
#     language="HCL"
# )

# language:HCL created:2024-03-01..2024-03-01
