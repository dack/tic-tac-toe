from flask import Flask
from flask_slack import Slack
from slackclient import SlackClient
import collections

app = Flask(__name__)
slack = Slack(app)
slack_token = "xyz"
command_token = "xyz" 
sc = SlackClient(slack_token)

app.add_url_rule('/ttt', view_func=slack.dispatch)
TEAM_ID = 'T300Q9W5R'


# games[channel_id] = {"turn": 1, "player1" : player(...), "player2" : player(...), "board": {1: [...], 2: [...]}}

games = {}
win_cond = ([0, 1, 2], [3, 4, 5], [6, 7, 8], [0, 3, 6], [1, 4, 7], [2, 5, 8], [0, 4, 8], [2, 4, 6])  # different combos to win on a 3x3 board

# Users can create a new game in any Slack channel by challenging another user (using their @username).
# A channel can have at most one game being played at a time.
# Anyone in the channel can run a command to display the current board and list whose turn it is.
# Users can specify their next move, which also publicly displays the board in the channel after the move
# with a reminder of whose turn it is.
# Only the user whose turn it is can make the next move.
# When a turn is taken that ends the game, the response indicates this along with who won.

# Tic Tac Toe
# [0, 1, 2,
#  3, 4, 5,
#  6, 7, 8]
# Player 1 is 'X', Player 2 is 'O'


@slack.command('ttt', token=command_token, team_id=TEAM_ID, methods=['POST'])
def tic_tac_toe(**kwargs):
    """
    endpoint for slack command "/ttt"
    :param kwargs: dict with the following keys:
    'user_id', 'response_url', 'text', 'token', 'channel_id',
    'team_id', 'command', 'team_domain', 'user_name', 'channel_name'
    :return: a slack response
    """
    channel_id = kwargs.get('channel_id')
    # creating new game
    if games is None or games.get(channel_id) is None:
        p2_id = ""
        p1_id = kwargs.get('user_id')
        p1_name = kwargs.get('user_name')
        opponent = kwargs.get('text').find('@')
        # no opponent for new game :(
        if opponent == -1:
            return slack.response("No opponent has been chosen.", response_type='in_channel')
        # there's a semblance of a username!
        else:
            p2_name = kwargs.get('text')[opponent+1:].strip()
            users_list = sc.api_call("users.list").get("members")
            print users_list
            # check members within channel
            channel_users_list = sc.api_call("channels.info", channel=channel_id).get('channel').get('members')
            print channel_users_list
            # find opponent in list of members
            for m in users_list:
                if p2_name == m["name"]:
                    p2_id = m['id']
                    if p2_id not in channel_users_list:
                        p2_id = ""
            # not found
            if p2_id == "":
                return slack.response("Invalid opponent. Please try again.", response_type='in_channel')
            # they're here!!!! let's GAME
            else:
                set_players(channel_id, p1_id, p1_name, p2_id, p2_name)
                return slack.response("You've challenged %s. %s" % (p2_name, show_instructions(channel_id)),
                                      response_type='in_channel')
    # game is in progress
    elif games.get(channel_id) is not None:
        # get rid of any whitespace
        req = kwargs.get('text')[kwargs.get('text').find(' ') + 1:].strip().lower()
        # show board
        if req == "board":
            board_and_turn = show_board(channel_id) + "\nIt's %s's turn." % whose_turn(channel_id, "name")
            return slack.response(board_and_turn, response_type='in_channel')
        # show info
        elif req == "info":
            return slack.response(show_instructions(channel_id), response_type='in_channel')
        # check if whomever is trying to play is supposed to
        elif kwargs.get('user_id') == whose_turn(channel_id, "id"):
            square_num = kwargs.get('text')[kwargs.get('text').find(' ') + 1:].strip()
            res = play(channel_id, whose_turn(channel_id, "num"), square_num)
            return slack.response(res, response_type='in_channel')
        # yell at them
        else:
            return slack.response("Game's started. Wait your turn.", response_type='in_channel')
    # somethings not right!!!!
    else:
        return slack.response("That's an invalid command.", response_type='in_channel')


