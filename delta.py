#!/usr/bin/env python
import tomllib
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from pprint import pprint

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
    sha: str
    package: str
    current_versions: dict[str, str]
    previous_versions: dict[str, str]

    def __init__(
        self,
        current_versions: dict[str, str],
        previous_versions: dict[str, str],
        package: str,
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


def _load(repo: git.Repo, commit: str, filepath: str) -> dict:
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


def _generate_table_from_delta(delta: dict, hide_unchanged: bool = True) -> Table:
    """
    Generate a rich table from the delta
    """
    table = _create_table()
    previous_lock_version: dict = {}
    previous_pyproject_version: dict = {}

    for commit, files in delta.items():
        lock_version: dict = files.get("poetry.lock", {})
        pyproject_version: dict = files.get("pyproject.toml", {})

        for package, version in lock_version.items():
            lock_comparison = Compare(lock_version, previous_lock_version, package)
            pyproject_comparison = Compare(
                pyproject_version, previous_pyproject_version, package
            )
            if hide_unchanged and lock_comparison.state == State.UNCHANGED:
                continue

            date: str = datetime.fromtimestamp(files["date"]).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
            table.add_row(
                commit[:7],
                date,
                package,
                version,
                pyproject_version.get(package, ""),
                lock_comparison.state.name,
                style=StateStyleMap[lock_comparison.state],
            )

        previous_lock_version = lock_version
        previous_pyproject_version = pyproject_version

    return table


def main(branch: str = DEFAULT_BRANCH):
    poetry_lock: Path = Path("poetry.lock")
    pyproject_toml: Path = Path("pyproject.toml")
    if not poetry_lock.exists() or not pyproject_toml.exists():
        raise click.ClickException("poetry.lock or pyproject.toml not found")

    repo: git.Repo = _fetch_repo(".")
    delta: dict = {}
    commits: list[str] = []
    add_commit: bool = False

    for commit in repo.iter_commits(branch, paths=[poetry_lock, pyproject_toml]):
        poetry_lock_data: dict = _load(repo, commit, str(poetry_lock))
        pyproject_toml_data: dict = _load(repo, commit, str(pyproject_toml))

        delta[commit.hexsha] = {
            "date": commit.committed_date,
            "poetry.lock": {},
            "pyproject.toml": {},
        }
        add_commit = False
        if poetry_lock_data and "package" in poetry_lock_data:
            delta[commit.hexsha]["poetry.lock"] = {
                package["name"]: package["version"]
                for package in poetry_lock_data["package"]
            }
            add_commit = True
        if pyproject_toml_data:
            delta[commit.hexsha]["pyproject.toml"] = pyproject_toml_data["tool"][
                "poetry"
            ]["dependencies"]
            add_commit = True

        if add_commit:
            commits.append(commit.hexsha)

    table: Table = _generate_table_from_delta(delta)
    console = Console()
    console.print(table)


if __name__ == "__main__":
    main()
