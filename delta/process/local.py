from pathlib import Path
import os
import git
from typing import List
from process.local_compare import LocalCompare
from process.compare import Compare
from process.state import State, StateStyleMap
from rich.table import Table
import click


class ProcessLocal:
    local: not git.Repo
    files: list[Path] = [
        find_poetrylock_path(),
        find_pyproject_path(),
    ]

    def __init__(self, path: str, use_backup: bool = False, use_autosave: bool = False):
        self.path = path
        self.packages = self._load_packages()
        self.use_backup = use_backup
        self.use_autosave = use_autosave


    @staticmethod
    def load_poetry_lock(lock_path: str) -> List[Package]:
        lock_data = ProcessLocal.load_file(lock_path)
        poetry_lock = PoetryLock(lock_data['package'])
        return poetry_lock.convert_to_packages()

    @staticmethod
    def load_poetry_lock_backup(backup_path: str) -> List[Package]:
        lock_path = os.path.join(backup_path, 'poetry.lock')
        return ProcessLocal.load_poetry_lock(lock_path)

    @staticmethod
    def load_poetry_lock_autosave(autosave_path: str) -> List[Package]:
        lock_path = os.path.join(autosave_path, 'poetry.lock.bak')
        return ProcessLocal.load_poetry_lock(lock_path)

    @staticmethod
    def compare_with_backup(package: str, current_versions: List[Package]) -> State:
        backup_path = get_last_backup()
        if backup_path:
            backup_packages = ProcessLocal.load_poetry_lock_backup(backup_path)
            backup_versions = {package.name: package.version for package in backup_packages}
            return Compare(package, current_versions, backup_versions).state
        else:
            # Handle case when backup is not found
            return State.ERROR

    @staticmethod
    def compare_with_autosave(package: str, current_versions: List[Package]) -> State:
        autosave_path = get_autosave()
        if autosave_path:
            autosave_packages = ProcessLocal.load_poetry_lock_autosave(autosave_path)
            autosave_versions = {package.name: package.version for package in autosave_packages}
            return Compare(package, current_versions, autosave_versions).state
        else:
            # Handle case when autosave is not found
            return State.ERROR

    @staticmethod
    def _load_packages(path: str) -> List[Package]:
        with open(path, 'r') as f:
            contents = f.read()
        return parse_lock(os.path.basename(path), contents)


    def show(self):
        args = sys.argv
        if len(args) != 3:
            raise ValueError("Expected exactly two args")

        lock_path = args[2]
        name = os.path.basename(lock_path)
        with open(lock_path, 'r') as f:
            lock_contents = f.read()
        packages = parse_lock(name, lock_contents)
        for package in packages:
            print(package)


    def _generate_table_rows_from_packages(self) -> list[dict[str, list[str] | str]]:
        table_data: list[dict[str, list[str] | str]] = []
        for package in self.packages:
            if self.use_backup:
                state = self.compare_with_backup(package.name, self.packages)
            elif self.use_autosave:
                state = self.compare_with_autosave(package.name, self.packages)
            else:
                state = Compare(package.name, self.packages).state
            table_data.append({
                "Package": package.name,
                "Version": package.version,
                "State": state.name
            })
        return table_data


    def _print_table(self, rows):
        table = self._create_table()
        for row in rows:
            table.add_row(*row.values())
        console = Console()
        console.print(table)


    @staticmethod
    def _create_table() -> Table:
        table = Table(show_header=True, show_lines=True, header_style="magenta")
        table.add_column("Package")
        table.add_column("Version")
        table.add_column("State")
        return table