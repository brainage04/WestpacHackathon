import os
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.core.window import Window
from kivy.core.audio import SoundLoader
import threading
import speech_recognition as sr
from kivy.clock import Clock


import struct

#pip3 install pvrecorder
from pvrecorder import PvRecorder
recorder = PvRecorder(device_index=-1, frame_length=512)
recorderAudio = []
import wave

#pip install PyAudio
import pyaudio

#pip install pydub
from pydub import AudioSegment
from pydub.utils import which

Window.size = (360, 640)

recorded_text = ""
audio_playing = True
assistant_option = "start"
assistant_option_state = 0
insideOption = False

# Load the Kv files
Builder.load_file('login.kv')
Builder.load_file('assistant.kv')

def playSound(voiceInput):
    # Construct the full path to the sound file based on voice input
    global audio_playing
    sound_file = menuOptions(voiceInput)

    sound = SoundLoader.load(sound_file)
    if sound:
        audio_playing = True
        sound.bind(on_stop=audioPlayingFalse)
        print("Sound found at %s" % sound.source)
        print("Sound is %.3f seconds" % sound.length)
        sound.play()
    else:
        print("Sound file not found or could not be loaded")

def audioPlayingFalse(self, _):
    global audio_playing
    audio_playing = False
    print("Sound finished playing and audio_playing is: ", audio_playing)

def menuOptions(inputPrompt):
    # Define menu options based on input prompt
    match inputPrompt:
        case "balance":
            return os.path.join('Sounds', "BalanceRead.mp3")
        case "Transfer Money":
            return os.path.join('Sounds', "PayAmount.mp3")
        case "Pay electric bill":
            return os.path.join('Sounds', "PayElectricBill.mp3")
        case "goodbye":
            return os.path.join('Sounds', "Goodbye.mp3")
        case _:
            return os.path.join('Sounds', "IncorrectInput.mp3")

def continuous_recording():
    global recorded_text
    global audio_playing
    print("Recording started...")
    recognizer = sr.Recognizer()
    microphone = sr.Microphone()
    
    while True:
        if not audio_playing:
            with microphone as source:
                print("Listening...")
                audio = recognizer.listen(source)
            
            try:
                # Extract raw audio data
                raw_audio = audio.get_raw_data()
                waveFilePath = os.path.join('Sounds', 'recording.wav')
                # Save the raw audio data to a wave file
                with wave.open(waveFilePath, 'wb') as f:
                    f.setnchannels(1)
                    f.setsampwidth(audio.sample_width)
                    f.setframerate(audio.sample_rate)
                    f.writeframes(raw_audio)

                text = recognizer.recognize_google(audio)
                print("Recognized:", text)
                recorded_text = text
                app = MyApp.get_running_app()
                current_screen = app.root.current
                assistant_screen = app.assistant_screen
                login_screen = app.login_screen
                if current_screen == 'assistant' and assistant_screen:
                    assistant_screen.optionSelect(text)  # Call method on AssistantScreen instance
                elif current_screen == 'login' and login_screen:
                    login_screen.checkPassword(text)  # Call method on LoginScreen instance
            except sr.UnknownValueError:
                print("Could not understand audio")
            except sr.RequestError as e:
                print("Could not request results; {0}".format(e))
            except FileNotFoundError as e:
                print(f"File not found error: {e}")

class LoginScreen(Screen):
    def on_enter(self):
        self.playSoundGreeting()

    def playSoundGreeting(self):
        global audio_playing
        # Construct the full path to the sound file
        print("Greeting")
        audio_playing = True
        sound_file = os.path.join('Sounds', "AuthenthicateQuestion.mp3")

        sound = SoundLoader.load(sound_file)
        if sound:
            print("Sound found at %s" % sound.source)
            print("Sound is %.3f seconds" % sound.length)
            audio_playing = True
            sound.bind(on_stop=self.on_sound_stop)
            sound.play()
        else:
            print("Sound file not found or could not be loaded")

    def on_sound_stop(self, sound):
        global audio_playing
        audio_playing = False

    def checkPassword(self, text):
        recognized_phrase = "password"
        if recognized_phrase == text.lower():
            self.passwordAuthenticate(True)
        else:
            self.passwordAuthenticate(False)

    def passwordAuthenticate(self, passwordCorrect):
        # Construct the full path to the sound file
        global audio_playing

        if passwordCorrect:
            playAudioPath = os.path.join('Sounds', "AuthenthicateConfirm.mp3")
            Clock.schedule_once(lambda dt: self.change_to_assistant_screen())
        else:
            playAudioPath = os.path.join('Sounds', "AuthenthicateWrong.mp3")

        sound = SoundLoader.load(playAudioPath)
        if sound:
            audio_playing = True
            sound.bind(on_stop=self.audioPlayingFalse)
            print("Sound found at %s" % sound.source)
            print("Sound is %.3f seconds" % sound.length)
            sound.play()
        else:
            print("Sound file not found or could not be loaded")

    def audioPlayingFalse(self, _):
        global audio_playing
        audio_playing = False
        print("Sound finished playing and audio_playing is: ", audio_playing)

    def change_to_assistant_screen(self):
        self.manager.current = 'assistant'


