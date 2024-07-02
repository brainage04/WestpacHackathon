from kivy.app import App
from kivy.uix.screenmanager import Screen, SlideTransition
from kivy.graphics import Rectangle
from kivy.graphics import Color
from kivy.graphics import Line

class Connected(Screen):
    def disconnect(self):
        self.manager.transition = SlideTransition(direction="right")
        self.manager.current = 'login'
        self.manager.get_screen('login').resetForm()
    
    def readCurrentBalance(self):
        pass
        