from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.properties import ObjectProperty, NumericProperty, ListProperty
import bao_engine as Bao
from kivy.logger import Logger
from kivy.uix.image import Image
from kivy.utils import get_color_from_hex
from random import randrange
from kivy.animation import Animation

class Pit(BoxLayout):
    def choose_pit(self):
        '''Pit was touched. Act on the touch'''
        Logger.debug('Pit: Touch on {}'.format(self.pit_obj))
        self.board.engine.play_round(self.pit_obj.id)
        self.board.stone_locations = self.board.engine.stones[:]
        self.board.animate_stones(self.board.stone_locations)
        self.board.turn_no += 1
        self.board.scores = self.board.engine.score
        self.board.curr_player = self.board.engine.current_player

class Stone(Image):
    pass

class BaoGame(BoxLayout):
    stone_locations = ObjectProperty(None)
    turn_no = NumericProperty(0)
    scores = ListProperty(None)
    curr_player = NumericProperty(None)
    def __init__(self, **kwargs):
        super(BaoGame, self).__init__(**kwargs)
        self.engine = Bao.Game()
        self.link_pits()
        self.init_stones()

    def move_stones(self, inst, value):
        sl = [s.kivy_obj for s in self.engine.stones if s.pit == inst.pit_obj.id]
        for s in sl:
            my_pos = self.pos_to_coords(s.stone_obj.position, inst)
            s.x = my_pos[0]
            s.y = my_pos[1]

    def pos_to_coords(self, pos, obj, rows=4, cols=4):
        '''given a position (integer), compute its coordinates inside the supplied `obj`'''
        if obj.pit_obj.target:
            rows = 12
        x_coord = pos % cols
        y_coord = pos // cols
        y_off = obj.height / rows * y_coord
        x_off = obj.width / cols * x_coord
        return (obj.x + x_off, obj.y + y_off)

    def init_stones(self):
        '''put the stones somewhere. Initially, half in one target, half in the other'''
        for stone in self.engine.stones:
            target_pit = self.engine.pits[self.engine.targets[stone.id%2 + 1]]
            target_pit.add(stone)
            my_pos = self.pos_to_coords(stone.position, target_pit.kivy_obj)
            sz = (target_pit.kivy_obj.width/3,  target_pit.kivy_obj.width/3)
            stone.kivy_obj = Stone(size_hint=(None,None),size=sz, pos=my_pos)
            stone.kivy_obj.color = get_color_from_hex(stone.color)
            stone.kivy_obj.stone_obj = stone
            target_pit.kivy_obj.contents.add_widget(stone.kivy_obj)


    def link_pits(self):
        for c in self.board_overlay.children:
            if type(c) is GridLayout:
                for c2 in c.children:
                    if type(c2) is Pit:
                        c2.board = self
                        c2.pit_obj = self.engine.pits[c2.pit_id]
                        self.engine.pits[c2.pit_id].kivy_obj = c2
                        c2.bind(pos=self.move_stones, size=self.move_stones)
                        Logger.debug('Link Pits: linked pit {} to {}'.format(c2.pit_id, c2.pit_obj))

    def animate_stones(self, stone_list):
        for stone in stone_list:
            my_pit = self.engine.pits[stone.pit].kivy_obj
            my_pos = self.pos_to_coords(stone.position, my_pit)
            anim = Animation(x=my_pos[0], y=my_pos[1],d=0.5)
            anim.start(stone.kivy_obj)

    def on_stone_locations(self, inst, value):
        '''Update the stones by animating them to their final location'''
        self.animate_stones(value)


    def start_game(self):
        '''Do the initial sow (place) to start a game'''
        self.engine.initial_place()
        self.toolbar.start_button.disabled = True
        self.stone_locations = self.engine.stones[:]

class BaoApp(App):
    def build(self):
        bg = BaoGame()
        return bg

if __name__ == '__main__':
    BaoApp().run()
