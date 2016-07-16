from __future__ import print_function
from random import choice
from math import ceil
from itertools import cycle

class pit():
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
        print(s)

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


class stone():
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


class bao_game():
    def __init__(self, n_stones=36, n_pits=6, n_rows=1):
        '''Create a bao game.
        * `n_pits` is the number of (non-target) pits per player
        * `n_rows` is the rows of pits per player (not currently used)
        * `n_stones` is the number of stones (seeds) that the game starts with'''
        self.game_over = False
        self.n_rows = n_rows
        self.n_pits = n_pits
        self.stones = [stone(id=i) for i in range(n_stones)]
        self.pits = [pit(target=(i%(n_pits+1) == n_pits),
                      player=(1 if i <= n_pits else 2),
                      id=i) for i in range(2*n_pits + 2)]
        self.targets = {}

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
        return s + '\nNext: Player {} \tGame State: {}\n'.format(self.current_player, 'Game Over' if self.game_over else 'Playing')

    def initial_place(self, debug=False, direction='ccw'):
        '''Do the initial placement (sowing) of stones.
        Place one in each non-target pit until all stones have been placed.
        * `direction` is currently unused'''

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

    def sow(self, pit_id, direction='ccw', debug=False):
        '''Current player picks up the seeds in pit `pit_id`,
        sowing in the direction specified by `direction`
        * Note: `direction` is not currently used
        '''
        if self.current_player != self.pits[pit_id].player:
            print("Not Your Turn!")
            return
        if self.pits[pit_id].count_stones() == 0:
            print("No stones here")
            return
        if self.pits[pit_id].target:
            print("can't sow a target")
            return
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
        if self.is_player_target(last_p):
            # Landed in out target.
            next_player = self.current_player
        else:
            next_player = self.get_player.next()

            # compute captures
            if self.pits[last_p].player == self.current_player: # my pit
                if self.pits[last_p].count_stones() == 1: # potential capture
                    opp_p = (len(self.pits) - 2) - last_p
                    if self.pits[opp_p].count_stones():
                        # capture occurs
                        self.pits[opp_p].pickup_stones()
                        self.pits[last_p].pickup_stones()
                        unplaced = (stone for stone in self.stones if stone.pit is None)
                        try:
                            while True:
                                stone = unplaced.next()
                                self.pits[self.targets[self.current_player]].add(stone)
                        except StopIteration:
                            pass
        self.current_player = next_player
        left = [p.count_stones() for p in self.pits if p.player == self.current_player and p.target != True]
        if (sum(left) == 0):
            # move remaining stones to target
            self.current_player = self.get_player.next()
            pits_remaining = [p for p in self.pits if p.player == self.current_player and p.target != True and p.count_stones()]
            for p in pits_remaining:
                p.pickup_stones()
            last_moves = (stone for stone in self.stones if stone.pit is None)
            try:
                while True:
                    stone = last_moves.next()
                    self.pits[self.targets[self.current_player]].add(stone)
            except StopIteration:
                pass
            self.game_over = True
        return (self.game_over, next_player, self.stones)


def random_game(bao = None, debug=False):
    '''Play a game of bao to completion by choosing (valid) moves at random.
    If `bao` is passed, the game will be played at random from the supplied position.
    `debug = True` makes for more verbose output (e.g. prints the board after each move)
    '''
    move_list = []
    if bao is None:
        bao=bao_game()
        bao.initial_place()
    if debug:
        print(bao)
    player = bao.current_player
    mno = 1
    move = bao.random_move()
    move_list += [move]
    if debug:
        print ('Move {}: Player {} sows {}'.format(mno, player, move))
    (done, player, stones) = bao.sow(move)
    while not done:
        if debug:
            print(bao)
        move = bao.random_move()
        move_list += [move]
        mno = mno + 1
        if debug:
            print ('Move {}: Player {} sows {}'.format(mno, player, move))
        try:
            (done, player, stones) = bao.sow(move)
        except:
            print("Error on game: {}".format(move_list))
            raise OverflowError

    if debug:
        print(bao)
        print('Final score:')
    scores = []
    for player in [1,2]:
        pscore = bao.pits[bao.targets[player]].count_stones()
        if debug:
            print("Player {}: {}".format(player, pscore))
        scores.append(pscore)
    bao.move_list = move_list
    return (bao, scores)


def check_game(bao, scores):
    '''Run consistency checks on a game.
    Raise exceptions on any issues.'''
    if bao.game_over:
        # End of game checks

        # score should add to number of stones
        if sum(scores) != len(bao.stones):
            raise RuntimeError, "Final score {} doesn't sum to {}".format(scores, len(bao.stones))


    # test addition, removal


def play_game(move_list, debug=False):
    '''Play a new game of bao with the specified move list.
    Returns the bao game, and the score after all moves are completed.
    '''
    bao=bao_game()
    bao.initial_place()
    mno = 1
    for move in move_list:
        if debug:
            print('Player {} sows {}'.format(bao.current_player, move))
        bao.sow(move)
        if debug:
            print(bao)

    scores = []
    for player in [1,2]:
        pscore = bao.pits[bao.targets[player]].count_stones()
        if debug:
            print("Player {}: {}".format(player, pscore))
        scores.append(pscore)
    return (bao, scores)

if __name__ == '__main__':

    # Known Test cases
    tests = []
    tests.append(("All positions full error", [1, 9, 2, 0, 7, 3, 11, 0, 10, 1, 11, 4, 7, 5, 11, 8, 0, 7, 3, 11, 2, 5, 4, 9, 1, 11]))
    tests.append(("Game ends with all positions full in a pit", [2, 9, 0, 12, 0, 11, 0, 7, 2, 12, 9, 5, 9, 4, 7, 5, 1, 9, 2, 10, 0, 7, 2, 12, 4, 0, 11, 8, 2, 10, 1, 9, 4, 11, 12, 1]))
    tests.append(("Game ends leaving pieces on the board", [4, 9, 2, 7, 1, 12, 3, 10, 5, 12, 10, 2, 8, 1, 12, 7, 2, 8, 4, 10, 0, 3, 7, 1, 9, 0, 10, 4, 1, 12, 8, 3, 9, 4, 10, 5, 9]))

    for tc in tests:
        bao, scores = play_game(tc[1])
        check_game(bao, scores)

    # Random Games

    for gno in range(1000):
        bao, score = random_game()
        check_game(bao, score)

    # test pickup_stones bug (not all stones were picked up) by re-adding everything a 2nd time

    p = pit(id=1)
    ss = [stone(id=i) for i in range(16)]
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
