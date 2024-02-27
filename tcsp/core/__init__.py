from typing import Tuple

from pydantic import BaseModel


class RemoteReference(BaseModel):
    path: str

    class Config:
        frozen = True


class RepoReference(RemoteReference):
    author: str
    project: str
    commit_hash: str


class GitHubReference(RepoReference):
    pass


class RemoteResource(BaseModel):
    remote_reference: RemoteReference
    is_directory: bool
    relative_path: Tuple[str, ...]
    name: str

    def get_relative_path(self) -> str:
        return "/".join(self.relative_path)

    def get_relative_path_with_name(self) -> str:
        rp = self.get_relative_path()

        return f"{self.get_relative_path()}/{self.name}" if rp else self.name

    def get_remote_abs_path(self) -> str:
        rel_p = self.get_relative_path()
        rem_p = self.remote_reference.path

        if not rel_p and not rem_p:
            return ""
        elif not rel_p:
            return rem_p
        elif not rem_p:
            return rel_p
        else:
            return f"{self.remote_reference.path}/{self.get_relative_path()}"

    def get_remote_abs_path_with_name(self) -> str:
        return f"{self.remote_reference.path}/{self.get_relative_path_with_name()}"

    def __str__(self) -> str:
        return self.get_remote_abs_path_with_name()

    class Config:
        frozen = True


class Resource(BaseModel):
    remote_resource: RemoteResource

    local_path: str
    name: str
    is_directory: bool

    class Config:
        frozen = True
