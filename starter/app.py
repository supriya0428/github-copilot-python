from flask import Flask, render_template, jsonify, request, session
import sudoku_logic
import os
import secrets
import uuid
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get(
    'SECRET_KEY',
    secrets.token_hex(32)
)
# Keep session-specific game state in memory.
CURRENT_GAMES = {}

def get_current_game():
    game_id = session.get('game_id')

    if game_id is None:
        game_id = str(uuid.uuid4())
        session['game_id'] = game_id

    return CURRENT_GAMES.setdefault(game_id, {
        'puzzle': None,
        'solution': None,
        'difficulty': None,
        'hint_count': 0,
        'hinted_cells': set(),
    })

def is_valid_submitted_board(board):
    if not isinstance(board, list) or len(board) != sudoku_logic.SIZE:
        return False
    return all(
        isinstance(row, list)
        and len(row) == sudoku_logic.SIZE
        and all(isinstance(cell, int) and not isinstance(cell, bool) and 0 <= cell <= sudoku_logic.SIZE for cell in row)
        for row in board
    )

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/new')
def new_game():
    difficulty = request.args.get('difficulty', 'medium').lower()
    if difficulty not in sudoku_logic.DIFFICULTY_CLUES:
        return jsonify({'error': 'Invalid difficulty'}), 400

    clues = sudoku_logic.DIFFICULTY_CLUES[difficulty]
    puzzle, solution = sudoku_logic.generate_puzzle(clues)
    game = get_current_game()
    game['puzzle'] = puzzle
    game['solution'] = solution
    game['difficulty'] = difficulty
    game['hint_count'] = 0
    game['hinted_cells'] = set()
    return jsonify({'puzzle': puzzle, 'difficulty': difficulty})


@app.route('/hint', methods=['POST'])
def provide_hint():
    data = request.json
    game = get_current_game()
    puzzle = game.get('puzzle')
    solution = game.get('solution')
    if puzzle is None or solution is None:
        return jsonify({'error': 'No game in progress'}), 400
    if not isinstance(data, dict):
        return jsonify({'error': 'Invalid board'}), 400

    board = data.get('board')
    if not is_valid_submitted_board(board):
        return jsonify({'error': 'Invalid board'}), 400

    for row in range(sudoku_logic.SIZE):
        for column in range(sudoku_logic.SIZE):
            if puzzle[row][column] != sudoku_logic.EMPTY and board[row][column] != puzzle[row][column]:
                return jsonify({'error': 'Prefilled cells cannot be changed'}), 400

    for row in range(sudoku_logic.SIZE):
        for column in range(sudoku_logic.SIZE):
            cell = (row, column)
            if (
                puzzle[row][column] == sudoku_logic.EMPTY
                and board[row][column] == sudoku_logic.EMPTY
                and cell not in game['hinted_cells']
            ):
                game['hinted_cells'].add(cell)
                game['hint_count'] += 1
                return jsonify({
                    'row': row,
                    'column': column,
                    'value': solution[row][column],
                    'hints_used': game['hint_count'],
                })

    return jsonify({'hint': None, 'hints_used': game['hint_count']})

@app.route('/check', methods=['POST'])
def check_solution():
    data = request.json
    if not isinstance(data, dict):
        return jsonify({'error': 'Invalid board'}), 400

    board = data.get('board')
    game = get_current_game()
    puzzle = game.get('puzzle')
    solution = game.get('solution')
    if solution is None or puzzle is None:
        return jsonify({'error': 'No game in progress'}), 400
    if not is_valid_submitted_board(board):
        return jsonify({'error': 'Invalid board'}), 400

    incorrect = []
    for i in range(sudoku_logic.SIZE):
        for j in range(sudoku_logic.SIZE):
            if puzzle[i][j] != sudoku_logic.EMPTY and board[i][j] != puzzle[i][j]:
                return jsonify({'error': 'Prefilled cells cannot be changed'}), 400
            if board[i][j] != solution[i][j]:
                incorrect.append([i, j])
    return jsonify({'incorrect': incorrect})

if __name__ == '__main__':
    app.run(debug=False)