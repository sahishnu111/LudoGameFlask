import os
import random
import json
from flask import Flask, render_template, request, session, jsonify
from flask_cors import CORS
import flask_session
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

CORS(app)  # Initialize CORS after creating the Flask app object
app.secret_key = 'your_secret_key'

# Database Configuration (use a relative path)
basedir = os.path.abspath(os.path.dirname(__file__))  # Get project directory
db_path = os.path.join(basedir, 'ludo_game.db')  # Path to database file
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
db = SQLAlchemy(app)

num_players = 0


class GameSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    game_state = db.Column(db.String(5000))
    current_player = db.Column(db.Integer)


class Player:
    def __init__(self, player_id, player_name, player_color, player_pieces=None, player_home=None,
                 player_place_count_pieces=None, player_pieces_set=None, player_pieces_count=None,
                 player_pieces_at_home=None, player_pieces_almost_home=None, at_safe_positions=None):
        self.player_id = player_id
        self.player_name = player_name
        self.player_color = player_color
        self.player_pieces = player_pieces if player_pieces is not None else [[0, 0] for _ in range(4)]
        self.player_home = player_home if player_home is not None else 0
        self.player_place_count_pieces = player_place_count_pieces if player_place_count_pieces is not None else [0] * 4
        self.player_pieces_set = player_pieces_set if player_pieces_set is not None else [False] * 4
        self.player_pieces_count = player_pieces_count if player_pieces_count is not None else 0
        self.player_pieces_at_home = player_pieces_at_home if player_pieces_at_home is not None else [False] * 4
        self.player_pieces_almost_home = player_pieces_almost_home if player_pieces_almost_home is not None else [
                                                                                                                     False] * 4
        self.at_safe_positions = at_safe_positions if at_safe_positions is not None else [False] * 4


class Board:
    def __init__(self):
        self.quadrant_ranges = {
            1: (6, 0, 8, 5),
            2: (0, 6, 5, 8),
            3: (6, 9, 8, 14),
            4: (9, 5, 14, 8),
        }

    def get_quadrant(self, player_row, player_col):
        for quadrant, (start_row, start_col, end_row, end_col) in self.quadrant_ranges.items():
            if start_row <= player_row <= end_row and start_col <= player_col <= end_col:
                return quadrant
        return -1


