#!/usr/bin/env python
import tomllib
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Generator

import click
import git
from rich.console import Console
from rich.table import Table

DEFAULT_BRANCH: str = "main"


class State(Enum):
    CHANGED = auto()
    UNCHANGED = auto()
    ADDED = auto()
    REMOVED = auto()
    UPGRADED = auto()
    DOWNGRADED = auto()
    ERROR = auto()


StateStyleMap: dict[State, str] = {
    State.CHANGED: "green",
    State.UNCHANGED: "dim",
    State.ADDED: "green",
    State.REMOVED: "red",
    State.UPGRADED: "green",
    State.DOWNGRADED: "red",
    State.ERROR: "white",
}


class Compare:
    current_state: State = State.UNCHANGED
    package: str
    current_versions: dict[str, str]
    previous_versions: dict[str, str]

    def __init__(
        self,
        package: str,
        current_versions: dict[str, str],
        previous_versions: dict[str, str],
    ) -> None:
        self.package = package
        self.current_versions = current_versions
        self.previous_versions = previous_versions
        self.state = self._check()

    def _check(self) -> State:
        if self._removed():
            return State.REMOVED
        if self._added():
            return State.ADDED
        if self._upgraded():
            return State.UPGRADED
        if self._downgraded():
            return State.DOWNGRADED
        if self._changed():
            return State.CHANGED

        return State.UNCHANGED

    def _added(self) -> bool:
        if self._present_in_current and not self._present_in_previous:
            return True

        return False

    def _removed(self) -> bool:
        if not self._present_in_current and self._present_in_previous:
            return True

        return False

    def _upgraded(self) -> bool:
        # TODO: Implement
        return False

    def _downgraded(self) -> bool:
        # TODO: Implement
        return False

    def _changed(self) -> bool:
        current_version: str | None = self._current_version
        previous_version: str | None = self._previous_version

        if (
            self._present_in_current
            and self._present_in_previous
            and current_version != previous_version
        ):
            return True

        return False

    @property
    def _present_in_current(self) -> bool:
        return self.package in self.current_versions

    @property
    def _present_in_previous(self) -> bool:
        return self.package in self.previous_versions

    @property
    def _current_version(self) -> str | None:
        return self.current_versions.get(self.package, None)

    @property
    def _previous_version(self) -> str | None:
        return self.previous_versions.get(self.package, None)


class CommitCompare:
    _commit: str
    _current_commit_data: dict[str, dict] = {}
    _previous_commit_data: dict[str, dict] = {}
    _ignore_unchanged: bool

    def __init__(
        self,
        commit: str,
        path: str,
        current_commit_data: dict[str, dict],
        previous_commit_data: dict[str, dict],
        ignore_unchanged: bool = True,
    ) -> None:
        self._commit = commit
        self._current_commit_data = current_commit_data
        self._previous_commit_data = previous_commit_data
        self._ignore_unchanged = ignore_unchanged
        self.changes = self._compare(path)

    def _get_current(self, path: str) -> dict:
        return self._current_commit_data.get(path, {})

    def _get_previous(self, path: str) -> dict:
        return self._previous_commit_data.get(path, {})

    def _current(self, path: str) -> Generator:
        for package, version in self._get_current(path).items():
            yield package, version

    def _previous(self, path: str) -> Generator:
        for package, version in self._get_previous(path).items():
            yield package, version

    def _get_current_date(self, path: str) -> str:
        return self._format_timestamp(self._get_current(path).get("date", ""))

    def _compare(self, path: str = "poetry.lock") -> list[dict[str, list[str] | str]]:
        rows: list[dict[str, list[str] | str]] = []
        date: str = self._get_current_date(path)

        for package, version in self._current(path):
            comparison = Compare(
                package, self._get_current(path), self._get_previous(path)
            )
            if self._ignore_unchanged and comparison.state == State.UNCHANGED:
                continue

            rows.append(
                {
                    "row": [
                        self._commit[:7],
                        date,
                        package,
                        version,
                        comparison.state.name,
                    ],
                    "style": StateStyleMap[comparison.state],
                }
            )

        return rows

    @staticmethod
    def _format_timestamp(date: float) -> str:
        return datetime.fromtimestamp(date).strftime("%Y-%m-%d %H:%M:%S")


def _load_file(repo: git.Repo, commit: str, filepath: str) -> dict:
    """
    Load the lock file from a commit
    """
    data: dict = {}
    try:
        show = repo.git.show(f"{commit}:{filepath}")
    except git.exc.GitCommandError:
        pass
    else:
        data = tomllib.loads(show)

    return data


def _fetch_repo(path: str) -> git.Repo:
    repo = git.Repo(path)
    return repo


def _create_table() -> Table:
    table = Table(
        title="Delta", show_header=True, show_lines=True, header_style="bold magenta"
    )
    table.add_column("Commit")
    table.add_column("Date")
    table.add_column("Package")
    table.add_column("poetry.lock")
    table.add_column("pyproject.toml")
    table.add_column("state")
    return table


def _generate_table_from_delta(delta: dict, ignore_unchanged: bool = True) -> Table:
    """
    Generate a rich table from the delta
    """
    table = _create_table()
    previous_data: dict = {}

    for commit, current_data in delta.items():
        comparison = CommitCompare(
            commit, "poetry.lock", current_data, previous_data, ignore_unchanged
        )
        for change in comparison.changes:
            table.add_row(*change["row"], style=change["style"])

        previous_data = current_data

    return table


def _load_files(repo: git.Repo, commit: str, paths: list[Path]) -> dict:
    return {str(path): _load_file(repo, commit, str(path)) for path in paths}


def _gather_commits(repo: git.Repo, branch: str, paths: dict[str, Path]) -> dict:
    delta: dict = {}
    commits: list[str] = []
    add_commit: bool = False

    for commit in repo.iter_commits(branch, paths=paths):
        data = _load_files(repo, commit, list(paths.values()))

        delta[commit.hexsha] = {
            "date": commit.committed_date,
            "poetry.lock": {},
            "pyproject.toml": {},
        }
        add_commit = False

        for path, path_contents in data.items():
            match path:
                case "poetry.lock": 
                    _load_poetry(path_contents)
                case "pyproject.toml":
                    _load_pyproject(path_contents)
                case _:
                    raise Exception("Nope")
        # TODO: Move into methods
        if poetry_lock_data and "package" in poetry_lock_data:
            delta[commit.hexsha]["poetry.lock"] = {
                package["name"]: package["version"]
                for package in poetry_lock_data["package"]
            }
            add_commit = True
        if pyproject_data:
            delta[commit.hexsha]["pyproject.toml"] = pyproject_data["tool"]["poetry"][
                "dependencies"
            ]
            add_commit = True

        if add_commit:
            commits.append(commit.hexsha)

    return delta, commits


def _preflight(paths: list[Path]):
    messages: list[str] = []
    for path in paths:
        messages.append(f"{path} not found")

    if messages:
        raise click.ClickException("Following errors triggered: {'\n'.join(messages)}")


def main(branch: str = DEFAULT_BRANCH):
    poetry_lock: Path = Path("poetry.lock")
    pyproject: Path = Path("pyproject.toml")
    _preflight([poetry_lock, pyproject])

    repo: git.Repo = _fetch_repo(".")

    table: Table = _generate_table_from_delta(delta)
    console = Console()
    console.print(table)


if __name__ == "__main__":
    main()
