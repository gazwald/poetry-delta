from packaging.version import Version, parse

from process.state import State


class Compare:
    """
    Compare two versions of a package based on contents of current_versions and previous_versions
    current_versions and previous_versions are dicts with package name as key and version as value
    99 percent of the time this will be the contents of a poetry.lock file
    """

    current_state: State = State.UNCHANGED
    package: str
    current_versions: dict[str, str]
    previous_versions: dict[str, str]

    def __init__(
        self,
        package: str,
        current_versions: dict[str, str],
        previous_versions: dict[str, str],
    ) -> None:
        self.package = package
        self.current_versions = current_versions
        self.previous_versions = previous_versions
        self.state = self._check()

    def _check(self) -> State:
        if self._removed():
            return State.REMOVED
        if self._added():
            return State.ADDED
        if self._upgraded():
            return State.UPGRADED
        if self._downgraded():
            return State.DOWNGRADED
        if self._changed():
            return State.CHANGED

        return State.UNCHANGED

    def _added(self) -> bool:
        if self._present_in_current and not self._present_in_previous:
            return True

        return False

    def _removed(self) -> bool:
        if not self._present_in_current and self._present_in_previous:
            return True

        return False

    def _compare_versions(self) -> State:
        if not self._present_in_both:
            return State.ERROR

        current: Version = parse(self._current_version)
        previous: Version = parse(self._previous_version)

        if current > previous:
            return State.UPGRADED
        if current < previous:
            return State.DOWNGRADED
        if current == previous:
            return State.UNCHANGED

        return State.ERROR

    def _upgraded(self) -> bool:
        if self._compare_versions() == State.UPGRADED:
            return True

        return False

    def _downgraded(self) -> bool:
        if self._compare_versions() == State.DOWNGRADED:
            return True

        return False

    def _changed(self) -> bool:
        if self._present_in_both and self._current_version != self._previous_version:
            return True

        return False

    @property
    def _present_in_current(self) -> bool:
        return self.package in self.current_versions

    @property
    def _present_in_previous(self) -> bool:
        return self.package in self.previous_versions

    @property
    def _present_in_both(self) -> bool:
        return self._present_in_current and self._present_in_previous

    @property
    def _current_version(self) -> str:
        return self.current_versions.get(self.package, "0.0.0")

    @property
    def _previous_version(self) -> str:
        return self.previous_versions.get(self.package, "0.0.0")
