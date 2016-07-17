from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
import bao_engine as Bao
from kivy.logger import Logger

class Pit(BoxLayout):
    def choose_pit(self):
        '''Pit was touched. Act on the touch'''
        Logger.debug('Pit: Touch on {}'.format(self.pit_obj))



class BaoGame(BoxLayout):
    def __init__(self, **kwargs):
        super(BaoGame, self).__init__(**kwargs)
        self.engine = Bao.Game()
        self.link_pits()

    def link_pits(self):
        for c in self.board_overlay.children:
            if type(c) is Pit:
                c.pit_obj = self.engine.pits[c.pit_id]
                Logger.debug('Link Pits: linked pit {} to {}'.format(c.pit_id, c.pit_obj))

            if type(c) is GridLayout:
                for c2 in c.children:
                    c2.pit_obj = self.engine.pits[c2.pit_id]
                    Logger.debug('Link Pits: linked pit {} to {}'.format(c2.pit_id, c2.pit_obj))


    def start_game(self):
        '''Do the initial sow (place) to start a game'''
        self.engine.initial_place()
        self.toolbar.start_button.disabled = True

class BaoApp(App):
    def build(self):
        bg = BaoGame()
        return bg

if __name__ == '__main__':
    BaoApp().run()
