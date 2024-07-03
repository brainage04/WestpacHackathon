from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen

# Load the Kv files
Builder.load_file('login.kv')
Builder.load_file('assistant.kv')

class LoginScreen(Screen):
    pass

class AssistantScreen(Screen):
    pass

class MyApp(App):
    def build(self):
        # Create a ScreenManager
        sm = ScreenManager()
        sm.add_widget(LoginScreen(name='login'))
        sm.add_widget(AssistantScreen(name='assistant'))
        return sm

    def login(self, username, password):
        # Implement your login logic here
        print(f'Logging in with username: {username} and password: {password}')
        # Example of switching to the assistant screen after login
        self.root.current = 'assistant'

    def perform_action_1(self):
        # Implement action 1 logic
        print('Performing Action 1')

    def perform_action_2(self):
        # Implement action 2 logic
        print('Performing Action 2')

    def logout(self):
        # Implement logout logic
        print('Logging out')
        self.root.current = 'login'

if __name__ == '__main__':
    MyApp().run()
