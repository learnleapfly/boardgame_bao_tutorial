from kivy.app import App
from kivy.uix.boxlayout import BoxLayout

class BaoGame(BoxLayout):
    pass

class BaoApp(App):
    def build(self):
        bg = BaoGame()
        return bg
    
if __name__ == '__main__':
    BaoApp().run()