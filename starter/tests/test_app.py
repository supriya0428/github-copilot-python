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
    solution = copy.deepcopy(app_module.CURRENT['solution'])
    incorrect_board = copy.deepcopy(solution)
    incorrect_board[0][0] = (incorrect_board[0][0] % 9) + 1

    incorrect_response = client.post('/check', json={'board': incorrect_board})
    correct_response = client.post('/check', json={'board': solution})

    assert incorrect_response.status_code == 200
    assert [0, 0] in incorrect_response.get_json()['incorrect']
    assert correct_response.status_code == 200
    assert correct_response.get_json() == {'incorrect': []}