"""
predict.py
----------
Runs pest detection inference on a single image (or batch) using the trained
model saved by model_train.py.

Usage:
    python predict.py --image path/to/leaf.jpg
"""

import os
import json
import argparse
import numpy as np
import tensorflow as tf

MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "models")
IMG_SIZE = (224, 224)


def load_model_and_classes():
    model_path = os.path.join(MODEL_DIR, "pest_cnn_model.h5")
    classes_path = os.path.join(MODEL_DIR, "class_names.json")
    if not os.path.exists(model_path):
        raise FileNotFoundError(
            f"No trained model found at {model_path}. Run model_train.py first."
        )
    model = tf.keras.models.load_model(model_path)
    with open(classes_path) as f:
        class_names = json.load(f)
    return model, class_names


def predict_image(image_path: str, model=None, class_names=None):
    if model is None or class_names is None:
        model, class_names = load_model_and_classes()

    img = tf.keras.utils.load_img(image_path, target_size=IMG_SIZE)
    arr = tf.keras.utils.img_to_array(img) / 255.0
    arr = np.expand_dims(arr, axis=0)

    preds = model.predict(arr, verbose=0)[0]
    top_idx = int(np.argmax(preds))
    result = {
        "pest_class": class_names[top_idx],
        "confidence": float(preds[top_idx]),
        "all_scores": {class_names[i]: float(preds[i]) for i in range(len(class_names))},
    }
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", required=True, help="Path to the leaf/field image")
    args = parser.parse_args()

    output = predict_image(args.image)
    print(f"Detected pest: {output['pest_class']} (confidence: {output['confidence']:.2%})")
