import keras
import os

model = keras.models.load_model(os.path.join(os.getcwd(), "model.keras"))

def predict_distance(first_sample, second_sample):
    prediction = model.predict([first_sample, second_sample])
    return prediction

# example usage:
# if predict_distance(first_sample, second_sample) < 0.02:
#     # user is identical, proceed
# else:
#     # user is not identical, do not proceed