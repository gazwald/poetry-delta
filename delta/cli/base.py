from pathlib import Path

import click
from process.repo import ProcessRepo
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
@click.option("--autosave", is_flag=True, help="Use last autosave")

def handle_local_project(path: Path, package: str | None = None):
    # Define current_version and previous_versions source type
    path: Path, branch: str, package: str, rev: str, local: bool, use_backup: bool, use_autosave: bool
):
    if use_backup:
        get_last_poetry_lock = get_last_backup()
    elif use_autosave:
        get_last_poetry_lock = get_autosave()

    # Load the current and previous versions of the files
    current_versions = load_file(os.path.join(find_pyproject_path(), "poetry.lock"))
    previous_versions = load_file(get_last_poetry_lock))

    # Compare the versions
    comparison = Compare(package, current_versions, previous_versions)
    print(comparison.state.name)

def main(
    path: Path,
    branch: str,
    local: bool = False,
    backup: bool = False,
    autosave: bool = False,
    package: str | None = None,
    rev: str | None = None,
):
    repo = ProcessRepo._fetch_repo(path)
    if repo is None:
        handle_local_project(path, package)
        
    else:
        message: list[str] = [f"Inspecting branch '{branch}'"]
        if package is not None:
            message.append(f"Filtering on package {package}")
    
        click.echo("\n".join(message))
    
        ProcessRepo(path, branch, package, rev)
