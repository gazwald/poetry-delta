from enum import Enum, auto


class State(Enum):
    CHANGED = auto()
    UNCHANGED = auto()
    ADDED = auto()
    REMOVED = auto()
    UPGRADED = auto()
    DOWNGRADED = auto()
    ERROR = auto()


StateStyleMap: dict[State, str] = {
    State.CHANGED: "green",
    State.UNCHANGED: "dim",
    State.ADDED: "blue",
    State.REMOVED: "red",
    State.UPGRADED: "green",
    State.DOWNGRADED: "orange",
    State.ERROR: "white",
}
