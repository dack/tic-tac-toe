from flask import Flask, request
from flask_slack import Slack
from slackclient import SlackClient
import collections
app = Flask(__name__)
slack = Slack(app)
slack_token = 'xoxp-102024336195-102778488359-103271606435-c95705887f81b9ac9bd4834ec3730936'
sc = SlackClient(slack_token)

app.add_url_rule('/', view_func=slack.dispatch)
TEAM_ID = 'T300Q9W5R'

# Users can create a new game in any Slack channel by challenging another user (using their @username).
# A channel can have at most one game being played at a time.
# Anyone in the channel can run a command to display the current board and list whose turn it is.
# Users can specify their next move, which also publicly displays the board in the channel after the move
# with a reminder of whose turn it is.
# Only the user whose turn it is can make the next move.
# When a turn is taken that ends the game, the response indicates this along with who won.

game_in_progress = False

# [0, 1, 2,
#  3, 4, 5,
#  6, 7, 8]
# Player 1 is 'X', Player 2 is 'O'


class TicTacToe(object):
    def __init__(self):
        self.win_cond = ([0, 1, 2], [3, 4, 5], [6, 7, 8], [0, 3, 6], [1, 4, 7], [2, 5, 8], [0, 4, 8], [2, 4, 6])
        self.board = {1: [], 2: []}
        self.turn = 1
        self.Player = collections.namedtuple('Player', 'id name')
        self.player1 = self.Player()
        self.player2 = self.Player()

    def set_players(self, p1_id, p1_name, p2_id, p2_name):
        self.player1 = self.Player(id=p1_id, name=p1_name)
        self.player2 = self.Player(id=p2_id, name=p2_name)

    def play(self, player, pos):
        if player != self.turn:
            return "It's not your turn."
        elif pos > 8:
            return "That's an invalid play."
        elif pos in self.board[1] or pos in self.board[2]:
            return "That's been done already."
        else:
            self.board[player].append(pos)
            self.next_turn()
            if self.has_winner() != -1:
                return self.draw_board() + "\n%s is a winner!!" % self.has_winner()
            else:
                return self.draw_board() + "\nIt's %s's turn." % self.whose_turn()

    def whose_turn(self):
        if self.turn == 1:
            return self.player1.name
        elif self.turn == 2:
            return self.player2.name

    def next_turn(self):
        if self.turn == 1:
            self.turn = 2
        elif self.turn == 2:
            self.turn = 1

    def draw_board(self):
        board_rep = []
        output = ""
        for i in range(9):
            if i in self.board[1]:
                board_rep.append('X')
            elif i in self.board[2]:
                board_rep.append('O')
            else:
                board_rep.append(' ')
        for i in range(9):
            if i % 3 == 0 and i > 0:
                output += "|\n|---+---+---|\n"
            output += "| " + board_rep[i] + " "
        output += "|"
        return output

    def has_winner(self):
        global game_in_progress
        if sorted(self.board[1]) in self.win_cond:
            game_in_progress = False
            return self.player1.name
        elif sorted(self.board[2]) in self.win_cond:
            game_in_progress = False
            return self.player2.name
        else:
            return -1


@slack.command('ttt', token=slack_token, team_id=TEAM_ID, methods=['POST'])
def tic_tac_toe():
    global game_in_progress
    # start a new game of tic tac toe
    if not game_in_progress:
        # response_url = request.args.response_url
        p2_id = ""
        p1_id = request.args.user_id
        p1_name = request.args.user_name
        opponent = request.args.text.find('@')
        if opponent == -1:
            return slack.response("No opponent has been chosen.")
        else:
            p2_name = request.args.text[opponent+1:].strip()
            users_list = sc.api_call("users.list")
            members = users_list["members"]
            for m in members:
                if p2_name == m["name"]:
                    p2_id = m['id']
                    ttt.set_players(p1_id, p1_name, p2_id, p2_name)
                    game_in_progress = True
            if p2_id == "":
                return slack.response("Invalid opponent. Please try again.")
    # play a move
    else:
        return slack.response("That's an invalid command.")


if __name__ == '__main__':
    ttt = TicTacToe()
    app.run()
