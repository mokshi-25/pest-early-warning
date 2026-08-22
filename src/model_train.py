"""
model_train.py
---------------
Trains a pest-detection CNN using MobileNetV2 transfer learning.
Saves the trained model + class index mapping to models/.
"""

import os
import json
import tensorflow as tf
from data_preprocessing import build_dataset, IMG_SIZE

MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "models")
os.makedirs(MODEL_DIR, exist_ok=True)


def build_model(num_classes: int) -> tf.keras.Model:
    base_model = tf.keras.applications.MobileNetV2(
        input_shape=IMG_SIZE + (3,),
        include_top=False,
        weights="imagenet",
    )
    base_model.trainable = False  # freeze backbone for initial training

    inputs = tf.keras.Input(shape=IMG_SIZE + (3,))
    x = base_model(inputs, training=False)
    x = tf.keras.layers.GlobalAveragePooling2D()(x)
    x = tf.keras.layers.Dropout(0.3)(x)
    x = tf.keras.layers.Dense(128, activation="relu")(x)
    x = tf.keras.layers.Dropout(0.2)(x)
    outputs = tf.keras.layers.Dense(num_classes, activation="softmax")(x)

    model = tf.keras.Model(inputs, outputs)
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=1e-3),
        loss="categorical_crossentropy",
        metrics=["accuracy"],
    )
    return model, base_model


def train(epochs: int = 15, fine_tune_epochs: int = 5):
    train_ds, class_names = build_dataset("train")
    val_ds, _ = build_dataset("val", shuffle=False)

    model, base_model = build_model(num_classes=len(class_names))

    callbacks = [
        tf.keras.callbacks.EarlyStopping(patience=4, restore_best_weights=True),
        tf.keras.callbacks.ModelCheckpoint(
            os.path.join(MODEL_DIR, "pest_cnn_model.h5"),
            save_best_only=True,
        ),
    ]

    print("--- Phase 1: training classification head (frozen backbone) ---")
    model.fit(train_ds, validation_data=val_ds, epochs=epochs, callbacks=callbacks)

    print("--- Phase 2: fine-tuning top backbone layers ---")
    base_model.trainable = True
    for layer in base_model.layers[:-30]:
        layer.trainable = False  # keep most of backbone frozen
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=1e-5),
        loss="categorical_crossentropy",
        metrics=["accuracy"],
    )
    model.fit(train_ds, validation_data=val_ds, epochs=fine_tune_epochs, callbacks=callbacks)

    model.save(os.path.join(MODEL_DIR, "pest_cnn_model.h5"))
    with open(os.path.join(MODEL_DIR, "class_names.json"), "w") as f:
        json.dump(class_names, f)

    print(f"Model + class map saved to {MODEL_DIR}")
    return model, class_names


if __name__ == "__main__":
    train()