class Game:
    def __init__(self):
        self.board = Board()
        self.players = []
        self.colors = ["Red", "Green", "Blue", "Yellow"]
        self.safe_spots = [(6, 1), (8, 3), (2, 6), (1, 8), (6, 12), (8, 13), (12, 8), (13, 6)]
        self.players_at_home_pushed = [False] * 4
        self.winner = []

    @classmethod
    def from_json(cls, json_str):
        game_data = json.loads(json_str)
        game = cls()
        game.board = Board()
        game.players = []

        for player_data in game_data.get('players', []):
            player = Player(
                player_id=player_data.get('player_id'),
                player_name=player_data.get('player_name'),
                player_color=player_data.get('player_color'),
                player_pieces=player_data.get('player_pieces'),
                player_home=player_data.get('player_home'),
                player_place_count_pieces=player_data.get('player_place_count_pieces'),
                player_pieces_set=player_data.get('player_pieces_set'),
                player_pieces_count=player_data.get('player_pieces_count'),
                player_pieces_at_home=player_data.get('player_pieces_at_home'),
                player_pieces_almost_home=player_data.get('player_pieces_almost_home'),
                at_safe_positions=player_data.get('at_safe_positions')
            )
            game.players.append(player)
        return game

    def add_player(self, player):
        self.players.append(player)

    def is_playable(self):
        return 2 <= len(self.players) <= 4

    def roll_dice(self):
        return random.randint(1, 6)

    def NullPosition(self, player_id):
        for i in range(4):
            self.players[player_id].player_pieces[i] = [0, 0]

    def update_starting_positions(self, number_of_players):
        starting_positions = {
            2: ([6, 1], [1, 8]),
            3: ([6, 1], [1, 8], [8, 13]),
            4: ([6, 1], [1, 8], [8, 13], [13, 6])
        }
        if number_of_players in starting_positions:
            for i in range(number_of_players):
                self.players[i].player_pieces = [starting_positions[number_of_players][i] for _ in range(4)]
        else:
            print("Invalid number of players")

    def quadrant_moves(self, player_row, player_col, roll, player_id, quadrant, wanna_move_piece):
        if quadrant == 1:
            self.quad1(player_row, player_col, roll, player_id, wanna_move_piece)
        elif quadrant == 2:
            self.quad2(player_row, player_col, roll, player_id, wanna_move_piece)
        elif quadrant == 3:
            self.quad3(player_row, player_col, roll, player_id, wanna_move_piece)
        elif quadrant == 4:
            self.quad4(player_row, player_col, roll, player_id, wanna_move_piece)
        else:
            print("Invalid Quadrant")

    def quad1(self, player_row, player_col, roll, player_id, wanna_move_piece):
        if player_col == 0:
            if player_row == 6 and roll == 6:
                self.players[player_id].player_pieces[wanna_move_piece] = (5, 6)
            else:
                if roll == 1:
                    if player_row == 6:
                        self.players[player_id].player_pieces[wanna_move_piece] = (6, 1)
                    else:
                        self.players[player_id].player_pieces[wanna_move_piece] = (player_row + roll, player_col)
                else:
                    new_roll = roll - (player_row - 6)
                    self.players[player_id].player_pieces[wanna_move_piece] = (6, new_roll)
        elif player_row == 8:
            new_roll = roll - player_col
            if new_roll < 3:
                self.players[player_id].player_pieces[wanna_move_piece] = (player_row - new_roll, player_col)
            else:
                new_roll1 = new_roll - (player_row - 6)
                self.players[player_id].player_pieces[wanna_move_piece] = (player_row, player_col + new_roll1)
        else:
            if player_col + roll >= 6:
                new_roll = roll - (5 - player_col) - 1
                if new_roll > 0:
                    self.players[player_id].player_pieces[wanna_move_piece] = (5 - new_roll, 6)
                else:
                    self.players[player_id].player_pieces[wanna_move_piece] = (5, 6)
            else:
                self.players[player_id].player_pieces[wanna_move_piece] = (player_row, player_col + roll)

    def quad3(self, player_row, player_col, roll, player_id, wanna_move_piece):
        if player_col == 14:  # Special case: Piece on the rightmost column
            if player_row == 8 and roll == 6:
                self.players[player_id].player_pieces[wanna_move_piece] = (9, 8)
            else:
                if roll == 1:
                    if player_row == 8:
                        self.players[player_id].player_pieces[wanna_move_piece] = (7, 14)  # Move up
                    else:
                        self.players[player_id].player_pieces[wanna_move_piece] = (player_row + roll, player_col)
                else:
                    new_roll = roll - (8 - player_row)  # Adjust roll for upward movement
                    self.players[player_id].player_pieces[wanna_move_piece] = (8, 14 - new_roll)  # Move leftward

        elif player_row == 8:  # Special case: Piece on the top row
            if player_col - roll <= 8:  # Reached or passed the corner
                new_roll = roll - (player_col - 9)  # Adjust roll for corner movement
                if new_roll > 0:
                    new_roll -= 1
                    if new_roll > 0:
                        self.players[player_id].player_pieces[wanna_move_piece] = (9 + new_roll, 8)
                    else:
                        self.players[player_id].player_pieces[wanna_move_piece] = (9, 8)
                else:
                    self.players[player_id].player_pieces[wanna_move_piece] = (8, 9)
            else:
                self.players[player_id].player_pieces[wanna_move_piece] = (player_row, player_col - roll)

        else:  # General case: Piece on the board
            if player_col - roll <= 8:  # Reached or passed the corner
                new_roll = roll - (player_col - 8)  # Adjust roll for corner movement
                if new_roll > 2:
                    new_roll -= 2
                    self.players[player_id].player_pieces[wanna_move_piece] = (8, 14 - new_roll)
                else:
                    self.players[player_id].player_pieces[wanna_move_piece] = (
                        6 + new_roll, 14)  # Move up or turn corner
            else:
                self.players[player_id].player_pieces[wanna_move_piece] = (player_row, player_col - roll)  # Move left

    def quad2(self, player_row, player_col, roll, player_id, wanna_move_piece):
        if player_row == 0:  # Special case: Piece is on the bottom row
            if player_col == 8 and roll == 6:
                self.players[player_id].player_pieces[wanna_move_piece] = (6, 9)
            else:
                if roll == 1:
                    if player_col == 8:
                        self.players[player_id].player_pieces[wanna_move_piece] = (1, 8)
                    else:
                        self.players[player_id].player_pieces[wanna_move_piece] = (player_row, player_col + roll)
                else:
                    new_roll = roll - (8 - player_col)
                    self.players[player_id].player_pieces[wanna_move_piece] = (new_roll, 8)

        elif player_col == 6:  # Special case: Piece is on the middle column
            if player_row - roll < 0:  # Check if move goes beyond the starting corner
                new_roll = roll - player_row
                if new_roll < 3:
                    self.players[player_id].player_pieces[wanna_move_piece] = (0, 6 + new_roll)
                else:
                    new_roll -= 2
                    self.players[player_id].player_pieces[wanna_move_piece] = (new_roll, 8)
            else:
                self.players[player_id].player_pieces[wanna_move_piece] = (player_row - roll, player_col)

        else:  # General case: Piece on the main board
            if player_row + roll >= 6:
                new_roll = roll - (5 - player_row) - 1
                if new_roll >= 0:  # Check if move goes into home column
                    self.players[player_id].player_pieces[wanna_move_piece] = (6, 9 + new_roll)
                else:  # Move normally if not entering home column
                    self.players[player_id].player_pieces[wanna_move_piece] = (player_row + roll, player_col)
            else:
                self.players[player_id].player_pieces[wanna_move_piece] = (
                    player_row + roll, player_col)  # Move up normally

    def quad4(self, player_row, player_col, roll, player_id, wanna_move_piece):
        if player_row == 14:  # Special case: Piece is on the bottom row
            if player_col == 6 and roll == 6:
                self.players[player_id].player_pieces[wanna_move_piece] = (8, 5)  # Move to home entrance
            else:
                if roll == 1:
                    if player_col == 6:
                        self.players[player_id].player_pieces[wanna_move_piece] = (13, 6)  # Move up
                    else:
                        self.players[player_id].player_pieces[wanna_move_piece] = (
                            player_row, player_col - roll)  # Move left
                else:
                    new_roll = roll - (player_col - 6)
                    self.players[player_id].player_pieces[wanna_move_piece] = (14 - new_roll, 6)  # Move up

        elif player_col == 6:  # Special case: Piece is on the middle column
            if player_row - roll < 9:  # Check if move goes beyond the starting corner
                new_roll = roll - (player_row - 9) - 1  # Adjusted roll for the corner and into home column
                if new_roll > 0:  # Check if moving into home column
                    self.players[player_id].player_pieces[wanna_move_piece] = (8, 5 - new_roll)
                else:  # Stopping at the home entrance
                    self.players[player_id].player_pieces[wanna_move_piece] = (8, 5)
            else:
                self.players[player_id].player_pieces[wanna_move_piece] = (player_row - roll, player_col)

        else:  # General case: Piece on the main board
            if player_row + roll > 14:  # Check if move goes beyond the bottom row
                new_roll = roll - (14 - player_row)  # Adjusted roll
                if new_roll < 3:
                    self.players[player_id].player_pieces[wanna_move_piece] = (14, 8 - new_roll)
                else:
                    new_roll -= 2
                    self.players[player_id].player_pieces[wanna_move_piece] = (14 - new_roll, 6)
            else:
                self.players[player_id].player_pieces[wanna_move_piece] = (player_row + roll, player_col)  # Move down

    def get_player_pieces(self, player_id):
        return [
            self.players[player_id].player_pieces[i]
            for i in range(4)
            if self.players[player_id].player_pieces_set[i]
        ]

    def player_attack(self, moved_piece, player_id):
        for i in range(len(self.players)):
            if i != player_id:
                for j in range(4):
                    if self.players[i].player_pieces[j] == self.players[player_id].player_pieces[moved_piece] and \
                            self.players[i].player_pieces[j] not in self.safe_spots:
                        if self.stack_pieces(i):
                            return False
                        print(f"Player {player_id + 1} piece {moved_piece} attacked Player {i + 1} piece {j}")
                        self.players[i].player_pieces[j] = [0, 0]
                        self.players[i].player_pieces_set[j] = False
                        self.players[i].player_pieces_count -= 1
                        return True
        return False

    def stack_pieces(self, player_id):
        for i in range(4):
            for j in range(i + 1, 4):
                if self.players[player_id].player_pieces_set[i] and self.players[player_id].player_pieces_set[j] and \
                        self.players[player_id].player_pieces[i] == self.players[player_id].player_pieces[j]:
                    self.players[player_id].at_safe_positions[i] = True
                    self.players[player_id].at_safe_positions[j] = True
                    print(
                        f"Player {player_id + 1} has two pieces stacked at ({self.players[player_id].player_pieces[i][0]}, {self.players[player_id].player_pieces[i][1]}).")
                    return True
        return False

    def stack_pieces_quad(self, player_id, wanna_move_piece):
        for j in range(4):
            if j != wanna_move_piece and self.players[player_id].player_pieces_set[j] and \
                    self.players[player_id].player_pieces[wanna_move_piece] == \
                    self.players[player_id].player_pieces[j]:
                self.players[player_id].at_safe_positions[wanna_move_piece] = True
                self.players[player_id].at_safe_positions[j] = True
                print(
                    f"Player {player_id + 1} has two pieces stacked at ({self.players[player_id].player_pieces[wanna_move_piece][0]}, {self.players[player_id].player_pieces[wanna_move_piece][1]}).")
                return True
        return False

    def stack_pieces_move(self, player_id, piece_index):
        for j in range(4):
            if j != piece_index and self.players[player_id].player_pieces_set[j] and \
                    self.players[player_id].player_pieces[piece_index] == \
                    self.players[player_id].player_pieces[j]:
                print(
                    f"Player {player_id + 1} has two pieces stacked at ({self.players[player_id].player_pieces[piece_index][0]}, {self.players[player_id].player_pieces[piece_index][1]}).")
                return j
        return -1

    def can_use_roll(self, player_id, roll):
        # Check if ANY of the player's pieces can legally use the roll
        for piece in self.get_player_pieces(player_id):
            if self.is_valid_move(piece, roll):
                return True
        return False

    def position_check(self, player_id, wanna_move_piece):
        player_row = self.players[player_id].player_pieces[wanna_move_piece][0]
        player_col = self.players[player_id].player_pieces[wanna_move_piece][1]
        print(f"UPDATED POSITION OF PLAYER {player_id + 1} PIECE {wanna_move_piece}\n")
        print(f"\tROW:{player_row}\tCOL:{player_col}")
        print("\n\n")

    def player_turn(self, player_id):
        while True:
            roll = self.roll_dice()
            if self.players[player_id].player_home < 4:
                print(f"Player {player_id + 1}: {self.players[player_id].player_name} rolled a {roll}")
                if self.players[player_id].player_pieces_count == 0:
                    if roll == 6:
                        self.take_piece_out(player_id)
                else:
                    self.choose_piece_to_move(player_id, roll)
            if roll != 6:
                break

    def computer_turn(self, player_id):
        while True:
            roll = self.roll_dice()
            if self.players[player_id].player_home < 4:
                print(f"Computer Player {player_id + 1}: {self.players[player_id].player_name} rolled a {roll}")
                if self.players[player_id].player_pieces_count == 0:
                    if roll == 6:
                        self.take_piece_out(player_id)
                else:
                    self.auto_choose_piece(player_id, roll)  # Automatically choose a piece for the computer
            if roll != 6:
                break

    def auto_choose_piece(self, player_id, roll):
        for i in range(4):
            if self.players[player_id].player_pieces_set[i]:
                player_row = self.players[player_id].player_pieces[i][0]
                player_col = self.players[player_id].player_pieces[i][1]
                quadrant = self.board.get_quadrant(player_row, player_col)

                if self.players[player_id].player_pieces_almost_home[i]:
                    self.move_piece(player_id, i, roll)
                    return

                if self.players[player_id].player_place_count_pieces[i] > 0:
                    self.move_piece(player_id, i, roll)
                    return

                if self.stack_pieces_quad(player_id, i):
                    x = self.stack_pieces_move(player_id, i)
                    roll //= 2
                    self.quadrant_moves(player_row, player_col, roll, player_id, quadrant, i)
                    self.quadrant_moves(player_row, player_col, roll, player_id, quadrant, x)
                    self.position_check(player_id, i)
                    return

                self.quadrant_moves(player_row, player_col, roll, player_id, quadrant, i)
                self.position_check(player_id, i)

                if self.player_attack(i, player_id):
                    print("Player Attack successfully")

                self.update_place_count(player_id, i, quadrant)
                return

    def choose_piece_to_move(self, player_id, roll, move_piece):

        while True:
            try:
                wanna_move_piece = int(move_piece)
                if -1 <= wanna_move_piece <= 3:
                    if wanna_move_piece == 0 and roll == 6 and not self.players[player_id].player_pieces_set[0]:
                        self.take_piece_out(player_id)
                        break
                    elif 0 <= wanna_move_piece <= 3 and self.players[player_id].player_pieces_set[wanna_move_piece]:
                        self.move_piece(player_id, wanna_move_piece, roll)
                        break
                    else:
                        print("Invalid input. Please enter a valid piece number.")
                        break
                else:
                    print("Invalid input. Please enter a number between -1 and 3.")
            except ValueError:
                print("Invalid input. Please enter a number.")

    def move_piece(self, player_id, piece_index, roll):
        player_row = self.players[player_id].player_pieces[piece_index][0]
        player_col = self.players[player_id].player_pieces[piece_index][1]
        quadrant = self.board.get_quadrant(player_row, player_col)

        if self.players[player_id].player_pieces_almost_home[piece_index]:
            self.move_almost_home(player_id, piece_index, roll)
        elif self.players[player_id].player_place_count_pieces[piece_index] > 0:
            self.move_in_home_path(player_id, piece_index, roll)
        else:
            if self.stack_pieces_quad(player_id, piece_index):
                stacked_piece_index = self.stack_pieces_move(player_id, piece_index)
                roll //= 2
                self.quadrant_moves(player_row, player_col, roll, player_id, quadrant, piece_index)
                self.quadrant_moves(player_row, player_col, roll, player_id, quadrant, stacked_piece_index)
            else:
                self.quadrant_moves(player_row, player_col, roll, player_id, quadrant, piece_index)

        self.position_check(player_id, piece_index)
        if self.player_attack(piece_index, player_id):
            print("Player Attack successful!")

        self.update_place_count(player_id, piece_index, quadrant)

    def move_almost_home(self, player_id, piece_index, roll):
        if player_id == 0:
            if self.players[player_id].player_pieces[piece_index][1] + roll <= 6:
                self.players[player_id].player_pieces[piece_index][1] += roll
                if self.players[player_id].player_pieces[piece_index][1] == 6:
                    print("\n\n")
                    print(f"Player {player_id + 1} piece {piece_index} entered home!")
                    print("\n\n")
                    self.players[player_id].player_home += 1
                    self.players[player_id].player_pieces_at_home[piece_index] = True
            else:
                print(f"Player {player_id + 1} piece {piece_index} cannot move home with this roll.")
        elif player_id == 1:
            if self.players[player_id].player_pieces[piece_index][0] + roll <= 6:
                self.players[player_id].player_pieces[piece_index][0] += roll
                if self.players[player_id].player_pieces[piece_index][0] == 6:
                    print("\n\n")
                    print(f"Player {player_id + 1} piece {piece_index} entered home!")
                    print("\n\n")
                    self.players[player_id].player_home += 1
                    self.players[player_id].player_pieces_at_home[piece_index] = True
            else:
                print(f"Player {player_id + 1} piece {piece_index} cannot move home with this roll.")

        # Similar logic for player_id 2 and 3...

    def move_in_home_path(self, player_id, piece_index, roll):
        # Similar logic to move_almost_home, but for moving within the home path...
        pass  # Implement the logic here

    def take_piece_out(self, player_id):
        for i in range(4):
            if not self.players[player_id].player_pieces_set[i]:
                self.players[player_id].player_pieces_set[i] = True
                self.players[player_id].player_pieces[i] = self.get_starting_position(player_id)
                self.players[player_id].player_pieces_count += 1
                print(f"Player {player_id + 1} took out piece {i}.")
                break

    def update_place_count(self, player_id, piece_index, quadrant):
        if player_id == 0 and quadrant == 1 and self.players[player_id].player_pieces[piece_index][
            0] == 8:
            self.players[player_id].player_place_count_pieces[piece_index] += 1
        # Similar logic for other player_ids and their corresponding quadrants...
        if player_id == 1 and quadrant == 2 and self.players[player_id].player_pieces[piece_index][
            1] == 6:
            self.players[player_id].player_place_count_pieces[piece_index] += 1
        if player_id == 2 and quadrant == 3 and self.players[player_id].player_pieces[piece_index][
            0] == 6:
            self.players[player_id].player_place_count_pieces[piece_index] += 1
        if player_id == 3 and quadrant == 4 and self.players[player_id].player_pieces[piece_index][
            1] == 8:
            self.players[player_id].player_place_count_pieces[piece_index] += 1

    def get_starting_position(self, player_id):
        starting_positions = {
            0: [6, 1],
            1: [1, 8],
            2: [8, 13],
            3: [13, 6]
        }
        return starting_positions[player_id]

    def print_piece_status(self, player_id):
        print("PLAYER pieces out of starting position:\t", end="")
        for i in range(4):
            print(f"{i} ({'True' if self.players[player_id].player_pieces_set[i] else 'False'})\t", end="")
        print()
        print(f"Player {player_id + 1}: {self.players[player_id].player_name} place count pieces: ", end="")
        for i in range(4):
            print(self.players[player_id].player_place_count_pieces[i], end=" ")
        print()

    def winner_check(self):
        for i in range(len(self.winner)):
            print(f"{i + 1} WINNER: {self.players[self.winner[i]].player_name}")

    def initialize_players(self, number_of_players):
        for i in range(number_of_players):
            # In a real game, you would get player names from user input
            name = f"Player {i + 1}"
            color = self.colors[i]
            player = Player(i, name, color)
            self.add_player(player)

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__, indent=4)


