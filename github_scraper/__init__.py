from datetime import date, datetime
from typing import Optional

from beanie import Document, Indexed


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
    all_attributes: dict

    class Settings:
        name = "github-search-results"