class AssistantScreen(Screen):
    def log_off(self):
        self.manager.current = 'login'

    def optionSelect(self, text):
        global assistant_option
        global insideOption
        global assistant_option_state

        if insideOption == False:
            text_lower = text.lower()
            if "balance" in text_lower:
                assistant_option = "balance"
                insideOption = True
            elif "transfer" in text_lower:
                assistant_option = "transfer"
                insideOption = True
            elif "pay" in text_lower:
                assistant_option = "pay bill"
                insideOption = True
            elif "no" in text_lower or "exit" in text_lower or "log off" in text_lower:
                assistant_option = "logout"
                insideOption = True
            else:
                self.playSoundIncorrectInput()
            
            print(f"Current assistant option: {assistant_option} with status of insideOption being: {insideOption}")

        if assistant_option == "balance":
            self.chainReadBalance()
        elif assistant_option == "transfer":
            self.chainTransfer()
        elif assistant_option == "pay bill":
            insideOption = False
        elif assistant_option == "logout":
            self.chainLogOut()
        else:
            insideOption = False
            
    def chainReadBalance(self):
        global insideOption
        global assistant_option_state
        print("inside chainReadBalance")

        assistant_option_state = 0
        insideOption = False
        self.playSoundFile("BalanceRead.mp3")
        
    
    def chainTransfer(self):
        global insideOption
        global assistant_option_state
        global recorded_text
        global audio_playing

        print("inside chainTransfer")

        # Use a while loop to ensure it processes as expected
        while True:
            if not audio_playing:
                match assistant_option_state:
                    case 0:
                        # Ask Name
                        print("State 0: Ask Name")
                        if "darren" in recorded_text.lower():
                            assistant_option_state = 1
                        else:
                            assistant_option_state = 5   
                    case 1:
                        # Confirm Name
                        print("State 1: Confirm Name")
                        assistant_option_state = 2
                    case 2:
                        # Confirm Amount
                        print("State 2: Confirm Amount")
                        assistant_option_state = 3
                    case 3:
                        # Payment Name
                        print("State 3: Payment Name")
                        assistant_option_state = 4
                    case 4:
                        # Finished
                        print("State 4: Finished")
                        assistant_option_state = 0
                        insideOption = False
                        break  # Exit loop as the operation is finished
                    case 5:
                        # New Account
                        print("State 5: New Account")
                        assistant_option_state = 0
                        insideOption = False
                        break  # Exit loop as the operation is finished
            else:
                match assistant_option_state:
                    case 0:
                        self.playSoundFile("TransferAccount.mp3")
                    case 1:
                        self.playSoundFile("TransferDarrenSmith.mp3")
                    case 2:
                        self.playSoundFile("Pay10Dollars.mp3")
                    case 3:
                        self.playSoundFile("PaymentName.mp3")
                    case 4:
                        self.playSoundFile("PayTransfer.mp3")
                    case 5:
                        self.playSoundFile("TransferNewAccount.mp3")
                break  # Exit loop to wait for audio to finish
    
    def chainLogOut(self):
        global insideOption
        global assistant_option_state
        
        assistant_option_state = 0
        insideOption = False

        print("inside chainLogOut")

        Clock.schedule_once(lambda dt: self.change_to_login_screen())
        self.manager.current = 'login'
        self.playSoundFile ("goodbye.mp3")

    def change_to_login_screen(self):
        print("changing to login screen")
        self.manager.current = 'login'

    def playSound(self, voiceInput):
        global audio_playing
        # Construct the full path to the sound file
        sound_file = menuOptions(voiceInput)

        sound = SoundLoader.load(sound_file)
        if sound:
            audio_playing = True
            sound.bind(on_stop=self.audioPlayingFalse)
            print("Sound found at %s" % sound.source)
            print("Sound is %.3f seconds" % sound.length)
            sound.play()
        else:
            print("Sound file not found or could not be loaded")
    
    def playSoundIncorrectInput(self):
        global audio_playing
        # Construct the full path to the sound file
        sound_file = os.path.join('Sounds', "IncorrectInput.mp3")
        print("Incorrect input for asssitant ")
        sound = SoundLoader.load(sound_file)
        if sound:
            audio_playing = True
            sound.bind(on_stop=self.playSoundFile("AdditionalAssistance.mp3"))
            print("Sound found at %s" % sound.source)
            print("Sound is %.3f seconds" % sound.length)
            sound.play()
        else:
            print("Sound file not found or could not be loaded")

    def playSoundFile(self, soundFileName):
        global audio_playing
        # Construct the full path to the sound file
        sound_file = os.path.join('Sounds', soundFileName)

        sound = SoundLoader.load(sound_file)
        if sound:
            audio_playing = True
            sound.bind(on_stop=self.audioPlayingFalse)
            print("Sound found at %s" % sound.source)
            print("Sound is %.3f seconds" % sound.length)
            sound.play()
        else:
            print("Sound file not found or could not be loaded")

    def audioPlayingFalse(self, _):
        global audio_playing
        audio_playing = False
        print("Sound finished playing and audio_playing is: ", audio_playing)
        
    

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

AudioSegment.converter = which("ffmpeg")