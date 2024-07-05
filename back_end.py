import os

os.environ["KERAS_BACKEND"] = "tensorflow"

import shutil
import numpy as np

import tensorflow as tf
import keras

from pathlib import Path
from IPython.display import display, Audio

import random

## Constants
#DATASET_ROOT = "16000_pcm_speeches"
DATASET_ROOT = "16000_pcm_speeches_MODIFIED"

# The folders in which we will put the audio samples and the noise samples
AUDIO_SUBFOLDER = "audio"
NOISE_SUBFOLDER = "noise"

DATASET_AUDIO_PATH = os.path.join(DATASET_ROOT, AUDIO_SUBFOLDER)
DATASET_NOISE_PATH = os.path.join(DATASET_ROOT, NOISE_SUBFOLDER)

# Percentage of samples to use for validation
VALID_SPLIT = 0.1

# Seed to use when shuffling the dataset and the noise
SHUFFLE_SEED = 43

# The sampling rate to use.
# This is the one used in all the audio samples.
# We will resample all the noise to this sampling rate.
# This will also be the output size of the audio wave samples
# (since all samples are of 1 second long)
#SAMPLING_RATE = 16000
SAMPLING_RATE = 80000 # 5 seconds long

# The factor to multiply the noise with according to:
#   noisy_sample = sample + noise * prop * scale
#      where prop = sample_amplitude / noise_amplitude
SCALE = 0.5

BATCH_SIZE = 32
EPOCHS = 5

