#!/usr/bin/env python
import tomllib
from datetime import datetime
from pathlib import Path
from pprint import pprint

import click
import git
from rich.console import Console
from rich.table import Table

DEFAULT_BRANCH: str = "main"


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


def _generate_table_from_delta(delta: dict) -> Table:
    """
    Generate a rich table from the delta
    """
    table = Table(title="Delta", show_header=True, header_style="bold magenta")
    table.add_column("Commit", style="dim")
    table.add_column("Date", style="dim")
    table.add_column("Package", style="dim")
    table.add_column("poetry.lock", style="dim")
    table.add_column("pyproject.toml", style="dim")

    for commit, files in delta.items():
        lock_version: dict = files.get("poetry.lock", {})
        pyproject_version: dict = files.get("pyproject.toml", {})
        for package, version in lock_version.items():
            date: str = datetime.fromtimestamp(files["date"]).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
            style: str = "green"
            table.add_row(
                commit[:7],
                date,
                package,
                version,
                pyproject_version.get(package, ""),
                style=style,
            )

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