def set_players(channel, p1_id, p1_name, p2_id, p2_name):
    """
    Creates a new game for the channel
    :param channel: channel id that game is played
    :param p1_id: id of player 1
    :param p1_name: name of player 1
    :param p2_id: id of player 2
    :param p2_name: name of player 2
    """
    global games
    player = collections.namedtuple('Player', 'id name')
    player1 = player(p1_id, p1_name)
    player2 = player(p2_id, p2_name)
    games[channel] = {"turn": 1, "player1": player1, "player2": player2, "board": {1: [], 2: []}}


def play(channel, player, pos):
    """
    Checks if play is valid and adds to board for player,
    else return: an error message
    :param channel: channel id for current game
    :param player: player that is trying to move (1 or 2)
    :param pos: the position on the board
    """
    try:
        player = int(player)
        pos = int(pos)
    except ValueError:
        return "That's not a number."
    if pos > 8 or pos < 0:
        return "That's an invalid play. Try again."
    elif pos in games[channel]['board'][1] or pos in games[channel]['board'][2]:
        return "That's been done already. Try again."
    else:
        games[channel]['board'][player].append(pos)
        next_turn(channel)
        if has_winner(channel) != -1:
            text = show_board(channel) + "\n%s is a winner!! Game over." % has_winner(channel)
            reset_game(channel)
            return text
        else:
            return show_board(channel) + "\nIt's %s's turn." % whose_turn(channel, "name")


def whose_turn(channel, info):
    """
    Gets info on the person whose turn it is
    :param channel: channel id for current game
    :param info: type of info request
    :return:
        num => returns player number
        name => returns player name
        id => returns player id
    """
    if info == "num":
        return games[channel]['turn']
    if info == "name":
        if games[channel]['turn'] == 1:
            return games[channel]['player1'].name
        elif games[channel]['turn'] == 2:
            return games[channel]['player2'].name
    if info == "id":
        if games[channel]['turn'] == 1:
            return games[channel]['player1'].id
        elif games[channel]['turn'] == 2:
            return games[channel]['player2'].id


def next_turn(channel):
    """
    Switches turn from 1 to 2 or vice versa
    :param channel: channel id for current game
    """
    if games[channel]['turn'] == 1:
        games[channel]['turn'] = 2
    elif games[channel]['turn'] == 2:
        games[channel]['turn'] = 1


def show_board(channel):
    """
    Gets current state of board for display
    :param channel: channel id for current game
    :return: string representation of board
    """
    board_rep = []
    output = "```"
    for i in range(9):
        if i in games[channel]['board'][1]:
            board_rep.append('X')
        elif i in games[channel]['board'][2]:
            board_rep.append('O')
        else:
            board_rep.append(' ')
    for i in range(9):
        if i % 3 == 0 and i > 0:
            output += "|\n|---+---+---|\n"
        output += "| " + board_rep[i] + " "
    output += "|```"
    return output


def has_winner(channel):
    """
    Checks if there's a winner
    :param channel: channel id for current game
    :return:
        if there's a winner => name of winner
        if there's a tie => "No one"
        if no winner => -1
    """
    if sorted(games[channel]['board'][1]) in win_cond:
        return games[channel]['player1'].name
    elif sorted(games[channel]['board'][2]) in win_cond:
        return games[channel]['player2'].name
    elif len(games[channel]['board'][1]) + len(games[channel]['board'][2]) >= 9:
        return "No one"
    else:
        return -1


def show_instructions(channel):
    """
    Gets instructions for commands and board layout
    :param channel: channel id for current game
    :return: string representation of instructions
    """
    output = "To play, tell me which square # you'd like to take.\n " \
             "%s is 'X', %s is 'O'.\n" \
             "'/ttt board' to view the current board\n" \
             "'/ttt info' to view the instructions\n```" % \
             (games[channel]['player1'].name, games[channel]['player2'].name)
    for i in range(9):
        if i % 3 == 0 and i > 0:
            output += "|\n|---+---+---|\n"
        output += "| " + str(i) + " "
    output += "|```"
    return output


def reset_game(channel):
    """
    Removes game belonging to the channel from the dict
    :param channel: channel id for game to be removed
    """
    global games
    del games[channel]


if __name__ == '__main__':
    app.run()
