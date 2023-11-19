from datetime import datetime
from typing import Any, Generator

from process.compare import Compare
from process.state import State, StateStyleMap


class CommitCompare:
    changes: dict[str, str | list[str]] = {}
    _commit: str
    _date_formatted: str
    _date_timestamp: float
    _current_commit_data: dict[str, dict] = {}
    _previous_commit_data: dict[str, dict] = {}
    _package: str | None
    _ignore_unchanged: bool

    def __init__(
        self,
        commit: str,
        path: str,
        current_commit_data: dict[str, dict],
        previous_commit_data: dict[str, dict],
        package: str | None = None,
        ignore_unchanged: bool = True,
    ) -> None:
        self._commit = commit
        self._package = package
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
            if self._package is not None and package != self._package:
                continue

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
                        self._current_commit_data["author"],
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
