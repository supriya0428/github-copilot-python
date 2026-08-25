import sudoku_logic


def is_complete_valid_board(board):
    expected = set(range(1, sudoku_logic.SIZE + 1))
    rows_valid = all(set(row) == expected for row in board)
    columns_valid = all(
        {board[row][column] for row in range(sudoku_logic.SIZE)} == expected
        for column in range(sudoku_logic.SIZE)
    )
    boxes_valid = all(
        {
            board[row][column]
            for row in range(box_row, box_row + 3)
            for column in range(box_column, box_column + 3)
        }
        == expected
        for box_row in range(0, sudoku_logic.SIZE, 3)
        for box_column in range(0, sudoku_logic.SIZE, 3)
    )
    return rows_valid and columns_valid and boxes_valid


def is_valid_puzzle(board):
    for row in range(sudoku_logic.SIZE):
        values = [board[row][column] for column in range(sudoku_logic.SIZE)]
        non_empty = [value for value in values if value != sudoku_logic.EMPTY]
        if any(value < sudoku_logic.EMPTY or value > sudoku_logic.SIZE for value in values):
            return False
        if len(non_empty) != len(set(non_empty)):
            return False

    for column in range(sudoku_logic.SIZE):
        values = [board[row][column] for row in range(sudoku_logic.SIZE)]
        non_empty = [value for value in values if value != sudoku_logic.EMPTY]
        if len(non_empty) != len(set(non_empty)):
            return False

    for box_row in range(0, sudoku_logic.SIZE, 3):
        for box_column in range(0, sudoku_logic.SIZE, 3):
            values = [
                board[row][column]
                for row in range(box_row, box_row + 3)
                for column in range(box_column, box_column + 3)
            ]
            non_empty = [value for value in values if value != sudoku_logic.EMPTY]
            if len(non_empty) != len(set(non_empty)):
                return False
    return True


UNIQUE_PUZZLE = [
    [5, 3, 0, 0, 7, 0, 0, 0, 0],
    [6, 0, 0, 1, 9, 5, 0, 0, 0],
    [0, 9, 8, 0, 0, 0, 0, 6, 0],
    [8, 0, 0, 0, 6, 0, 0, 0, 3],
    [4, 0, 0, 8, 0, 3, 0, 0, 1],
    [7, 0, 0, 0, 2, 0, 0, 0, 6],
    [0, 6, 0, 0, 0, 0, 2, 8, 0],
    [0, 0, 0, 4, 1, 9, 0, 0, 5],
    [0, 0, 0, 0, 8, 0, 0, 7, 9],
]


def test_count_solutions_returns_one_for_unique_puzzle_without_mutating_board():
    puzzle = [row[:] for row in UNIQUE_PUZZLE]

    assert sudoku_logic.count_solutions(puzzle) == 1
    assert puzzle == UNIQUE_PUZZLE


def test_count_solutions_returns_two_for_ambiguous_puzzle():
    ambiguous_puzzle = sudoku_logic.create_empty_board()

    assert sudoku_logic.count_solutions(ambiguous_puzzle) == 2

def test_create_empty_board_returns_nine_by_nine_empty_board():
    board = sudoku_logic.create_empty_board()

    assert len(board) == sudoku_logic.SIZE
    assert all(len(row) == sudoku_logic.SIZE for row in board)
    assert all(cell == sudoku_logic.EMPTY for row in board for cell in row)


def test_is_safe_rejects_existing_row_column_and_box_values():
    board = sudoku_logic.create_empty_board()
    board[0][0] = 1

    assert not sudoku_logic.is_safe(board, 0, 1, 1)
    assert not sudoku_logic.is_safe(board, 1, 0, 1)
    assert not sudoku_logic.is_safe(board, 1, 1, 1)
    assert sudoku_logic.is_safe(board, 1, 1, 2)


def test_fill_board_creates_a_complete_valid_board():
    board = sudoku_logic.create_empty_board()

    assert sudoku_logic.fill_board(board)
    assert is_complete_valid_board(board)


def test_generate_puzzle_returns_puzzle_with_matching_solution_and_clue_count():
    clues = 35
    puzzle, solution = sudoku_logic.generate_puzzle(clues)

    assert is_complete_valid_board(solution)
    assert is_valid_puzzle(puzzle)
    assert sudoku_logic.count_solutions(puzzle) == 1
    assert len(puzzle) == sudoku_logic.SIZE
    assert all(len(row) == sudoku_logic.SIZE for row in puzzle)
    assert sum(cell != sudoku_logic.EMPTY for row in puzzle for cell in row) == clues
    assert all(
        puzzle[row][column] in (sudoku_logic.EMPTY, solution[row][column])
        for row in range(sudoku_logic.SIZE)
        for column in range(sudoku_logic.SIZE)
    )


def test_generate_puzzle_supports_all_difficulty_clue_targets():
    for difficulty, clues in sudoku_logic.DIFFICULTY_CLUES.items():
        puzzle, solution = sudoku_logic.generate_puzzle(clues)

        assert sum(cell != sudoku_logic.EMPTY for row in puzzle for cell in row) == clues
        assert sudoku_logic.count_solutions(puzzle) == 1
        assert is_complete_valid_board(solution)


def test_generate_puzzle_retries_when_target_is_not_reached(monkeypatch):
    attempts = iter([False, True])
    original_remove_cells = sudoku_logic.remove_cells

    def remove_cells_with_one_failed_attempt(board, clues):
        if not next(attempts):
            return False
        return original_remove_cells(board, clues)

    monkeypatch.setattr(sudoku_logic, 'remove_cells', remove_cells_with_one_failed_attempt)

    puzzle, solution = sudoku_logic.generate_puzzle(45)

    assert sum(cell != sudoku_logic.EMPTY for row in puzzle for cell in row) == 45
    assert sudoku_logic.count_solutions(puzzle) == 1
    assert is_complete_valid_board(solution)