## Generate Dataset
def paths_and_labels_to_dataset(audio_paths, labels):
    """Constructs a dataset of audios and labels."""
    images = np.zeros((2, len(audio_paths), SAMPLING_RATE // 2, 1))
    label = np.zeros(len(audio_paths))
    
    for i in range(len(audio_paths)):
        
        if (i % 2 == 0):
            idx1 = random.randint(0, len(audio_paths) - 1)
            idx2 = random.randint(0, len(audio_paths) - 1)
            l = 1
            while (labels[idx1] != labels[idx2]):
                idx2 = random.randint(0, len(audio_paths) - 1)            
                
        else:
            idx1 = random.randint(0, len(audio_paths) - 1)
            idx2 = random.randint(0, len(audio_paths) - 1)
            l = 0
            while (labels[idx1] == labels[idx2]):
                idx2 = random.randint(0, len(audio_paths) - 1)

        images[0, i, :, :] = audio_to_fft(path_to_audio(audio_paths[idx1]))[:]
        images[1, i, :, :] = audio_to_fft(path_to_audio(audio_paths[idx2]))[:]
        label[i] = l

    return images, label

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

# Get the list of audio file paths along with their corresponding labels
class_names = os.listdir(DATASET_AUDIO_PATH)
print(
    "Our class names: {}".format(
        class_names,
    )
)

audio_paths = []
labels = []
for label, name in enumerate(class_names):
    print(
        "Processing speaker {}".format(
            name,
        )
    )
    dir_path = Path(DATASET_AUDIO_PATH) / name
    speaker_sample_paths = [
        os.path.join(dir_path, filepath)
        for filepath in os.listdir(dir_path)
        if filepath.endswith(".wav")
    ]
    audio_paths += speaker_sample_paths
    labels += [label] * len(speaker_sample_paths)

print(
    "Found {} files belonging to {} classes.".format(len(audio_paths), len(class_names))
)

# Shuffle
rng = np.random.RandomState(SHUFFLE_SEED)
rng.shuffle(audio_paths)
rng = np.random.RandomState(SHUFFLE_SEED)
rng.shuffle(labels)

# Split into training and validation
num_val_samples = int(VALID_SPLIT * len(audio_paths))
print("Using {} files for training.".format(len(audio_paths) - num_val_samples))
train_audio_paths = audio_paths[:-num_val_samples]
train_labels = labels[:-num_val_samples]

print("Using {} files for validation.".format(num_val_samples))
valid_audio_paths = audio_paths[-num_val_samples:]
valid_labels = labels[-num_val_samples:]

# Create 2 datasets, one for training and the other for validation
train_x, train_y = paths_and_labels_to_dataset(train_audio_paths, train_labels)
val_x, val_y = paths_and_labels_to_dataset(valid_audio_paths, valid_labels)

print(train_x.shape)
print(train_y.shape)
print(val_x.shape)
print(val_y.shape)

rng = np.random.RandomState(SHUFFLE_SEED)
rng.shuffle(train_x)
rng = np.random.RandomState(SHUFFLE_SEED)
rng.shuffle(train_y)
rng = np.random.RandomState(SHUFFLE_SEED)
rng.shuffle(val_x)
rng = np.random.RandomState(SHUFFLE_SEED)
rng.shuffle(val_y)

## Compile Model
def residual_block(x, filters, conv_num=3, activation="relu"):
    # Shortcut
    s = keras.layers.Conv1D(filters, 1, padding="same")(x)
    for i in range(conv_num - 1):
        x = keras.layers.Conv1D(filters, 3, padding="same")(x)
        x = keras.layers.Activation(activation)(x)
    x = keras.layers.Conv1D(filters, 3, padding="same")(x)
    x = keras.layers.Add()([x, s])
    x = keras.layers.Activation(activation)(x)
    return keras.layers.MaxPool1D(pool_size=2, strides=2)(x)


def build_model(dummy_input):
    x = residual_block(dummy_input, 16, 2)
    x = residual_block(x, 32, 2)
    x = residual_block(x, 64, 3)
    x = residual_block(x, 128, 3)
    x = residual_block(x, 128, 3)

    x = keras.layers.AveragePooling1D(pool_size=3, strides=3)(x)
    x = keras.layers.Flatten()(x)
    x = keras.layers.Dense(256, activation="relu")(x)
    x = keras.layers.Dense(128, activation="relu")(x)

    return x

DUMMY_INPUT_SHAPE = (SAMPLING_RATE // 2, 1)
EMBEDDING_SIZE = 32

dummy_input = keras.layers.Input(shape=DUMMY_INPUT_SHAPE)
base_network = build_model(dummy_input)
embedding_layer = keras.layers.Dense(EMBEDDING_SIZE, activation=None)(base_network)

base_network = keras.Model(dummy_input, embedding_layer, name='SiameseBranch')

input_a = keras.Input(DUMMY_INPUT_SHAPE, name='InputA')
input_b = keras.Input(DUMMY_INPUT_SHAPE, name='InputB')

embedding_a = base_network(input_a)
embedding_b = base_network(input_b)

def normalise_vector(vect):
    # get the magnitude for each vector in the batch
    mag = keras.ops.sqrt(keras.ops.sum(keras.ops.square(vect), axis=1))
    # repeat this, so we now have as many elements in mag as we do in vect
    mag = keras.ops.reshape(keras.ops.repeat(mag, vect.shape[1], axis=0), (-1, vect.shape[1]))
    # element wise division
    return keras.ops.divide(vect, mag)

def euclidean_distance(vects):
    x, y = vects
    x = normalise_vector(x) # this is just doing x = tf.math.l2_normalize(x, axis=1)
    y = normalise_vector(y) # this is just doing y = tf.math.l2_normalize(y, axis=1)

    sum_square = keras.ops.sum(keras.ops.square(keras.ops.subtract(x, y)), axis=1, keepdims=True)
    return keras.ops.sqrt(keras.ops.maximum(sum_square, keras.config.epsilon()))

def eucl_dist_output_shape(shapes):
    shape1, shape2 = shapes
    return (shape1[0], 1)

def contrastive_loss(y_true, y_pred):
    '''Contrastive loss from Hadsell-et-al.'06
    http://yann.lecun.com/exdb/publis/pdf/hadsell-chopra-lecun-06.pdf
    '''
    margin = 1
    square_pred = keras.ops.square(y_pred)
    margin_square = keras.ops.square(keras.ops.maximum(margin - y_pred, 0))
    return keras.ops.mean(y_true * square_pred + (1 - y_true) * margin_square)

distance = keras.layers.Lambda(euclidean_distance,
                  output_shape=eucl_dist_output_shape)([embedding_a, embedding_b])

model = keras.Model([input_a, input_b], distance)

model.summary()

# Compile the model using Adam's default learning rate
model.compile(
    optimizer="Adam",
    loss=contrastive_loss,
    metrics=["accuracy"],
)

# Add callbacks:
# 'EarlyStopping' to stop training when the model is not enhancing anymore
# 'ModelCheckPoint' to always keep the model that has the best val_accuracy
model_save_filename = "model.keras"

earlystopping_cb = keras.callbacks.EarlyStopping(patience=10, restore_best_weights=True)
mdlcheckpoint_cb = keras.callbacks.ModelCheckpoint(
    model_save_filename, monitor="val_loss", save_best_only=True
)

## Train Model
history = model.fit(
    [train_x[0], train_x[1]],
    train_y,
    epochs=EPOCHS,
    batch_size=BATCH_SIZE,
    validation_data=([val_x[0], val_x[1]], val_y),
    callbacks=[earlystopping_cb, mdlcheckpoint_cb],
)

print(model.evaluate((val_x, val_y)))

## Testing Model
SAMPLES_TO_DISPLAY = 10

test_ds = paths_and_labels_to_dataset(valid_audio_paths, valid_labels)
test_ds = test_ds.shuffle(buffer_size=BATCH_SIZE * 8, seed=SHUFFLE_SEED).batch(
    BATCH_SIZE
)

#test_ds = test_ds.map(
#    lambda x, y: (add_noise(x, noises, scale=SCALE), y),
#    num_parallel_calls=tf.data.AUTOTUNE,
#)

for audios, labels in test_ds.take(1):
    # Get the signal FFT
    ffts = audio_to_fft(audios)
    # Predict
    y_pred = model.predict(ffts)
    # Take random samples
    rnd = np.random.randint(0, BATCH_SIZE, SAMPLES_TO_DISPLAY)
    audios = audios.np()[rnd, :, :]
    labels = labels.np()[rnd]
    y_pred = np.argmax(y_pred, axis=-1)[rnd]

    for index in range(SAMPLES_TO_DISPLAY):
        # For every sample, print the true and predicted label
        # as well as run the voice with the noise
        print(
            "Speaker:\33{} {}\33[0m\tPredicted:\33{} {}\33[0m".format(
                "[92m" if labels[index] == y_pred[index] else "[91m",
                class_names[labels[index]],
                "[92m" if labels[index] == y_pred[index] else "[91m",
                class_names[y_pred[index]],
            )
        )
        display(Audio(audios[index, :, :].squeeze(), rate=SAMPLING_RATE))