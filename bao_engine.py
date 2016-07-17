# file: bao_engine.py
# copyright: Copyright (C) 2016 Kjell Wooding
# license:  MIT. See LICENSE for complete license text

from __future__ import print_function
from random import choice
from math import ceil
from itertools import cycle
from operator import sub
import json


class Pit():
    '''Represent a pit in a mankala (bao) style game.
    We assume locations are a grid overlaying the circular pit,
    so we flag some locations as unusable (the corners) by placing an 'X' there.
    All other locations receive a list of stones'''

    def __init__(self, id=-1, n=4, player=1, n_target_pos=48, target=False):
        '''Create a bao pit.
        There should be an even number of pits.
        Pits should be numbered sequentially.
        Each pit belongs to a particular player (below half = player 1. Above = player 2)
        Each player has one pit called a `target`
        Non-target pits consist of an nxn grid of positions
        Target pits consist of n_target_pos positions.
        '''
        self.id = id
        if target:
            self.cols = n
            self.rows = int(ceil(n_target_pos / float(n)))
        else:
            self.rows = n
            self.cols = n
        self.loc = []
        for j in range(self.rows * self.cols):
            self.loc.append(list())
        self.loc[0] = 'X'
        self.loc[n-1] = 'X'
        self.loc[-1] = 'X'
        self.loc[-n] = 'X'
        self.target = target
        self.player = player

    def __repr__(self):
        return '{}: {} {}'.format(self.id, self.count_stones(), ('(T)' if self.target else ''))

    def pretty_print(self):
        '''pretty-print a pit.
        dots indicate empty locations.
        numbers indicate the number of stones at that position.'''
        s = ''
        for x in range(self.rows):
            for y in range(self.cols):
                p = self.loc[self.cols*x+y]
                if p == "X":
                    s += ' '
                elif len(p) > 0:
                    s += str(len(p))
                else:
                    s += '.'
            s += '\n'
        s +='{}: p{} {}'.format(self.id, self.player, ('(T)' if self.target else ''))
        print(s + '\n')

    def free_locations(self, reuse=False):
        '''return a list of all empty locations in this pit.
        Useful in conjunction with `random.choice()`
        if `reuse == True`, then a list of all non-'X' pits is returned
        '''
        ret = []
        for (i, contents) in enumerate(self.loc):
            if reuse == True and (contents != 'X' or len(contents) == 0):
                ret += [i]
            elif reuse == False and len(contents) == 0:
                ret += [i]
        return ret

    def add(self, stone, debug=False):
        '''Add the supplied stone to this pit.
        Stone should be currently unallocated. Add will fail (return False) if stone is already positioned somewhere '''
        if stone.pit is not None:
            raise RuntimeError, "Tried to add stone to pit {} that is already placed in pit {}".format(self.id, stone.pit)
            return False

        free = self.free_locations()
        if (len(free)):
            loc = choice(free)
        else:
            # no locations free
            free = self.free_locations(reuse=True)
            loc = choice(free)

        stone.position = loc
        stone.pit = self.id
        self.loc[loc].append(stone)
        return True

    def pickup_stones(self, debug=False):
        '''pick-up all stones in this pit (i.e. their location becomes None'''
        for i, stone_l in enumerate(self.loc):
            stones = stone_l[:] # make a copy: we need to mutate the list
            if (stones != 'X') and (len(stones) > 0):
                for stone in stones:
                    if (stone.pit != self.id):
                        raise RuntimeError, 'Stone {} has pit_id {}, but being removed from {}'.format(stone.id, stone.pit, self.id)
                    if debug:
                        print('Removing stone {} from pit {}, loc {}'.format(stone.id, self.id, stone.position))
                    stone.pit = None
                    stone.position = None
                    self.loc[i].remove(stone)

    def count_stones(self, debug=False):
        '''count the number of stones in a pit'''
        c = 0
        for i,stones in enumerate(self.loc):
            if debug:
                print('{}:{} '.format(i,stones),end='')
            if (stones != 'X') and (len(stones) > 0):
                c = c + len(stones)
        if debug:
            print()
        return c


