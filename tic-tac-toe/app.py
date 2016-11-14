from flask import Flask, request, session
from flask_slack import Slack
from slackclient import SlackClient
import collections
app = Flask(__name__)
slack = Slack(app)
slack_token = 'KjL3USguGA6pbPgvbVyWMPhj'
sc = SlackClient(slack_token)

app.add_url_rule('/ttt', view_func=slack.dispatch)
TEAM_ID = 'T300Q9W5R'

# Users can create a new game in any Slack channel by challenging another user (using their @username).
# A channel can have at most one game being played at a time.
# Anyone in the channel can run a command to display the current board and list whose turn it is.
# Users can specify their next move, which also publicly displays the board in the channel after the move
# with a reminder of whose turn it is.
# Only the user whose turn it is can make the next move.
# When a turn is taken that ends the game, the response indicates this along with who won.


# [0, 1, 2,
#  3, 4, 5,
#  6, 7, 8]
# Player 1 is 'X', Player 2 is 'O'




        # self.win_cond = ([0, 1, 2], [3, 4, 5], [6, 7, 8], [0, 3, 6], [1, 4, 7], [2, 5, 8], [0, 4, 8], [2, 4, 6])
        # self.board = {1: [], 2: []}
        # self.Player = collections.namedtuple('Player', 'id name')
        # self.player1 = self.Player()
        # self.player2 = self.Player()

def set_players(self, p1_id, p1_name, p2_id, p2_name):
    self.player1 = self.Player(id=p1_id, name=p1_name)
    self.player2 = self.Player(id=p2_id, name=p2_name)

def play(self, player, pos):
    if player != session['turn']:
        return "It's not your turn."
    elif not isinstance(pos, int):
        return "That's an invalid command."
    elif pos > 8:
        return "That's an invalid play."
    elif pos in self.board[1] or pos in self.board[2]:
        return "That's been done already."
    else:
        self.board[player].append(pos)
        self.next_turn()
        if self.has_winner() != -1:
            return self.show_board() + "\n%s is a winner!!" % self.has_winner()
        else:
            return self.show_board() + "\nIt's %s's turn." % self.whose_turn()

def whose_turn(self):
    if session['turn'] == 1:
        return self.player1.name
    elif session['turn'] == 2:
        return self.player2.name

def next_turn(self):
    if session['turn'] == 1:
        session['turn'] = 2
    elif session['turn'] == 2:
        session['turn'] = 1

def show_board(self):
    board_rep = []
    output = "```"
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
    output += "|```"
    return output

def has_winner(self):
    if sorted(self.board[1]) in self.win_cond:
        session['game'] = False
        return self.player1.name
    elif sorted(self.board[2]) in self.win_cond:
        session['game'] = False
        return self.player2.name
    else:
        return -1

def show_instructions(self):
    output = "To play, tell me which square # you'd like to take. \n```"
    for i in range(9):
        if i % 3 == 0 and i > 0:
            output += "|\n|---+---+---|\n"
        output += "| " + i + " "
    output += "|```"
    return output


@slack.command('ttt', token=slack_token, team_id=TEAM_ID, methods=['POST'])
def tic_tac_toe(**kwargs):
    session['game'] = False
    session['turn'] = 1
    #ttt = TicTacToe()
    # start a new game of tic tac toe
    if not session['game']:
        print request.form.get('user_id')
        p2_id = ""
        p1_id = request.form.get('user_id')
        p1_name = request.form.get('user_name')
        opponent = request.form.get('text').find('@')
        if opponent == -1:
            return slack.response("No opponent has been chosen.", response_type='in_channel')
        else:
            p2_name = request.args.text[opponent+1:].strip()
            users_list = sc.api_call("users.list")
            members = users_list["members"]
            for m in members:
                if p2_name == m["name"]:
                    p2_id = m['id']
            if p2_id == "":
                return slack.response("Invalid opponent. Please try again.", response_type='in_channel')
            else:
                #ttt.set_players(p1_id, p1_name, p2_id, p2_name)
                session['game'] = True
                return show_instructions()
    # play a move
    elif request.args.user_id == "":
        play = request.args.text[request.args.text.find(' ')+1:].strip()
        return slack.response(play(request.args.user_id, play), response_type='in_channel')
    # somethings not right
    else:
        return slack.response("That's an invalid command.", response_type='in_channel')


if __name__ == '__main__':
    app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'
    app.run()
