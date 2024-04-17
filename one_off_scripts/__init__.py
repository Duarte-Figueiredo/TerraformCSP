import os
from datetime import date, datetime
from typing import Optional, List

from beanie import Document, Indexed, init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

MONGO_DB_USER: str = os.environ['MONGO_DB_USER']
MONGO_DB_PASS: str = os.environ['MONGO_DB_PASS']
MONGO_DB_URL: str = os.environ.get('MONGO_DB_URL', '192.168.1.12:27017')
DRY_RUN: bool = os.environ.get('DRY_RUN', "True").lower() == 'true'

MONGO_DATABASE_URL = f"mongodb://{MONGO_DB_USER}:{MONGO_DB_PASS}@{MONGO_DB_URL}"
OUTPUT_FOLDER = "/output"


async def initialize_db():
    mongo_client = AsyncIOMotorClient(MONGO_DATABASE_URL)

    await init_beanie(database=mongo_client.thesis,
                      document_models=[GithubConfig, GithubSearchResult, GithubSearchResultDay])


class GithubConfig(Document):
    config_name: Indexed(str)
    last_date_queried: date
    total_results: int

    class Settings:
        name = "github-config"


class GithubSearchResultDay(Document):
    day_date: Indexed(date)
    total_results: int

    class Settings:
        name = "github-search-result-day"


class GithubSearchResult(Document):
    id: str
    repo_name: str
    star_gazers: int
    archived: bool
    is_fork: bool
    created_at: datetime
    last_pushed_at: datetime
    description: Optional[str]
    downloaded: Optional[bool] = None
    main_tf: Optional[List[str]] = None
    all_attributes: dict

    class Settings:
        name = "github-search-results"
