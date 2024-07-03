import os
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.core.window import Window
from kivy.properties import ObjectProperty

from kivy.core.audio import SoundLoader

import pyaudio
import wave
import audioop

Window.size = (360, 640)


# Load the Kv files
Builder.load_file('login.kv')
Builder.load_file('assistant.kv')

class LoginScreen(Screen):
    pass

class AssistantScreen(Screen):

    def soundAuthentication(self, givenPassword):
        match givenPassword:
            case "Captain John One":
                # Correct password
                return os.path.join('Sounds', "AuthenthicateConfirmJohn.mp3")
            
            case "Wrong Password":
                # Incorrect password
                return os.path.join('Sounds', "AuthenthicateWrong.mp3")
        
        # Default case
        return os.path.join('Sounds', "IncorrectInput.mp3")

    def menuOptions(self, inputPrompt):
        match inputPrompt:
            case "Greetings":
                return os.path.join('Sounds', "AuthenthicateQuestion.mp3")
            case "What is my current balance":
                return os.path.join('Sounds', "BalanceRead.mp3")
            
            case "Transfer Money":
                return os.path.join('Sounds', "PayAmount.mp3")
            
            case "Pay electric bill":
                return os.path.join('Sounds', "PayElectricBill.mp3")

            case "That's all thank you":
                return os.path.join('Sounds', "Goodbye.mp3")
            
            case _:
                return os.path.join('Sounds', "IncorrectInput.mp3")
            
    def soundMenu(self):
        return os.path.join('Sounds', "AdditionalAssistance.mp3")

    def soundTransferMoney10(self):
        return os.path.join('Sounds', "Pay10Dollars.mp3")

    def soundTransferWrong(self):
        return os.path.join('Sounds', "TransferNewAccount.mp3")

    def playSound(self, voiceInput):
        # Construct the full path to the sound file
        sound_file = self.menuOptions(voiceInput)

        sound = SoundLoader.load(sound_file)
        if sound:
            print("Sound found at %s" % sound.source)
            print("Sound is %.3f seconds" % sound.length)
            sound.play()
        else:
            print("Sound file not found or could not be loaded")
    
    


class MyApp(App):
    
    
    def build(self):
        # Create a ScreenManager
        sm = ScreenManager()
        sm.add_widget(LoginScreen(name='login'))
        sm.add_widget(AssistantScreen(name='assistant'))
        
        # Construct the full path to the sound file
        base_path = os.path.dirname(os.path.abspath(__file__))
        sound_file = os.path.join(base_path, 'Sounds', 'Goodbye.mp3')

        assistant_screen = sm.get_screen('assistant')
        if assistant_screen:
            assistant_screen.playSound("Greetings")

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


