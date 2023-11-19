from pathlib import Path

import click
from process.repo import ProcessRepo

CWD: Path = Path.cwd()


@click.command()
@click.option("--path", default=CWD, help="Path to the repository; default is cwd")
@click.option("--branch", default="main", help="Branch to inspect")
@click.option("--package", required=False, help="Package to filter on")
@click.option("--rev", required=False, help="Rev, see `git rev-parse` for details.")
def main(path: Path, branch: str, package: str | None = None, rev: str | None = None):
    message: list[str] = [f"Processing {path}, on branch {branch}"]
    if package is not None:
        message.append(f"Filtering on package {package}")

    click.echo("\n".join(message))

    ProcessRepo(path, branch, package, rev)