# Create the database tables (only needed once)
with app.app_context():
    db.create_all()


@app.route('/')
def home():
    return render_template('index.html'), 200


@app.route('/game.html')
def game():
    return render_template('game.html'), 200


@app.route('/start_game', methods=['POST'])
def start_game():
    global num_players
    try:
        data = request.get_json()
        num_players = int(data.get('numPlayers'))
        game = Game()
        game.initialize_players(num_players)

        game_session = GameSession(game_state=game.to_json(), current_player=0)
        db.session.add(game_session)
        db.session.commit()
        session['game_id'] = game_session.id

        # Ensure game_id is an integer before storing and returning
        if not isinstance(game_session.id, int):
            return jsonify({'error': 'Invalid game ID type'}), 500

        session['game_id'] = game_session.id
        return jsonify({'message': 'Game started successfully!', 'game_id': game_session.id}), 200
    except Exception as e:
        print("Error in start_game:", e)
        return jsonify({'error': f"An unexpected error occurred: {str(e)}"}), 500


@app.route('/game_players/<int:game_id>', methods=['GET'])
def get_game_players(game_id):
    game_session = GameSession.query.get(game_id)
    if game_session is not None:
        game = Game.from_json(game_session.game_state)
        players = [
            {'name': player.player_name, 'color': player.player_color, "player_piece": player.player_pieces,
             "id": player.player_id}
            for player in game.players
        ]  # Include player_id here

        # Use session to store the game_id
        session["game_id"] = game_id
        print(session["game_id"])
        return jsonify({'game_id': game_id, 'players': players}), 200
    else:
        return jsonify({'error': 'Game not found!'}), 404


