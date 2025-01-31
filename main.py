import os
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.core.window import Window
from kivy.core.audio import SoundLoader
import threading

#pip install SpeechRecognition
import speech_recognition as sr
from kivy.clock import Clock
from kivy.properties import ObjectProperty
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle
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
playTwice = 0
assistantMenuOpen = True

assistanceFirstTime = True
audioTimeOut = 90
typingSubmit = False
additionalAssistancePlayed = False

same_user = True

# Load the Kv files
Builder.load_file('login.kv')
Builder.load_file('assistant.kv')

# Load the machine learning model
import keras
import os
import tensorflow as tf
import numpy as np

SAMPLING_RATE = 80000 # 5 seconds long

## Functions required to convert audio paths to np.array data
def path_to_audio(path):
    """Reads and decodes an audio file."""
    audio = tf.io.read_file(path)
    audio, _ = tf.audio.decode_wav(audio, 1, SAMPLING_RATE)
    return audio

def audio_to_fft(audio):
    # Since tf.signal.fft applies FFT on the innermost dimension,
    # we need to squeeze the dimensions and then expand them again
    # after FFT
    og_size = audio.shape[0]
    audio = tf.squeeze(audio, axis=-1)
    fft = tf.signal.fft(
        tf.cast(tf.complex(real=audio, imag=tf.zeros_like(audio)), tf.complex64)
    )
    fft = tf.expand_dims(fft, axis=-1)

    # Return the absolute value of the first half of the FFT
    # which represents the positive frequencies
    return tf.math.abs(fft[0:(og_size // 2), :])

def path_to_fft(path):
    return audio_to_fft(path_to_audio(path))

## Functions required by model layers
@keras.saving.register_keras_serializable()
def normalise_vector(vect):
    # get the magnitude for each vector in the batch
    mag = keras.ops.sqrt(keras.ops.sum(keras.ops.square(vect), axis=1))
    # repeat this, so we now have as many elements in mag as we do in vect
    mag = keras.ops.reshape(keras.ops.repeat(mag, vect.shape[1], axis=0), (-1, vect.shape[1]))
    # element wise division
    return keras.ops.divide(vect, mag)

@keras.saving.register_keras_serializable()
def euclidean_distance(vects):
    x, y = vects
    x = normalise_vector(x) # this is just doing x = tf.math.l2_normalize(x, axis=1)
    y = normalise_vector(y) # this is just doing y = tf.math.l2_normalize(y, axis=1)

    sum_square = keras.ops.sum(keras.ops.square(keras.ops.subtract(x, y)), axis=1, keepdims=True)
    return keras.ops.sqrt(keras.ops.maximum(sum_square, keras.config.epsilon()))

@keras.saving.register_keras_serializable()
def eucl_dist_output_shape(shapes):
    shape1, shape2 = shapes
    return (shape1[0], 1)

@keras.saving.register_keras_serializable()
def contrastive_loss(y_true, y_pred):
    '''Contrastive loss from Hadsell-et-al.'06
    http://yann.lecun.com/exdb/publis/pdf/hadsell-chopra-lecun-06.pdf
    '''
    margin = 1
    square_pred = keras.ops.square(y_pred)
    margin_square = keras.ops.square(keras.ops.maximum(margin - y_pred, 0))
    return keras.ops.mean(y_true * square_pred + (1 - y_true) * margin_square)

## Model
model = keras.models.load_model(os.path.join(os.getcwd(), "model.keras"), compile=False)

# Use this function to predict the distance between two samples
def predict_distance(samples):
    global model
    prediction = model.predict(samples)
    print("Prediction:", prediction)
    return prediction[0][0]

# Use THIS function to check if two samples are spoken by the same user
def spoken_by_same_user(samples):
    if predict_distance(samples) < 0.5:
        return True
    else:
        return False

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
    app = MyApp.get_running_app()
    assistant_screen = app.assistant_screen
    if not additionalAssistancePlayed:
        textToDisplay = playTransferText()
        print("Update additionalAssistance")
        assistant_screen.assistantText.text = (f"{textToDisplay}")
    match inputPrompt:
        case "balance":
            return os.path.join('Sounds', "BalanceRead.mp3")
        case "Transfer Money":
            return os.path.join('Sounds', "PayAmount.mp3")
        case "Pay electric bill":
            return os.path.join('Sounds', "PayElectricBill.mp3")
        case "goodbye":
            assistant_screen.assistantText.text = "Thank you, have a nice day."
            return os.path.join('Sounds', "Goodbye.mp3")
        case _:
            return os.path.join('Sounds', "IncorrectInput.mp3")



def waitingTyping():
    global typingSubmit
    audioTimeOut = 0
    while (typingSubmit):
        text = recorded_text
        useTextFunction(text)

def continuous_recording():
    global recorded_text
    global audio_playing
    global same_user
    print("Recording started...")
    recognizer = sr.Recognizer()
    microphone = sr.Microphone()
    
    while True:

        app = MyApp.get_running_app()
        current_screen = app.root.current
        assistant_screen = app.assistant_screen
        if not additionalAssistancePlayed:
            textToDisplay = playTransferText()
            assistant_screen.assistantText.text = (f"{textToDisplay}")
        if current_screen == 'assistant' and assistant_screen:
            playTransferSounds()

        if not audio_playing and not typingSubmit:
            with microphone as source:
                print("Listening...")
                audio = recognizer.listen(source)
                if (not typingSubmit):
                    assistant_screen.assistantText.text = "<The assistant is currently listening>"
                    assistant_screen.responseText.text = "<You are currently speaking>"
            try:
                # Extract raw audio data
                raw_audio = audio.get_raw_data()
                waveFilePath = os.path.join(os.getcwd(), 'Sounds', 'Thomas', 'thomas_new.wav')

                # Save the raw audio data to a wave file
                with wave.open(waveFilePath, 'wb') as f:
                    f.setnchannels(1)
                    f.setsampwidth(audio.sample_width)
                    f.setframerate(audio.sample_rate)
                    f.writeframes(raw_audio)

                # Crop audio data to 5 second clip
                waveFileNewBefore = path_to_fft(waveFilePath) # (N, 1), we want this to be (40000, 1)
                waveFileNew = np.zeros(shape=(40000, 1))

                # if recorded audio is larger, just transfer the last 5 seconds over
                if (waveFileNewBefore.shape[0] > SAMPLING_RATE // 2):
                    waveFileNew[:, :] = waveFileNewBefore[-40000:, :]
                # if recorded audio is smaller, transfer everything over
                else:
                    waveFileNew[:len(waveFileNewBefore), :] = waveFileNewBefore[:, :]

                waveFileOriginalBefore = path_to_fft(os.path.join(os.getcwd(), 'Sounds', 'Thomas', 'thomas_original.wav'))
                waveFileOriginal = np.zeros(shape=(40000, 1))

                # if recorded audio is larger, just transfer the last 5 seconds over
                if (waveFileOriginalBefore.shape[0] > SAMPLING_RATE // 2):
                    waveFileOriginal[:, :] = waveFileOriginalBefore[-40000:, :]
                # if recorded audio is smaller, transfer everything over
                else:
                    waveFileOriginal[:len(waveFileOriginalBefore), :] = waveFileOriginalBefore[:, :]

                print("New:", waveFileNew.shape)
                print("Original:", waveFileOriginal.shape)

                # reshape both to have a batch dimension of 1
                waveFileNew = tf.reshape(waveFileNew, (1, 40000, 1))
                waveFileOriginal = tf.reshape(waveFileOriginal, (1, 40000, 1))

                same_user = spoken_by_same_user([waveFileNew, waveFileOriginal])

                if same_user == True:
                    print("User Thomas has been authenticated.")
                else:
                    print("User is not Thomas! Authentication cancelled.")

                text = recognizer.recognize_google(audio)
                print("Recognized:", text)
                useTextFunction(text)
                
            except sr.UnknownValueError:
                print("Could not understand audio")
                assistant_screen.responseText.text = "<...>"
            except sr.RequestError as e:
                print("Could not request results; {0}".format(e))
                assistant_screen.responseText.text = "<...>"
            except FileNotFoundError as e:
                print(f"File not found error: {e}")
                assistant_screen.responseText.text = "<...>"
        
        




def useTextFunction(text):
    global typingSubmit
    global audioTimeOut
    print ("useTextFunction")
    app = MyApp.get_running_app()
    current_screen = app.root.current
    assistant_screen = app.assistant_screen
    if not (text == "password"):
        assistant_screen.responseText.text = (f"{text}")
    else:
        assistant_screen.responseText.text = (f"...")
    recorded_text = text
    
    login_screen = app.login_screen
    if current_screen == 'assistant' and assistant_screen:
        if insideOption == False:
            text_lower = text.lower()
            if not ("balance" in text_lower) and not ("pay" in text_lower) and not ("no" in text_lower or "exit" in text_lower or "log off" in text_lower):
                assistant_screen.assistantText.text = "I'm sorry, I don't understand"
        assistant_screen.optionSelect(text)  # Call method on AssistantScreen instance
    elif current_screen == 'login' and login_screen:
        login_screen.checkPassword(text)  # Call method on LoginScreen instance
    audioTimeOut = 90

class LoginScreen(Screen):
    global assistanceFirstTime
    assistanceFirstTime = True
    
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
        global same_user
        if passwordCorrect and same_user:
            playAudioPath = os.path.join('Sounds', "AuthenthicateMerge.mp3")
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
    assistantText = ObjectProperty(None)
    responseText = ObjectProperty(None)

    def submitTextInput(self):
        global recorded_text
        global typingSubmit
        app = MyApp.get_running_app()
        assistant_screen = app.assistant_screen
        recorded_text = assistant_screen.user_input.text
        print (f"Submitted text: {assistant_screen.user_input.text}")
        assistant_screen.user_input.text = ""
        typingSubmit = True
        waitingTyping()

    def log_off(self):
        self.manager.current = 'login'

    def optionSelect(self, text):
        global assistant_option
        global insideOption
        global assistant_option_state
        global assistanceFirstTime
        global assistantMenuOpen
        global typingSubmit
        print ("Inside optionSelect")
        typingSubmit = False
        app = MyApp.get_running_app()
        assistant_screen = app.assistant_screen
        
        if insideOption == False:
            print("Changing option")
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
                assistant_option = "wrong"
                insideOption = True
                
            
            print(f"Current assistant option: {assistant_option} with status of insideOption being: {insideOption}")
            assistant_screen.optionSelect(text)

        else:
            
            if assistant_option == "balance":
                self.chainReadBalance()
            elif assistant_option == "transfer":
                print (f"Given Text: {text}")
                self.chainTransfer(text)
            elif assistant_option == "pay bill":
                insideOption = False
            elif assistant_option == "logout":
                self.chainLogOut()
            elif assistant_option == "wrong":
                self.chainIncorrectInput()
            else:
                insideOption = False
                assistanceFirstTime = True
    
    def chainIncorrectInput(self):
        app = MyApp.get_running_app()
        assistant_screen = app.assistant_screen
        global insideOption
        global assistant_option_state
        global assistantMenuOpen
        self.playSoundFileIncorrect("IncorrectInput.mp3")
        assistant_screen.assistantText.text = "I'm sorry, I don't understand"
        assistant_option_state = 0


    def chainReadBalance(self):
        
        app = MyApp.get_running_app()
        assistant_screen = app.assistant_screen
        global insideOption
        global assistant_option_state
        global assistantMenuOpen
        
        print("inside chainReadBalance")

        assistant_option_state = 0
        insideOption = False
        assistantMenuOpen = False
        print("inside chainReadBalance")

        self.playSoundFile("BalanceRead.mp3")
        assistant_screen.assistantText.text = "Sure, you currently have $1234 in your account"
        

        print(f"insideOption: {insideOption} assistantMenuOpen: {assistantMenuOpen}")
        print(f"Checking if menu start can be played: {(insideOption == False) and assistantMenuOpen}")
        
        
    
    def chainTransfer(self, text):
        global insideOption
        global assistant_option_state
        global recorded_text
        global audio_playing
        global playTwice
        global assistantMenuOpen
        print("inside chainTransfer")
        
        if not audio_playing:
            print(f"assistant_option_state: {assistant_option_state} playTwice = {playTwice}")
            match assistant_option_state:
                case 0:
                    # Ask Name
                    print("State 0: Ask Name")
                    print(f"given text in state 0: {recorded_text.lower()}")
                    if (("darren" in text.lower() or "aaron" in text.lower()) or "aaron" in text.lower() or "Darren" in text.lower() or "baron" in text.lower()) and playTwice == 1:
                        print("Change state to 1")
                        playTwice = 0
                        assistant_option_state = 1
                    elif playTwice == 1:
                        print(f"given text is: {text}")
                        print("Change state to 5")
                        assistant_option_state = 6
                        playTwice = 0   
                case 1:
                    # Confirm Name
                    print("State 1: Confirm Name")
                    print("Change state to 2")
                    assistant_option_state = 2
                    playTwice = 0
                case 2:
                    print("State 2: Ask how much")
                    print("Change state to 3")
                    assistant_option_state = 3
                    playTwice = 0
                case 3:
                    # Confirm Amount
                    print("State 3: Confirm Amount")
                    print("Change state to 4")
                    assistant_option_state = 4
                    playTwice = 0
                case 4:
                    # Payment Name
                    print("State 4: Payment Name")
                    print("Change state to 5")
                    assistant_option_state = 5
                    playTwice = 0
                case 5:
                    # Finished
                    print("State 5: Finished")
                    print("Change state to 0")
                    assistant_option_state = 0
                    insideOption = False
                    audio_playing = True
                    playTwice = 0
                    assistantMenuOpen = True
                    
                    
                case 6:
                    # New Account
                    print("State 6: New Account/ Unrecognised Name")
                    assistant_option_state = 0
                    insideOption = False
                    self.playSoundFile("TransferNewAccount.mp3")
                    audio_playing = True
                    playTwice = 0
                    assistantMenuOpen = True
        else:
            print("Audio is playing, waiting for it to finish...")

    
    def chainLogOut(self):
        app = MyApp.get_running_app()
        assistant_screen = app.assistant_screen
        global insideOption
        global assistant_option_state
        global assistantMenuOpen
        assistant_option_state = 0
        insideOption = False
        
        print("inside chainLogOut")

        Clock.schedule_once(lambda dt: self.change_to_login_screen())
        self.manager.current = 'login'
        assistantMenuOpen = False
        self.playSoundFile ("goodbye.mp3")
        assistant_screen.assistantText.text = "Thank you, have a nice day."
        

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
        app = MyApp.get_running_app()
        assistant_screen = app.assistant_screen

        # Construct the full path to the sound file
        sound_file = os.path.join('Sounds', "IncorrectInput.mp3")
        print("Incorrect input for asssitant ")
        sound = SoundLoader.load(sound_file)
        if sound:
            audio_playing = True
            sound.bind(on_stop=self.playSoundFile("AdditionalAssistance.mp3"))
            assistant_screen.assistantText.text = "Is there anything else you would like assistance with?"
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

    
    
    def playSoundFileIncorrect(self, soundFileName):
        global audio_playing
        global assistantMenuOpen
        global insideOption
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
        
        

    def audioPlayingFalseIncorrect(self, _):
        global audio_playing
        audio_playing = False
        global assistantMenuOpen
        global insideOption
        global assistanceFirstTime
        print("Sound finished playing and audio_playing is: ", audio_playing)
        assistantMenuOpen = True
        insideOption = False
        playSoundFile("AdditionalAssistance.mp3")
        assistanceFirstTime = True



    def audioPlayingFalse(self, _):
        global audio_playing
        global insideOption
        global assistant_option_state
        global assistanceFirstTime
        global assistantMenuOpen
        global additionalAssistancePlayed
        assistant_option_state = 0
        insideOption = False
        

        app = MyApp.get_running_app()
        assistant_screen = app.assistant_screen
        
        
        print("Sound finished playing and audio_playing is: ", audio_playing)
        assistanceFirstTime = False
        if insideOption == False:
            assistantMenuOpen = True
            audio_playing = True
            if not additionalAssistancePlayed:
                
                print("Additional Assistance")
                additionalAssistancePlayed = True
                
            else:
                assistant_screen.assistantText.text = ("Is there anything else you would like assistance with?")
                additionalAssistancePlayed = False

        else:
            assistantMenuOpen = False
        audio_playing = False
        
def playTransferSounds():
    global insideOption
    global assistant_option
    global assistant_option_state
    global playTwice
    global assistanceFirstTime
    global assistantMenuOpen
    if (not insideOption) and assistantMenuOpen:
        if not assistanceFirstTime and not insideOption:
            print("Played Assistance Other Time")
            playSoundFile("AdditionalAssistance.mp3")
            
            assistantMenuOpen = False
    if (playTwice == 0 and assistant_option == "transfer"):
        match assistant_option_state:
                case 0:
                    playSoundFile("TransferQuestion.mp3")
                case 1:
                    playSoundFile("TransferDarrenSmith.mp3")
                case 2:
                    playSoundFile("PayAmount.mp3")
                case 3:
                    playSoundFile("Pay10Dollars.mp3")
                case 4:
                    playSoundFile("PaymentName.mp3")
                case 5:
                    playSoundFile("PayTransfer.mp3")
                case 6:
                    playSoundFile("TransferNewAccount.mp3")
        playTwice = playTwice + 1

def playTransferText():
    global insideOption
    global assistant_option
    global assistant_option_state
    global playTwice
    global assistanceFirstTime
    global assistantMenuOpen

    if not insideOption and assistantMenuOpen:
        if assistanceFirstTime:
            return "Your identity has been confirmed. Hello, Thomas. How can I assist you today?"
        else:
            return "Is there anything else you would like assistance with?"
    elif (playTwice == 1 and assistant_option == "transfer"):
        match assistant_option_state:
                case 0:
                    return "Sure, who would you like to transfer the money to?"
                case 1:
                    return "You want to transfer to Darren Smith, is this correct?"
                case 2:
                    return "Okay, how much do you want to transfer?"
                case 3:
                    return "$10, is this correct?"
                case 4:
                    return "Okay, what would you like to name this payment?"
                case 5:
                    return "Okay, transferring the payment"
                case 6:
                    return "I'm sorry, as this is a new account, you will have to contact the bank."
    elif(assistant_option == "balance"):
        return "Sure, you currently have $1234 in your account."

    
    else:
        return "Hello, Thomas. How can I assist you today?"

def playSoundFile(soundFileName):
        global audio_playing
        # Construct the full path to the sound file
        sound_file = os.path.join('Sounds', soundFileName)
        sound = SoundLoader.load(sound_file)
        if sound:
            audio_playing = True
            sound.bind(on_stop=audioPlayingFalse)
            print("Sound found at %s" % sound.source)
            print("Sound is %.3f seconds" % sound.length)
            sound.play()
        else:
            print("Sound file not found or could not be loaded")

def audioPlayingFalse(instance):
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