from pathlib import Path

import click
from process.repo import ProcessRepo

CWD: Path = Path.cwd()
BRANCH: str = "main"


@click.command()
@click.option("--path", default=CWD, help=f"Path to the repository; currently {CWD}")
@click.option(
    "--branch", default=BRANCH, help=f"Branch to inspect; default is '{BRANCH}'"
)
@click.option("--package", required=False, help="Package to filter on; e.g. boto3")
@click.option("--rev", required=False, help="Rev, see `git rev-parse` for details.")
@click.option("--local", is_flag=True, help="Use local project instead of Git repository")

def handle_local_project(path: Path, package: str | None = None):
    # Define source and destination directories
    source_dir = os.path.expanduser("~/.local/bin/pypoetry/Cache/virtualenvs/envsystem")
    destination_dir = "C:/AI/POETRYGHOST/_autosave/envsystem/"
    tmp_dir = os.path.join(destination_dir, "tmp")

    # Create source directory if it doesn't exist
    os.makedirs(source_dir, exist_ok=True)

    # Create destination directory if it doesn't exist
    os.makedirs(destination_dir, exist_ok=True)

    # Create tmp directory if it doesn't exist
    os.makedirs(tmp_dir, exist_ok=True)

    # Backup pyproject.toml, poetry.lock, and requirements.txt
    shutil.copy2(os.path.join(source_dir, "pyproject.toml"), tmp_dir)
    shutil.copy2(os.path.join(source_dir, "poetry.lock"), tmp_dir)
    shutil.copy2(os.path.join(source_dir, "requirements.txt"), tmp_dir)

    # Load the current and previous versions of the files
    current_versions = load_file(os.path.join(source_dir, "poetry.lock"))
    previous_versions = load_file(os.path.join(tmp_dir, "poetry.lock.bak"))

    # Compare the versions
    comparison = Compare(package, current_versions, previous_versions)
    print(comparison.state.name)

def main(
    path: Path,
    branch: str,
    local: bool = False,
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
