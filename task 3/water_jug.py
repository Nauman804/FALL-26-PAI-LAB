from typing import List, Tuple, Optional, Set

State = Tuple[int, int]

def fill_x(state: State, cap_x: int) -> State:
    x, y = state
    return cap_x, y


def fill_y(state: State, cap_y: int) -> State:
    x, y = state
    return x, cap_y


def empty_x(state: State) -> State:
    x, y = state
    return 0, y


def empty_y(state: State) -> State:
    x, y = state
    return x, 0


def pour_x_to_y(state: State, cap_y: int) -> State:
    x, y = state
    amount = min(x, cap_y - y)
    return x - amount, y + amount


def pour_y_to_x(state: State, cap_x: int) -> State:
    x, y = state
    amount = min(y, cap_x - x)
    return x + amount, y - amount


class WaterJugSolver:
    def __init__(self, cap_x: int, cap_y: int, target: int):
        self.cap_x = cap_x
        self.cap_y = cap_y
        self.target = target
        self.visited: Set[State] = set()
        self.solution_path: List[Tuple[State, str]] = []

    def is_target(self, state: State) -> bool:
        x, y = state
        return x == self.target or y == self.target

    def dfs(self, state: State, path: List[Tuple[State, str]]) -> Optional[List[Tuple[State, str]]]:
        if state in self.visited:
            return None
        self.visited.add(state)

        if self.is_target(state):
            return path

        moves = [
            (lambda s: fill_x(s, self.cap_x), "Fill X"),
            (lambda s: fill_y(s, self.cap_y), "Fill Y"),
            (empty_x, "Empty X"),
            (empty_y, "Empty Y"),
            (lambda s: pour_x_to_y(s, self.cap_y), "Pour X->Y"),
            (lambda s: pour_y_to_x(s, self.cap_x), "Pour Y->X"),
        ]

        for move, name in moves:
            new_state = move(state)
            if new_state == state:
                continue
            result = self.dfs(new_state, path + [(new_state, name)])
            if result is not None:
                return result

        return None

    def solve(self) -> None:
        start_state: State = (0, 0)
        path = [(start_state, "Start")]
        solution = self.dfs(start_state, path)
        if solution:
            print("Solution found:\n")
            for state, rule in solution:
                print(f"State: {state}  Rule: {rule}")
        else:
            print("No solution")


if __name__ == "__main__":
    print("Starting water jug solver...")
    solver = WaterJugSolver(4, 3, 2)
    solver.solve()
