import os
import keras
import numpy as np
import tensorflow as tf
from main_copy import path_to_fft

model = keras.models.load_model(os.path.join(os.getcwd(), "model.keras"))

model.summary()
model.summary(expand_nested=True)

first_sample = path_to_fft(os.path.join(os.getcwd(), 'Sounds', 'Thomas', 'thomas_original.wav'))
second_sample = path_to_fft(os.path.join(os.getcwd(), 'Sounds', 'Thomas', 'thomas_original.wav'))

print("First: ", first_sample.shape)
print("Second: ", second_sample.shape)

prediction = model.predict([first_sample, second_sample])
print(prediction)