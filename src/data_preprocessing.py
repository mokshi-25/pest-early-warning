"""
data_preprocessing.py
----------------------
Loads a pest image dataset organized as:

    data/train/<pest_class_name>/*.jpg
    data/val/<pest_class_name>/*.jpg
    data/test/<pest_class_name>/*.jpg

and builds tf.data pipelines with resizing, normalization, and augmentation
for the pest detection CNN.
"""

import os
import tensorflow as tf

IMG_SIZE = (224, 224)
BATCH_SIZE = 32
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def build_dataset(split: str, shuffle: bool = True) -> tf.data.Dataset:
    """Builds a labeled tf.data.Dataset for a given split ('train'/'val'/'test')."""
    split_dir = os.path.join(DATA_DIR, split)
    if not os.path.isdir(split_dir):
        raise FileNotFoundError(
            f"Expected dataset directory at {split_dir}. "
            "Place class-labeled image folders there (e.g. data/train/aphid/*.jpg)."
        )

    ds = tf.keras.utils.image_dataset_from_directory(
        split_dir,
        image_size=IMG_SIZE,
        batch_size=BATCH_SIZE,
        shuffle=shuffle,
        label_mode="categorical",
    )
    class_names = ds.class_names

    normalization = tf.keras.layers.Rescaling(1.0 / 255)
    ds = ds.map(lambda x, y: (normalization(x), y), num_parallel_calls=tf.data.AUTOTUNE)

    if split == "train":
        augmentation = tf.keras.Sequential([
            tf.keras.layers.RandomFlip("horizontal"),
            tf.keras.layers.RandomRotation(0.15),
            tf.keras.layers.RandomZoom(0.15),
            tf.keras.layers.RandomContrast(0.1),
        ])
        ds = ds.map(lambda x, y: (augmentation(x, training=True), y),
                    num_parallel_calls=tf.data.AUTOTUNE)

    ds = ds.prefetch(tf.data.AUTOTUNE)
    return ds, class_names


if __name__ == "__main__":
    train_ds, classes = build_dataset("train")
    print(f"Detected {len(classes)} pest classes: {classes}")
    for images, labels in train_ds.take(1):
        print("Batch image shape:", images.shape)
        print("Batch label shape:", labels.shape)
