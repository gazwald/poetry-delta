from pathlib import Path
import os, sys, json, 
import click
from process.repo import ProcessRepo
from process.local import ProcessLocal
from process import backup

CWD: Path = Path.cwd()
BRANCH: str = "main"
backup_dir = os.path.join(os.getenv('POETRY_HOME'), "backup")

@click.command()
@click.option("--path", default=CWD, help=f"Path to the repository; currently {CWD}")
@click.option(
    "--branch", default=BRANCH, help=f"Branch to inspect; default is '{BRANCH}'"
)
@click.option("--package", required=False, help="Package to filter on; e.g. boto3")
@click.option("--rev", required=False, help="Rev, see `git rev-parse` for details.")
@click.option("--local", is_flag=True, help="Use local project instead of Git repository")
@click.option("--backup", is_flag=True, help="Use last backup")
@click.option("--show", is_flag=True, help="Use in combination with --local or --backup or --autosave")


def main(
    path: Path,
    branch: str,
    local: bool = False,
    backup: bool = False,
    autosave: bool = False,
    show: bool = False,
    package: str | None = None,
    rev: str | None = None,
):
    if show:
        ProcessLocal(path).show()
    else:
        repo = ProcessRepo._fetch_repo(path)
        if repo is None:
            message = ["Local Mode"] 
            if package is not None:
                message.append(f"Filtering on package {package}")
            click.echo("\n".join(message))
            ProcessLocal(path, branch, package, local, backup, autosave)
            
        else:
            message: list[str] = [f"Inspecting branch '{branch}'"]
            if package is not None:
                message.append(f"Filtering on package {package}")
            click.echo("\n".join(message))
            ProcessRepo(path, branch, package, rev)
