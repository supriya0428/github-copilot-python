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
    assert response.get_json()['difficulty'] == 'medium'


def test_new_game_stores_active_difficulty_only_after_success():
    app_module.app.config.update(TESTING=True)
    client = app_module.app.test_client()
    client.get('/new?difficulty=easy')

    assert app_module.CURRENT['difficulty'] == 'easy'


def test_invalid_new_game_preserves_existing_game_state():
    app_module.app.config.update(TESTING=True)
    client = app_module.app.test_client()
    client.get('/new?difficulty=hard')
    previous_state = {
        key: copy.deepcopy(value)
        for key, value in app_module.CURRENT.items()
        if key != 'hinted_cells'
    }
    previous_hinted_cells = app_module.CURRENT['hinted_cells'].copy()

    response = client.get('/new?difficulty=invalid')

    assert response.status_code == 400
    assert app_module.CURRENT == {**previous_state, 'hinted_cells': previous_hinted_cells}


def test_new_game_defaults_to_medium():
    app_module.app.config.update(TESTING=True)
    client = app_module.app.test_client()

    response = client.get('/new')
    puzzle = response.get_json()['puzzle']

    assert response.status_code == 200
    assert sum(cell != 0 for row in puzzle for cell in row) == 35


def test_new_game_resets_hint_state():
    app_module.app.config.update(TESTING=True)
    client = app_module.app.test_client()
    client.get('/new')
    client.post('/hint', json={'board': app_module.CURRENT['puzzle']})

    client.get('/new')

    assert app_module.CURRENT['hint_count'] == 0
    assert app_module.CURRENT['hinted_cells'] == set()


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


def test_hint_requires_a_game_in_progress():
    app_module.CURRENT['puzzle'] = None
    app_module.CURRENT['solution'] = None
    app_module.app.config.update(TESTING=True)
    client = app_module.app.test_client()

    response = client.post('/hint', json={'board': []})

    assert response.status_code == 400
    assert response.get_json() == {'error': 'No game in progress'}


def test_hint_returns_one_correct_editable_cell_and_tracks_count():
    app_module.app.config.update(TESTING=True)
    client = app_module.app.test_client()
    client.get('/new')
    puzzle = copy.deepcopy(app_module.CURRENT['puzzle'])

    response = client.post('/hint', json={'board': puzzle})
    data = response.get_json()

    assert response.status_code == 200
    assert data['row'] == 0
    assert data['column'] == next(column for column in range(9) if puzzle[0][column] == 0)
    assert data['value'] == app_module.CURRENT['solution'][data['row']][data['column']]
    assert data['hints_used'] == 1
    assert app_module.CURRENT['hint_count'] == 1
    assert (data['row'], data['column']) in app_module.CURRENT['hinted_cells']


def test_hint_does_not_overwrite_user_values_or_reuse_hinted_cells():
    app_module.app.config.update(TESTING=True)
    client = app_module.app.test_client()
    client.get('/new')
    puzzle = copy.deepcopy(app_module.CURRENT['puzzle'])
    editable = next((row, column) for row in range(9) for column in range(9) if puzzle[row][column] == 0)
    user_board = copy.deepcopy(puzzle)
    user_board[editable[0]][editable[1]] = 1

    first = client.post('/hint', json={'board': user_board}).get_json()
    second = client.post('/hint', json={'board': user_board}).get_json()

    assert [first['row'], first['column']] != [editable[0], editable[1]]
    assert [second['row'], second['column']] != [first['row'], first['column']]
    assert second['hints_used'] == 2


def test_hint_rejects_invalid_boards_and_prefilled_changes():
    app_module.app.config.update(TESTING=True)
    client = app_module.app.test_client()
    client.get('/new')
    puzzle = copy.deepcopy(app_module.CURRENT['puzzle'])
    prefilled = next((row, column) for row in range(9) for column in range(9) if puzzle[row][column] != 0)
    puzzle[prefilled[0]][prefilled[1]] = (puzzle[prefilled[0]][prefilled[1]] % 9) + 1

    for board in ([[0] * 9 for _ in range(8)], puzzle):
        response = client.post('/hint', json={'board': board})
        assert response.status_code == 400
        assert response.get_json()['error'] in ('Invalid board', 'Prefilled cells cannot be changed')