class Stone():
    '''Object representing a stone (marker, or seed) in a game of bao'''
    def __init__(self, color=None, id=-1):
        '''Create a bao stone.
        * A stone has a `pit` (None, or pit id) if it has been placed, and if a pit_id has been assigned,
        it has a `position` in that pit.
        * A stone has an id indicating its position in the stones array
        * A stone has a color (tint). Sometimes we color starting stones by player,
          though it makes no difference to gameplay.'''
        if color == None:
            color = '#6666af'
        self.pit = None
        self.position = None
        self.id = id
        self.color = color

    def __repr__(self):
        return '(id={}, pit={}, pos={}, color={})'.format(self.id, self.pit, self.position, self.color)

class Game():
    def __init__(self, n_stones=36, n_pits=6, n_rows=1):
        '''Create a bao game.
        * `n_pits` is the number of (non-target) pits per player
        * `n_rows` is the rows of pits per player (not currently used)
        * `n_stones` is the number of stones (seeds) that the game starts with'''
        self.game_over = True
        self.n_rows = n_rows
        self.n_pits = n_pits
        self.stones = [Stone(id=i) for i in range(n_stones)]
        self.pits = [Pit(target=(i%(n_pits+1) == n_pits),
                      player=(1 if i <= n_pits else 2),
                      id=i) for i in range(2*n_pits + 2)]
        self.targets = {}

        # State variables for moving, capturing
        self.captures_done = True
        self.last_pit = None

        #self.get_player = self.toggle_player()
        self.get_player = cycle([1,2])
        self.current_player = self.get_player.next()
        # remember player targets
        for p in self.pits:
            if p.target:
                self.targets[p.player] = p.id

    def __repr__(self):
        '''Text representation of the game board'''
        s = '\t\t'
        for i in range(self.n_pits + 1):
            s += str(self.pits[i]) + '\t'
        s += '\n'
        for i in range(2 * self.n_pits + 1, self.n_pits, -1):
            s += str(self.pits[i]) + '\t'
        return s + '\nNext: Player {} \tGame State: {}\t Captures done:{}\t Last_pit: {}\n'.format(self.current_player, 'Game Over' if self.game_over else 'Playing', self.captures_done, self.last_pit)

    @property
    def score(self):
        '''returns a list containing the current score [p1_score, p2_score]'''
        scores = []
        for player in [1,2]:
            scores.append(self.pits[self.targets[player]].count_stones())
        return scores

    @property
    def n_stones(self):
        return len(self.stones)

    def initial_place(self, debug=False, direction='ccw'):
        '''Do the initial placement (sowing) of stones.
        This can only be done if the current game is over.
        Place one in each non-target pit until all stones have been placed.
        * `direction` is currently unused. If game is already initialized,
        do nothing.'''

        if self.game_over == False:
            return

        # pick everything up
        for p in self.pits:
            p.pickup_stones()

        unplaced = (stone for stone in self.stones if stone.pit is None)
        p = 0
        try:
            while True:
                stone = unplaced.next()
                if self.pits[p].target == True:
                    p = (p + 1) % len(self.pits)
                if debug:
                    print('Placing stone {} in pit {}'.format(stone.id, self.pits[p].id))
                self.pits[p].add(stone)
                stone.color = '#6666af' if self.pits[p].player == 1 else '#75755e'
                p = (p + 1) % len(self.pits)
        except StopIteration:
            pass
        self.game_over = False

    def is_player_target(self, pit_id):
        '''return True if the supplied `pid_id` is the current player's target pit'''
        if self.pits[pit_id].target and self.pits[pit_id].player == self.current_player:
            return True
        return False

    def is_opponent_target(self, pit_id):
        '''return True if the supplied `pid_id` is the opponent's (i.e. *not* the current player's) target pit'''
        if self.pits[pit_id].target and self.pits[pit_id].player != self.current_player:
            return True
        return False

    def toggle_player(self):
        '''alternate between players'''
        while True:
            yield 1
            yield 2

    def random_move(self):
        '''choose a (valid) random move for the active player'''
        pits_remaining = [p for p in self.pits if p.player == self.current_player and p.target != True and p.count_stones()]
        move = choice(pits_remaining)
        return move.id

    def perform_captures(self):
        '''Perform captures. Can only be done after a sow.
        In this case, `captures_done` will be True, and
        `last_pit` will indicate where the final sown stone ended.
        '''
        if self.captures_done == True:
            if self.last_pit is None:
                return # nothing to do
            else:
                raise RuntimeError, 'last_pit is set but captures done'

        if self.last_pit is None:
                raise RuntimeError, 'captures needed, but last_pit not set'

        if self.pits[self.last_pit].player == self.current_player: # my pit
            if self.pits[self.last_pit].count_stones() == 1: # potential capture

                # Compute the pit opposite me. Note: pits always add to 2 * n_pits. e.g.
                #        0  1  2  3  4  5  6  7(T)
                # 13(T) 12 11 10  9  8  7  6
                #       --------------------
                #       12 12 12 12 12 12 12

                opp_p = (len(self.pits) - 2) - self.last_pit
                if self.pits[opp_p].count_stones():
                    # capture occurs
                    self.pits[opp_p].pickup_stones()
                    self.pits[self.last_pit].pickup_stones()

                    captured = (stone for stone in self.stones if stone.pit is None)
                    try:
                        while True:
                            stone = captured.next()
                            self.pits[self.targets[self.current_player]].add(stone)
                    except StopIteration:
                        pass

        self.captures_done = True

    def moves_available(self):
        '''Return True if there are stones in non-target pits for the current player'''
        left = [p.count_stones() for p in self.pits if p.player == self.current_player and p.target != True]
        return (sum(left) > 0)


    def handle_endgame(self):
        '''Check if there are any valid moves for the current player.
        If not, move opponent's stones to their target pit and declare the game over
        '''
        if (self.moves_available()):
            return

        self.current_player = self.get_player.next()

        pits_remaining = [p for p in self.pits if p.player == self.current_player and p.target != True and p.count_stones()]
        for p in pits_remaining:
            p.pickup_stones()
        endgame_captures = (stone for stone in self.stones if stone.pit is None)
        try:
            while True:
                stone = endgame_captures.next()
                self.pits[self.targets[self.current_player]].add(stone)
        except StopIteration:
            pass

        self.game_over = True

    def update_player(self, debug=False):
        if debug:
            print('Current player: {}'.format(self.current_player))
        if self.last_pit is None:
            raise RuntimeError, 'update_player called and last_pit is None'
        if not self.is_player_target(self.last_pit):
            self.current_player = self.get_player.next()
        if debug:
            print('Toggle player? {}'.format(not self.is_player_target(self.last_pit)))
            print('New player? {}'.format(self.current_player))
        self.last_pit = None


    def sow(self, pit_id, direction='ccw', debug=False):
        '''Current player picks up the seeds in pit `pit_id`,
        sowing in the direction specified by `direction`
        * Note: `direction` is not currently used
        '''
        if self.current_player != self.pits[pit_id].player:
            print("Not Your Turn!")
            return False
        if self.pits[pit_id].count_stones() == 0:
            print("No stones here")
            return False
        if self.pits[pit_id].target:
            print("can't sow a target")
            return False
        if self.captures_done == False:
            print("Can't re-sow without first performing captures")
            return False

        self.captures_done = False
        self.next_player = None

        # Perform the sowing
        self.pits[pit_id].pickup_stones()
        unplaced = (stone for stone in self.stones if stone.pit is None)
        p = (pit_id + 1) % len(self.pits)
        try:
            while True:
                stone = unplaced.next()
                if self.is_opponent_target(p):
                    p = (p + 1) % len(self.pits)
                if debug:
                    print('Sowing stone {} in pit {}'.format(stone.id, self.pits[p].id))
                self.pits[p].add(stone)
                last_p = p
                p = (p + 1) % len(self.pits)
        except StopIteration:
            pass

        self.last_pit = last_p

        return True

    def play_round(self, pit_no, direction='ccw', debug=False):
        '''Play a round of bao. Sow, starting at `pit_no`
        * `direction` is currently ignored.
        If the indicated move is invalid, return None.
        Otherwise, return the game status, current player, and stones list.
        '''
        success = self.sow(pit_no, direction, debug)

        if not success: # not a valid move
            return None

        self.perform_captures()

        self.update_player()

        self.handle_endgame()

        return (self.game_over, self.current_player, self.stones)



