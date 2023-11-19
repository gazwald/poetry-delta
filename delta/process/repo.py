import tomllib
from operator import itemgetter
from pathlib import Path

import click
import git
from rich.console import Console
from rich.table import Table

from process.commit_compare import CommitCompare


class ProcessRepo:
    repo: git.Repo
    branch: str
    files: list[Path] = [
        Path("poetry.lock"),
        Path("pyproject.toml"),
    ]

    def __init__(
        self,
        path: str | Path | None,
        branch: str | None = None,
        package: str | None = None,
        rev: str | None = None,
    ) -> None:
        path = self._check_paths(path)
        self.repo = self._fetch_repo(path)
        self.branch = self._pick_branch() if branch is None else branch
        delta = self._gather_commits(rev)
        rows = self._generate_table_rows_from_delta(delta, package)
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
            if "poetry" in data["tool"]:
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
        table.add_column("Author")
        table.add_column("Package")
        table.add_column("poetry.lock")
        table.add_column("State")
        return table

    def _generate_table_rows_from_delta(
        self, delta: dict, package: str | None = None, ignore_unchanged: bool = True
    ) -> list[dict[str, list[str] | str]]:
        table_data: list[dict[str, list[str] | str]] = []
        previous_data: dict = {}

        for commit, data in delta.items():
            comparison = CommitCompare(
                commit, "poetry.lock", data, previous_data, package, ignore_unchanged
            )
            table_data.append(comparison.changes)

            previous_data = data

        return table_data

    def _gather_commits(self, rev: str | None) -> dict:
        delta: dict = {}
        if rev:
            commits = list(self.repo.iter_commits(rev, paths=self.files))
        else:
            commits = list(self.repo.iter_commits(self.branch, paths=self.files))
        commits.reverse()

        for commit in commits:
            data = self._load_files(commit, self.files)

            delta[commit.hexsha] = {
                "date": commit.committed_date,
                "author": commit.author.name,
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
