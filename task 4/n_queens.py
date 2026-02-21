"""Dynamic N-Queens Problem solver.

This module provides functions to compute all solutions to the N-Queens
problem using a backtracking approach with caching of partial states for
dynamic programming. The goal is to demonstrate a dynamic programming style
for solving the classic N-queens challenge.

Usage:
    python n_queens.py 8

This will print the number of solutions and optionally display each board.
"""

from functools import lru_cache
from typing import List, Tuple
import sys

Board = List[int]  # row -> column index of queen placement


def is_safe(row: int, col: int, board: Board) -> bool:
    """Check if it's safe to place a queen at (row, col) given existing board."""
    for r, c in enumerate(board):
        if c == col or abs(r - row) == abs(c - col):
            return False
    return True


@lru_cache(maxsize=None)
def count_solutions(n: int, row: int = 0, cols: Tuple[int, ...] = tuple()) -> int:
    """Count number of valid solutions for an N-queens board starting at a given row.

    This recursive function uses caching to avoid recomputing subproblems.
    The columns parameter is a tuple representing queen positions for previous rows.
    """
    if row == n:
        return 1

    total = 0
    for col in range(n):
        if all(col != c and abs(row - r) != abs(col - c) for r, c in enumerate(cols)):
            total += count_solutions(n, row + 1, cols + (col,))
    return total


def generate_solutions(n: int) -> List[Board]:
    """Generate all valid N-queen board configurations.

    This uses backtracking without caching since we return full boards.
    """
    def backtrack(row: int, cols: List[int], results: List[Board]):
        if row == n:
            results.append(cols.copy())
            return
        for col in range(n):
            if is_safe(row, col, cols):
                cols.append(col)
                backtrack(row + 1, cols, results)
                cols.pop()

    res: List[Board] = []
    backtrack(0, [], res)
    return res


def print_board(board: Board) -> None:
    n = len(board)
    for row in board:
        line = ". " * n
        line = list(line.split())
        line[row] = "Q"
        print(" ".join(line))
    print()


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python n_queens.py <n>")
        sys.exit(1)
    try:
        n = int(sys.argv[1])
    except ValueError:
        print("n must be an integer")
        sys.exit(1)

    print(f"Counting solutions for n={n} using dynamic caching...")
    total = count_solutions(n)
    print(f"Total solutions: {total}\n")

    print(f"Generating all solutions (for demonstration)...\n")
    solutions = generate_solutions(n)
    for sol in solutions:
        print_board(sol)
    print(f"Displayed {len(solutions)} solutions.")


if __name__ == "__main__":
    main()
