import copy
import random

SIZE = 9
EMPTY = 0


def deep_copy(board):
    return copy.deepcopy(board)


def create_empty_board():
    return [[EMPTY for _ in range(SIZE)] for _ in range(SIZE)]


def is_safe(board, row, col, num):
    # Check row and column
    for x in range(SIZE):
        if board[row][x] == num or board[x][col] == num:
            return False
    # Check 3x3 box
    start_row = row - row % 3
    start_col = col - col % 3
    for i in range(3):
        for j in range(3):
            if board[start_row + i][start_col + j] == num:
                return False
    return True


def fill_board(board):
    for row in range(SIZE):
        for col in range(SIZE):
            if board[row][col] == EMPTY:
                possible = list(range(1, SIZE + 1))
                random.shuffle(possible)
                for candidate in possible:
                    if is_safe(board, row, col, candidate):
                        board[row][col] = candidate
                        if fill_board(board):
                            return True
                        board[row][col] = EMPTY
                return False
    return True


def count_solutions(board, limit=2):
    """Count a board's solutions, capped at ``limit``."""
    if limit < 1:
        return 0

    working_board = deep_copy(board)

    def search():
        best_cell = None
        best_candidates = None

        for row in range(SIZE):
            for col in range(SIZE):
                if working_board[row][col] != EMPTY:
                    continue

                candidates = [
                    number
                    for number in range(1, SIZE + 1)
                    if is_safe(working_board, row, col, number)
                ]
                if not candidates:
                    return 0
                if best_candidates is None or len(candidates) < len(best_candidates):
                    best_cell = (row, col)
                    best_candidates = candidates
                    if len(candidates) == 1:
                        break
            if best_candidates is not None and len(best_candidates) == 1:
                break

        if best_cell is None:
            return 1

        row, col = best_cell
        solutions = 0
        for candidate in best_candidates:
            working_board[row][col] = candidate
            solutions += search()
            working_board[row][col] = EMPTY
            if solutions >= limit:
                return limit
        return solutions

    return min(search(), limit)


def remove_cells(board, clues):
    cells_to_remove = SIZE * SIZE - clues
    coordinates = [(row, col) for row in range(SIZE) for col in range(SIZE)]
    random.shuffle(coordinates)

    for row, col in coordinates:
        if cells_to_remove == 0:
            break
        if board[row][col] == EMPTY:
            continue

        value = board[row][col]
        board[row][col] = EMPTY
        if count_solutions(board) == 1:
            cells_to_remove -= 1
        else:
            board[row][col] = value

def generate_puzzle(clues=35):
    board = create_empty_board()
    fill_board(board)
    solution = deep_copy(board)
    remove_cells(board, clues)
    puzzle = deep_copy(board)
    return puzzle, solution
