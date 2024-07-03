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

# Load the Kv files
Builder.load_file('login.kv')
Builder.load_file('assistant.kv')

def playSound(voiceInput):
    # Construct the full path to the sound file based on voice input
    sound_file = menuOptions(voiceInput)

    sound = SoundLoader.load(sound_file)
    if sound:
        print("Sound found at %s" % sound.source)
        print("Sound is %.3f seconds" % sound.length)
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
            playSound(text)  # Function to handle text response
        except sr.UnknownValueError:
            print("Could not understand audio")
        except sr.RequestError as e:
            print("Could not request results; {0}".format(e))

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
        
        # Start continuous recording in a separate thread
        recording_thread = threading.Thread(target=continuous_recording)
        recording_thread.daemon = True  # Daemonize the thread to stop with the app
        recording_thread.start()
        
        # Play initial greeting sound
        playSound("Greetings")
        
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
