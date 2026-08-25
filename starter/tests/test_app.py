import copy
from pathlib import Path

import app as app_module


def test_index_returns_successfully():
    app_module.app.config.update(TESTING=True)
    client = app_module.app.test_client()

    response = client.get('/')

    assert response.status_code == 200


def test_new_game_returns_a_puzzle():
    app_module.app.config.update(TESTING=True)
    client = app_module.app.test_client()

    response = client.get('/new?difficulty=medium')

    assert response.status_code == 200
    puzzle = response.get_json()['puzzle']
    assert len(puzzle) == 9
    assert all(len(row) == 9 for row in puzzle)
    assert app_module.CURRENT['solution'] is not None


def test_new_game_defaults_to_medium():
    app_module.app.config.update(TESTING=True)
    client = app_module.app.test_client()

    response = client.get('/new')
    puzzle = response.get_json()['puzzle']

    assert response.status_code == 200
    assert sum(cell != 0 for row in puzzle for cell in row) == 35


def test_new_game_supports_all_difficulty_levels():
    app_module.app.config.update(TESTING=True)
    client = app_module.app.test_client()

    for difficulty, clues in {'easy': 45, 'medium': 35, 'hard': 25}.items():
        response = client.get(f'/new?difficulty={difficulty}')
        puzzle = response.get_json()['puzzle']

        assert response.status_code == 200
        assert sum(cell != 0 for row in puzzle for cell in row) == clues
        assert app_module.sudoku_logic.count_solutions(puzzle) == 1


def test_new_game_rejects_invalid_difficulty():
    app_module.app.config.update(TESTING=True)
    client = app_module.app.test_client()

    response = client.get('/new?difficulty=impossible')

    assert response.status_code == 400
    assert response.get_json() == {'error': 'Invalid difficulty'}


def test_index_includes_difficulty_selector():
    app_module.app.config.update(TESTING=True)
    client = app_module.app.test_client()

    html = client.get('/').get_data(as_text=True)

    assert 'id="difficulty"' in html
    assert all(f'value="{difficulty}"' in html for difficulty in ('easy', 'medium', 'hard'))


def test_frontend_new_game_uses_selected_difficulty():
    javascript = Path(app_module.app.root_path, 'static', 'main.js').read_text()

    assert "document.getElementById('difficulty').value" in javascript
    assert "fetch(`/new?difficulty=${encodeURIComponent(difficulty)}`)" in javascript


def test_check_solution_requires_a_game_in_progress():
    app_module.CURRENT['solution'] = None
    app_module.app.config.update(TESTING=True)
    client = app_module.app.test_client()

    response = client.post('/check', json={'board': []})

    assert response.status_code == 400
    assert response.get_json() == {'error': 'No game in progress'}


def test_check_solution_reports_incorrect_cells_and_accepts_solution():
    app_module.app.config.update(TESTING=True)
    client = app_module.app.test_client()
    client.get('/new')
    puzzle = app_module.CURRENT['puzzle']
    solution = copy.deepcopy(app_module.CURRENT['solution'])
    incorrect_board = copy.deepcopy(solution)
    editable_cell = next(
        (row, column)
        for row in range(9)
        for column in range(9)
        if puzzle[row][column] == 0
    )
    row, column = editable_cell
    incorrect_board[row][column] = (incorrect_board[row][column] % 9) + 1

    incorrect_response = client.post('/check', json={'board': incorrect_board})
    correct_response = client.post('/check', json={'board': solution})

    assert incorrect_response.status_code == 200
    assert [row, column] in incorrect_response.get_json()['incorrect']
    assert correct_response.status_code == 200
    assert correct_response.get_json() == {'incorrect': []}


def test_check_solution_reports_only_incorrect_editable_cells():
    app_module.app.config.update(TESTING=True)
    client = app_module.app.test_client()
    client.get('/new')
    puzzle = copy.deepcopy(app_module.CURRENT['puzzle'])
    solution = copy.deepcopy(app_module.CURRENT['solution'])
    editable_cell = next(
        (row, column)
        for row in range(9)
        for column in range(9)
        if puzzle[row][column] == 0
    )
    row, column = editable_cell
    solution[row][column] = (solution[row][column] % 9) + 1

    response = client.post('/check', json={'board': solution})

    assert response.status_code == 200
    assert response.get_json()['incorrect'] == [[row, column]]


def test_check_solution_accepts_a_solved_puzzle_without_incorrect_cells():
    app_module.app.config.update(TESTING=True)
    client = app_module.app.test_client()
    client.get('/new')

    response = client.post('/check', json={'board': copy.deepcopy(app_module.CURRENT['solution'])})

    assert response.status_code == 200
    assert response.get_json() == {'incorrect': []}


def test_check_solution_rejects_invalid_board_values_and_shapes():
    app_module.app.config.update(TESTING=True)
    client = app_module.app.test_client()
    client.get('/new')

    invalid_boards = [
        [[10] * 9 for _ in range(9)],
        [[0] * 9 for _ in range(8)],
        [[0] * 9 for _ in range(9)],
    ]
    invalid_boards[-1][0][0] = '1'

    for board in invalid_boards:
        response = client.post('/check', json={'board': board})

        assert response.status_code == 400
        assert response.get_json() == {'error': 'Invalid board'}


def test_check_solution_rejects_changes_to_prefilled_cells():
    app_module.app.config.update(TESTING=True)
    client = app_module.app.test_client()
    client.get('/new')
    puzzle = copy.deepcopy(app_module.CURRENT['puzzle'])
    prefilled_cell = next(
        (row, column)
        for row in range(9)
        for column in range(9)
        if puzzle[row][column] != 0
    )
    row, column = prefilled_cell
    board = copy.deepcopy(app_module.CURRENT['solution'])
    board[row][column] = (board[row][column] % 9) + 1

    response = client.post('/check', json={'board': board})

    assert response.status_code == 400
    assert response.get_json() == {'error': 'Prefilled cells cannot be changed'}


def test_frontend_protects_prefilled_cells_and_marks_conflicts():
    javascript = Path(app_module.app.root_path, 'static', 'main.js').read_text()
    html = client = app_module.app.test_client().get('/').get_data(as_text=True)

    assert 'inp.disabled = true' in javascript
    assert 'hasConflict(i, j, val)' in javascript
    assert "classList.toggle('incorrect'" in javascript
    assert 'id="sudoku-board"' in html