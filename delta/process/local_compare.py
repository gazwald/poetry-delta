from typing import List
import os
import json
from process.state import State
from process.compare import Compare
from process import backup

class Package:
    def __init__(self, name: str, version: str):
        self.name = name
        self.version = version

    def __str__(self):
        return f"{self.name}@{self.version}"


class PoetryLock:
    def __init__(self, packages: List[dict]):
        self.packages = packages

    def convert_to_packages(self) -> List[Package]:
        return [Package(p['name'], p['version']) for p in self.packages]


def parse_lock(name: str, contents: str) -> List[Package]:
    if name == "poetry.lock":
        return PoetryLock(json.loads(contents)['package']).convert_to_packages()
    else:
        raise ValueError("Unsupported lock file format. Only poetry.lock is supported.")


def LocalCompare:
    def __init__(self, package: Package, use_backup: bool = False, use_autosave: bool = False):
        self.package = package
        self.use_backup = use_backup
        self.use_autosave = use_autosave


    def _get_state(self) -> str:
        current_versions = self.package.versions
        if self.use_backup:
            backup_versions = get_last_backup(self.package.name)
            state = compare_current_with_backup(self.package.name, current_versions, backup_versions)
        elif self.use_autosave:
            autosave_versions = get_autosave(self.package.name)
            state = compare_current_with_autosave(self.package.name, current_versions, autosave_versions)
        else:
            state = Compare(self.package.name, current_versions).state
        return state.name