def random_game(bg=None, debug=False):
    '''Play a game of bao to completion by choosing (valid) moves at random.
    If `bao` is passed, the game will be played at random from the supplied position.
    `debug = True` makes for more verbose output (e.g. prints the board after each move)
    '''
    move_list = []
    if bg is None:
        bg=Game()
        bg.initial_place()
    if debug:
        print(bg)
    player = bg.current_player
    mno = 1
    move = bg.random_move()
    move_list += [move]
    if debug:
        print ('Move {}: Player {} sows {}'.format(mno, player, move))
    (done, player, stones) = bg.play_round(move)
    while not done:
        if debug:
            print(bg)
        move = bg.random_move()
        move_list += [move]
        mno = mno + 1
        if debug:
            print ('Move {}: Player {} sows {}'.format(mno, player, move))
        try:
            (done, player, stones) = bg.play_round(move)
        except:
            raise RuntimeError, "Error on game: {}".format(move_list)

    if debug:
        print(bg)
        print('Final score:')
    scores = []
    for player in [1,2]:
        pscore = bg.pits[bg.targets[player]].count_stones()
        if debug:
            print("Player {}: {}".format(player, pscore))
        scores.append(pscore)
    bg.move_list = move_list
    return (bg, scores)


def check_game(bao_game, scores):
    '''Run consistency checks on a game.
    Raise exceptions on any issues.'''
    if bao_game.game_over:
        # End of game checks

        # score should add to number of stones
        if sum(scores) != len(bao_game.stones):
            raise RuntimeError, "Final score {} doesn't sum to {}".format(scores, len(bao_game.stones))


