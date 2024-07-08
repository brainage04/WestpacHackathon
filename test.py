import os
import keras
from main_copy import path_to_fft

model = keras.models.load_model(os.path.join(os.getcwd(), "model.keras"), compile=False)

first_sample = path_to_fft(os.path.join(os.getcwd(), 'Sounds', 'Thomas', 'thomas_original.wav'))
second_sample = path_to_fft(os.path.join(os.getcwd(), 'Sounds', 'Thomas', 'thomas_original.wav'))

prediction = model.predict([first_sample, second_sample])
print(prediction)