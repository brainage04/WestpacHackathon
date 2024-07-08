import os
import keras
import numpy as np
import tensorflow as tf
from main import path_to_fft

model = keras.models.load_model(os.path.join(os.getcwd(), "model.keras"))

model.summary()
model.summary(expand_nested=True)

first_sample = path_to_fft(os.path.join(os.getcwd(), 'Sounds', 'Thomas', 'thomas_original.wav'))
second_sample = path_to_fft(os.path.join(os.getcwd(), 'Sounds', 'Thomas', 'thomas_original.wav'))

first_sample = tf.reshape(first_sample, (1, 40000, 1))
second_sample = tf.reshape(second_sample, (1, 40000, 1))

print("First: ", first_sample.shape)
print("Second: ", second_sample.shape)

prediction = model.predict([first_sample, second_sample])
print(prediction)