def play_game(move_list, debug=False):
    '''Play a new game of bao with the specified move list.
    Returns the bao game, and the score after all moves are completed.
    '''
    bg = Game()
    bg.initial_place()
    mno = 1
    for move in move_list:
        if debug:
            print('Player {} sows {}'.format(bg.current_player, move))
        bg.play_round(move)
        if debug:
            print(bg)

    scores = []
    for player in [1,2]:
        pscore = bg.pits[bg.targets[player]].count_stones()
        if debug:
            print("Player {}: {}".format(player, pscore))
        scores.append(pscore)
    return (bg, scores)

def generate_test_vectors(self, n=50, filename='test_vectors.json'):
    test_vectors = []
    for i in range(n):
        bg = bao.bao_game()
        bg.initial_place()
        bao.random_game(bg=bg)
        test_vectors.append((bg.move_list, bg.score))

    with open(filename, 'w') as fp:
        json.dump(test_vectors, fp)


def verify_test_vectors(self, filename='test_vectors.json'):
    '''evaluate test vectors, consisting of tuples:
       [move list], [p1_score, p2_score]
    Basically, run the supplied moves, and ensure the new score matches the old
    '''
    with open('test_vectors.json', 'r') as fr:
        tv = json.load(fr)
        for (ml, score) in tv:
            b,s = play_game(ml)
            if sum(tuple(map(sub, score, s))) != 0:
                raise RuntimeError, 'New score {} != {}. for test moves {}'.format(s, score, ml)


if __name__ == '__main__':

    # Known Test cases
    tests = []
    tests.append(("All positions full error", [1, 9, 2, 0, 7, 3, 11, 0, 10, 1, 11, 4, 7, 5, 11, 8, 0, 7, 3, 11, 2, 5, 4, 9, 1, 11]))
    tests.append(("Game ends with all positions full in a pit", [2, 9, 0, 12, 0, 11, 0, 7, 2, 12, 9, 5, 9, 4, 7, 5, 1, 9, 2, 10, 0, 7, 2, 12, 4, 0, 11, 8, 2, 10, 1, 9, 4, 11, 12, 1]))
    tests.append(("Game ends leaving pieces on the board", [4, 9, 2, 7, 1, 12, 3, 10, 5, 12, 10, 2, 8, 1, 12, 7, 2, 8, 4, 10, 0, 3, 7, 1, 9, 0, 10, 4, 1, 12, 8, 3, 9, 4, 10, 5, 9]))

    for tc in tests:
        bg, scores = play_game(tc[1])
        check_game(bg, scores)

    # Random Games

    for gno in range(100):
        bg, score = random_game()
        check_game(bg, score)

    # test pickup_stones bug (not all stones were picked up) by re-adding everything a 2nd time

    p = Pit(id=1)
    ss = [Stone(id=i) for i in range(16)]
    for s in ss:
        p.add(s)
    p.pickup_stones()
    for s in ss:
        p.add(s)
    p.pickup_stones()
    left = p.count_stones()
    if left:
        print("Should be no stones left. Found {}".format(left))
        p.pretty_print()
        print([s for s in ss if s.pit is not None])

    # known test vectors
    import json
    from kivy.vector import Vector
    with open('testvectors.json', 'r') as fr:
        tv = json.load(fr)
        for (ml, score) in tv:
            b,s = play_game(ml)
            if sum(Vector(score) - s) != 0:
                raise RuntimeError, 'New score {} != {}. for test moves {}'.format(s, score, ml)
