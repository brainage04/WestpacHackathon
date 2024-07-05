import keras
import os
import tensorflow as tf

model = keras.models.load_model(os.path.join(os.getcwd(), "model.keras"))

def predict_distance(first_sample, second_sample):
    prediction = model.predict([first_sample, second_sample])
    return prediction

SAMPLING_RATE = 80000 # 5 seconds long

def path_to_audio(path):
    """Reads and decodes an audio file."""
    audio = tf.io.read_file(path)
    audio, _ = tf.audio.decode_wav(audio, 1, SAMPLING_RATE)
    return audio

def audio_to_fft(audio):
    # Since tf.signal.fft applies FFT on the innermost dimension,
    # we need to squeeze the dimensions and then expand them again
    # after FFT
    audio = tf.squeeze(audio, axis=-1)
    fft = tf.signal.fft(
        tf.cast(tf.complex(real=audio, imag=tf.zeros_like(audio)), tf.complex64)
    )
    fft = tf.expand_dims(fft, axis=-1)

    # Return the absolute value of the first half of the FFT
    # which represents the positive frequencies
    return tf.math.abs(fft[0:(SAMPLING_RATE // 2), :])

def path_to_fft(path):
    return audio_to_fft(path_to_audio(path))

# example usage:
first_path = ""
second_path = ""

first_sample = path_to_fft(first_path)
second_sample = path_to_fft(second_path)

# if the distance between the two samples is really small (let's say 0.05)
if predict_distance(first_sample, second_sample) < 0.05:
    # users in both samples is identical, proceed
    pass
else:
    # user in both samples are NOT identical, do NOT proceed
    pass