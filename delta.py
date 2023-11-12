#!/usr/bin/env python
import tomllib
from pathlib import Path

import click
import git
from rich.console import Console
from rich.table import Table

DEFAULT_BRANCH: str = "master"


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
    table.add_column("Commit", style="dim", width=12)
    table.add_column("Package", style="dim", width=12)
    table.add_column("poetry.lock", style="dim", width=12)
    table.add_column("pyproject.toml", style="dim", width=12)

    for commit, packages in delta.items():
        for package, versions in packages.items():
            table.add_row(
                commit[:7],
                package,
                versions["poetry.lock"],
                versions["pyproject.toml"],
            )

    return table


def main(branch: str = DEFAULT_BRANCH):
    poetry_lock: Path = Path("poetry.lock")
    pyproject_toml: Path = Path("pyproject.toml")
    if not poetry_lock.exists() or not pyproject_toml.exists():
        raise click.ClickException("poetry.lock or pyproject.toml not found")

    repo: git.Repo = _fetch_repo(".")
    delta: dict = {}

    for commit in repo.iter_commits(branch, paths=[poetry_lock, pyproject_toml]):
        poetry_lock_data: dict = _load(repo, commit, str(poetry_lock))
        pyproject_toml_data: dict = _load(repo, commit, str(pyproject_toml))

        if poetry_lock_data or pyproject_toml_data:
            delta[commit.hexsha] = {
                "poetry.lock": {
                    package["name"]: package["version"]
                    for package in poetry_lock_data["packages"]
                },
                "pyproject.toml": {
                    package["name"]: package["version"]
                    for package in pyproject_toml_data["tool"]["poetry"]["dependencies"]
                },
            }

    table: Table = _generate_table_from_delta(delta)
    console = Console()
    console.print(table)


if __name__ == "__main__":
    main()
