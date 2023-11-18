#!/usr/bin/env python
import tomllib
from datetime import datetime
from enum import Enum, auto
from operator import itemgetter
from pathlib import Path
from typing import Any, Generator

import click
import git
from packaging.version import Version, parse
from rich.console import Console
from rich.table import Table


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
    """
    Compare two versions of a package based on contents of current_versions and previous_versions
    current_versions and previous_versions are dicts with package name as key and version as value
    99 percent of the time this will be the contents of a poetry.lock file
    """

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

    def _compare_versions(self) -> State:
        if not self._present_in_both:
            return State.ERROR

        current: Version = parse(self._current_version)
        previous: Version = parse(self._previous_version)

        if current > previous:
            return State.UPGRADED
        if current < previous:
            return State.DOWNGRADED
        if current == previous:
            return State.UNCHANGED

        return State.ERROR

    def _upgraded(self) -> bool:
        if self._compare_versions() == State.UPGRADED:
            return True

        return False

    def _downgraded(self) -> bool:
        if self._compare_versions() == State.DOWNGRADED:
            return True

        return False

    def _changed(self) -> bool:
        if self._present_in_both and self._current_version != self._previous_version:
            return True

        return False

    @property
    def _present_in_current(self) -> bool:
        return self.package in self.current_versions

    @property
    def _present_in_previous(self) -> bool:
        return self.package in self.previous_versions

    @property
    def _present_in_both(self) -> bool:
        return self._present_in_current and self._present_in_previous

    @property
    def _current_version(self) -> str:
        return self.current_versions.get(self.package, "0.0.0")

    @property
    def _previous_version(self) -> str:
        return self.previous_versions.get(self.package, "0.0.0")


class CommitCompare:
    changes: dict[str, str | list[str]] = {}
    _commit: str
    _date_formatted: str
    _date_timestamp: float
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
        self._date_timestamp = current_commit_data["date"]
        self._date_formatted = self._format_timestamp(self._date_timestamp)
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

    def _compare(self, path: str = "poetry.lock") -> list[dict[str, str | list[str]]]:
        rows: list[dict[str, list[str] | str]] = []

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
                        self._date_formatted,
                        package,
                        version,
                        comparison.state.name,
                    ],
                    "style": StateStyleMap[comparison.state],
                }
            )

        return rows

    @staticmethod
    def _format_timestamp(date: Any) -> str:
        return datetime.fromtimestamp(date).strftime("%Y-%m-%d %H:%M:%S")


class ProcessRepo:
    repo: git.Repo
    branch: str
    files: list[Path] = [
        Path("poetry.lock"),
        Path("pyproject.toml"),
    ]

    def __init__(self, path: str | Path | None, branch: str | None = None) -> None:
        path = self._check_paths(path)
        self.repo = self._fetch_repo(path)
        self.branch = self._pick_branch() if branch is None else branch
        delta = self._gather_commits()
        rows = self._generate_table_rows_from_delta(delta)
        self._print_table(rows)

    def _check_paths(self, path: str | Path | None) -> Path:
        """
        Check if the path is valid
        """
        if path is None:
            click.echo("No path specified, defaulting to current working directory.")
            path = Path.cwd()

        if isinstance(path, str):
            path = Path(path)

        if not path.exists():
            raise click.ClickException(f"Path {path} does not exist")

        if not path.is_dir():
            raise click.ClickException(f"Path {path} is not a directory")

        messages = [
            f"{file} not found" for file in self.files if not (path / file).exists()
        ]

        if messages:
            raise click.ClickException(
                f"Following errors triggered:\n{'\n'.join(messages)}"
            )

        return path

    def _pick_branch(self) -> str:
        branch: str = self.repo.active_branch.name
        click.echo(f"No branch specified, using active branch: {branch}")
        return branch

    def _load_file(self, commit: str, filepath: str) -> dict:
        data: dict = {}
        try:
            show = self.repo.git.show(f"{commit}:{filepath}")
        except git.exc.GitCommandError:
            pass
        else:
            data = tomllib.loads(show)

        return data

    def _load_files(self, commit: str, paths: list[Path]) -> dict:
        return {str(path): self._load_file(commit, str(path)) for path in paths}

    @staticmethod
    def _load_poetry(data: dict) -> dict:
        if "package" in data:
            return {package["name"]: package["version"] for package in data["package"]}

        return {}

    @staticmethod
    def _load_pyproject(data: dict) -> dict:
        if "tool" in data:
            return data["tool"]["poetry"]["dependencies"]

        return {}

    @staticmethod
    def _fetch_repo(path: Path) -> git.Repo:
        try:
            repo = git.Repo(path)
        except git.exc.InvalidGitRepositoryError:
            raise click.ClickException(f"Path {path} is not a git repository")

        return repo

    @staticmethod
    def _create_table() -> Table:
        table = Table(
            title="Delta",
            show_header=True,
            show_lines=True,
            header_style="bold magenta",
        )
        table.add_column("Commit")
        table.add_column("Date")
        table.add_column("Package")
        table.add_column("poetry.lock")
        table.add_column("pyproject.toml")
        table.add_column("state")
        return table

    def _generate_table_rows_from_delta(
        self, delta: dict, ignore_unchanged: bool = True
    ) -> list[dict[str, list[str] | str]]:
        table_data: list[dict[str, list[str] | str]] = []
        previous_data: dict = {}

        for commit, data in delta.items():
            comparison = CommitCompare(
                commit, "poetry.lock", data, previous_data, ignore_unchanged
            )
            table_data.append(comparison.changes)

            previous_data = data

        return table_data

    def _gather_commits(self) -> dict:
        delta: dict = {}
        commits = list(self.repo.iter_commits(self.branch, paths=self.files))
        commits.reverse()

        for commit in commits:
            data = self._load_files(commit, self.files)

            delta[commit.hexsha] = {
                "date": commit.committed_date,
                "poetry.lock": {},
                "pyproject.toml": {},
            }

            for path, path_contents in data.items():
                match path:
                    case "poetry.lock":
                        delta[commit.hexsha]["poetry.lock"] = self._load_poetry(
                            path_contents
                        )
                    case "pyproject.toml":
                        delta[commit.hexsha]["pyproject.toml"] = self._load_pyproject(
                            path_contents
                        )
                    case _:
                        raise click.ClickException(
                            f"Path {path} didn't match any of the paths I know how to process."
                        )

        return delta

    def _print_table(self, delta) -> None:
        table = self._create_table()

        for rows in delta:
            for row in rows:
                table.add_row(*itemgetter("row")(row), style=itemgetter("style")(row))

        console = Console()
        console.print(table)


def main(path: Path | None = None, branch: str | None = None):
    ProcessRepo(path, branch)


if __name__ == "__main__":
    main()