@app.route('/playing_game', methods=['POST'])
def playing_game():
    try:
        data = request.get_json()
        player_id = int(data.get('player_id'))
        if player_id is None or not isinstance(player_id, int):
            return jsonify({'error': 'Missing or invalid player_id'}), 400

        player_rolls = data.get('player_roll')
        if not isinstance(player_rolls, list) or not all(isinstance(roll, int) for roll in player_rolls):
            return jsonify({'error': 'Invalid player_roll'}), 400

        player_move = int(data.get('player_move'))
        if player_move is None or not isinstance(player_move, int):
            return jsonify({'error': 'Missing or invalid player_move'}), 400
        game_id = data.get('game_id')

        game_session = GameSession.query.get(game_id)
        if game_session is not None:
            game = Game.from_json(game_session.game_state)

            # --- Key Improvement: Loop for Multiple Rolls ---
            for roll in player_rolls:
                # If your game logic needs it, you can check if the player can use all the rolls.

                game.choose_piece_to_move(player_id, roll, player_move)

            # --- End Improvement ---

            game_session.game_state = game.to_json()
            db.session.commit()

            return jsonify({'message': 'Move made successfully!'}), 200
        else:
            return jsonify({'error': 'Game not found!'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 400


if __name__ == '__main__':
    app.run(debug=True)
