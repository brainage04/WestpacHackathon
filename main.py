import os
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.core.window import Window
from kivy.core.audio import SoundLoader
import threading
import speech_recognition as sr

Window.size = (360, 640)

recorded_text = ""
audio_playing = False

# Load the Kv files
Builder.load_file('login.kv')
Builder.load_file('assistant.kv')

def playSound(voiceInput):
    # Construct the full path to the sound file based on voice input
    global audio_playing
    sound_file = menuOptions(voiceInput)

    sound = SoundLoader.load(sound_file)
    if sound:
        print("Sound found at %s" % sound.source)
        print("Sound is %.3f seconds" % sound.length)
        audio_playing = True
        sound.bind(on_stop=lambda _: setattr(sound, 'audio_playing', False))
        sound.play()
    else:
        print("Sound file not found or could not be loaded")

def menuOptions(inputPrompt):
    # Define menu options based on input prompt
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

def continuous_recording():
    # Function for continuous recording and processing
    global recorded_text
    print("Recording started...")
    recognizer = sr.Recognizer()
    microphone = sr.Microphone()
    
    while True:
        with microphone as source:
            print("Listening...")
            audio = recognizer.listen(source)
        
        # Process the audio
        try:
            text = recognizer.recognize_google(audio)
            print("Recognized:", text)
            recorded_text = text
            assistant_screen = MyApp.get_running_app().assistant_screen
            login_screen = MyApp.get_running_app().login_screen
            if assistant_screen:
                assistant_screen.processText(text)  # Call method on AssistantScreen instance
            if login_screen:
                login_screen.checkPassword(text)  # Call method on AssistantScreen instance
        except sr.UnknownValueError:
            print("Could not understand audio")
        except sr.RequestError as e:
            print("Could not request results; {0}".format(e))

class LoginScreen(Screen):
    def checkPassword(self, text):
        # Process the recognized text
        print(f"Processing text: {text}")
        # Example: Perform actions based on recognized text
        if "password" in text.lower():
            self.passwordAuthenticate(True)
        else:
            self.passwordAuthenticate(False)

    def passwordAuthenticate(self, passwordCorrect):
        # Construct the full path to the sound file
        global audio_playing

        if passwordCorrect:
            playAudioPath = os.path.join('Sounds', "AuthenthicateConfirmJohn.mp3")
            self.manager.current = 'assistant'
        else:
            playAudioPath = os.path.join('Sounds', "AuthenthicateWrong.mp3")

        sound = SoundLoader.load(playAudioPath)
        if sound:
            audio_playing = True
            sound.bind(on_stop=lambda _: setattr(sound, 'audio_playing', False))
            print("Sound found at %s" % sound.source)
            print("Sound is %.3f seconds" % sound.length)
            sound.play()
        else:
            print("Sound file not found or could not be loaded")


class AssistantScreen(Screen):
    def log_off(self):
        self.manager.current = 'login'

    def processText(self, text):
        # Process the recognized text
        print(f"Processing text: {text}")
        # Example: Perform actions based on recognized text
        if "balance" in text.lower():
            self.playSound("What is my current balance")
        elif "transfer" in text.lower():
            self.playSound("Transfer Money")
        else:
            self.playSound("IncorrectInput")

    def playSound(self, voiceInput):
        global audio_playing
        # Construct the full path to the sound file
        sound_file = menuOptions(voiceInput)

        sound = SoundLoader.load(sound_file)
        if sound:
            print("Sound found at %s" % sound.source)
            print("Sound is %.3f seconds" % sound.length)
            audio_playing = True
            sound.bind(on_stop=lambda _: setattr(sound, 'audio_playing', False))
            sound.play()
        else:
            print("Sound file not found or could not be loaded")

class MyApp(App):
    assistant_screen = None  # Store a reference to AssistantScreen instance
    login_screen = None
    
    def build(self):
        # Create a ScreenManager
        sm = ScreenManager()
        self.login_screen = LoginScreen(name='login')
        self.assistant_screen = AssistantScreen(name='assistant')
        
        sm.add_widget(self.login_screen)
        sm.add_widget(self.assistant_screen)
        
        # Start continuous recording in a separate thread
        recording_thread = threading.Thread(target=continuous_recording)
        recording_thread.daemon = True  # Daemonize the thread to stop with the app
        recording_thread.start()
        
        # Play initial greeting sound
        self.assistant_screen.playSound("Greetings")
        
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