def test_hint_no_op_does_not_increment_count_when_board_is_full():
    app_module.app.config.update(TESTING=True)
    client = app_module.app.test_client()
    client.get('/new')
    solution = copy.deepcopy(app_module.CURRENT['solution'])
    app_module.CURRENT['hint_count'] = 2

    response = client.post('/hint', json={'board': solution})

    assert response.status_code == 200
    assert response.get_json() == {'hint': None, 'hints_used': 2}
    assert app_module.CURRENT['hint_count'] == 2


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


def test_hinted_solution_can_complete_a_puzzle():
    app_module.app.config.update(TESTING=True)
    client = app_module.app.test_client()
    client.get('/new')
    board = copy.deepcopy(app_module.CURRENT['puzzle'])
    while any(cell == 0 for row in board for cell in row):
        hint = client.post('/hint', json={'board': board}).get_json()
        if 'hint' in hint and hint['hint'] is None:
            break
        board[hint['row']][hint['column']] = hint['value']

    response = client.post('/check', json={'board': board})

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


def test_frontend_includes_hint_controls_and_behavior():
    javascript = Path(app_module.app.root_path, 'static', 'main.js').read_text()
    css = Path(app_module.app.root_path, 'static', 'styles.css').read_text()
    html = app_module.app.test_client().get('/').get_data(as_text=True)

    assert 'id="hint"' in html
    assert 'id="hint-count"' in html
    assert "fetch('/hint'" in javascript
    assert 'input.disabled = true' in javascript
    assert "classList.add('hinted')" in javascript
    assert '.sudoku-cell.hinted' in css


def test_frontend_includes_timer_completion_and_leaderboard_behavior():
    javascript = Path(app_module.app.root_path, 'static', 'main.js').read_text()
    html = app_module.app.test_client().get('/').get_data(as_text=True)

    assert 'id="timer"' in html
    assert 'id="leaderboard-list"' in html
    assert "Date.now() - gameStartedAt" in javascript
    assert 'clearInterval(timerInterval)' in javascript
    assert 'gameCompleted = true' in javascript
    assert 'LEADERBOARD_KEY = \'sudokuLeaderboard\'' in javascript
    assert 'DIFFICULTY_BONUSES' in javascript
    assert 'HINT_PENALTY_SECONDS' in javascript
    assert 'slice(0, 10)' in javascript
    assert 'hintsUsed' in javascript
    assert 'window.prompt' in javascript


def test_frontend_includes_accessible_theme_toggle_and_persistence():
    javascript = Path(app_module.app.root_path, 'static', 'main.js').read_text()
    html = app_module.app.test_client().get('/').get_data(as_text=True)

    assert 'id="theme-toggle"' in html
    assert 'aria-label="Toggle dark mode"' in html
    assert "document.documentElement.dataset.theme" in javascript
    assert "localStorage.getItem(THEME_KEY)" in javascript
    assert "localStorage.setItem(THEME_KEY, theme)" in javascript
    assert 'initializeTheme()' in javascript


def test_frontend_includes_box_identifiers_accessible_cells_and_semantic_messages():
    javascript = Path(app_module.app.root_path, 'static', 'main.js').read_text()

    assert "input.dataset.box" in javascript
    assert "box-tone-a" in javascript
    assert "box-tone-b" in javascript
    assert "aria-label', `Row ${i + 1}, Column ${j + 1}`" in javascript
    assert "message-${type}" in javascript
    assert 'style.color' not in javascript


def test_frontend_css_defines_themes_box_tones_and_responsive_layout():
    css = Path(app_module.app.root_path, 'static', 'styles.css').read_text()

    for variable in (
        '--page-background', '--primary-text', '--secondary-text',
        '--board-background', '--box-tone-a', '--box-tone-b', '--normal-cell',
        '--prefilled-cell', '--hinted-cell', '--incorrect-cell', '--focus-state',
        '--button-background', '--timer-text', '--leaderboard-background',
        '--success-message', '--error-message', '--neutral-message',
    ):
        assert variable in css
    assert ':root[data-theme="dark"]' in css
    assert '.sudoku-cell.box-tone-a' in css
    assert '.sudoku-cell.box-tone-b' in css
    assert 'width: min(92vw, 468px)' in css
    assert 'aspect-ratio: 1' in css
    assert 'flex-wrap: wrap' in css


def test_frontend_resets_timer_and_completion_on_new_game():
    javascript = Path(app_module.app.root_path, 'static', 'main.js').read_text()

    assert 'activeDifficulty = data.difficulty' in javascript
    assert "document.getElementById('timer').innerText = '00:00'" in javascript
    assert "document.getElementById('check-solution').disabled = false" in javascript
    assert "document.getElementById('hint').disabled = false" in javascript
    assert 'startTimer()' in javascript