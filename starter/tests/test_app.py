import copy

import app as app_module


def test_index_returns_successfully():
    app_module.app.config.update(TESTING=True)
    client = app_module.app.test_client()

    response = client.get('/')

    assert response.status_code == 200


def test_new_game_returns_a_puzzle():
    app_module.app.config.update(TESTING=True)
    client = app_module.app.test_client()

    response = client.get('/new?clues=35')

    assert response.status_code == 200
    puzzle = response.get_json()['puzzle']
    assert len(puzzle) == 9
    assert all(len(row) == 9 for row in puzzle)
    assert app_module.CURRENT['solution'] is not None


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