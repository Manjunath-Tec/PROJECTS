"""
Arecanut Disease Detection Model Training Script
Uses Transfer Learning with MobileNetV2 for fast and accurate training
"""

import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.applications import MobileNetV2
import numpy as np
import os

# Set seeds for reproducibility
np.random.seed(42)
tf.random.set_seed(42)

# Configuration
IMG_HEIGHT = 224
IMG_WIDTH = 224
BATCH_SIZE = 32
EPOCHS_PHASE1 = 15
EPOCHS_PHASE2 = 10

# Paths
TRAIN_DIR = "Dataset/Arecanut_dataset/Arecanut_dataset/train"
TEST_DIR = "Dataset/Arecanut_dataset/Arecanut_dataset/test"
MODEL_OUTPUT = "best_arecanut_fast_model.h5"

def prepare_data():
    """Prepare data generators with augmentation"""
    
    # Training data augmentation
    train_datagen = ImageDataGenerator(
        rescale=1./255,
        rotation_range=30,
        width_shift_range=0.2,
        height_shift_range=0.2,
        shear_range=0.2,
        zoom_range=0.2,
        horizontal_flip=True,
        fill_mode='nearest'
    )
    
    # Test data (only rescaling)
    test_datagen = ImageDataGenerator(rescale=1./255)
    
    train_generator = train_datagen.flow_from_directory(
        TRAIN_DIR,
        target_size=(IMG_HEIGHT, IMG_WIDTH),
        batch_size=BATCH_SIZE,
        class_mode='categorical',
        shuffle=True
    )
    
    test_generator = test_datagen.flow_from_directory(
        TEST_DIR,
        target_size=(IMG_HEIGHT, IMG_WIDTH),
        batch_size=BATCH_SIZE,
        class_mode='categorical',
        shuffle=False
    )
    
    return train_generator, test_generator

def build_model(num_classes):
    """Build model using transfer learning with MobileNetV2"""
    
    # Load pre-trained MobileNetV2 (trained on ImageNet)
    base_model = MobileNetV2(
        input_shape=(IMG_HEIGHT, IMG_WIDTH, 3),
        include_top=False,
        weights='imagenet'
    )
    
    # Freeze base model initially
    base_model.trainable = False
    
    # Build model
    model = keras.Sequential([
        base_model,
        layers.GlobalAveragePooling2D(),
        layers.BatchNormalization(),
        layers.Dropout(0.3),
        layers.Dense(256, activation='relu'),
        layers.BatchNormalization(),
        layers.Dropout(0.4),
        layers.Dense(128, activation='relu'),
        layers.Dropout(0.3),
        layers.Dense(num_classes, activation='softmax')
    ])
    
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=0.001),
        loss='categorical_crossentropy',
        metrics=['accuracy']
    )
    
    return model, base_model

def train_model():
    """Main training function"""
    
    print("=" * 60)
    print("ARECANUT DISEASE DETECTION - MODEL TRAINING")
    print("Using Transfer Learning with MobileNetV2")
    print("=" * 60)
    
    # Prepare data
    print("\n[1/5] Preparing data...")
    train_gen, test_gen = prepare_data()
    
    num_classes = len(train_gen.class_indices)
    class_names = list(train_gen.class_indices.keys())
    
    print(f"\nFound {num_classes} classes:")
    # Print the actual class indices from Keras (this is the correct mapping)
    print("Class indices (from Keras):")
    for class_name, idx in sorted(train_gen.class_indices.items(), key=lambda x: x[1]):
        print(f"  {idx}: {class_name}")
    
    # Save class indices to JSON for reference
    import json
    class_indices_path = "class_indices.json"
    with open(class_indices_path, 'w') as f:
        json.dump(train_gen.class_indices, f, indent=2)
    print(f"\nClass indices saved to: {class_indices_path}")
    
    print(f"\nTraining samples: {train_gen.n}")
    print(f"Test samples: {test_gen.n}")
    
    # Build model
    print("\n[2/5] Building model...")
    model, base_model = build_model(num_classes)
    print(f"Total parameters: {model.count_params():,}")
    
    # Callbacks
    callbacks = [
        keras.callbacks.EarlyStopping(
            monitor='val_loss',
            patience=5,
            restore_best_weights=True,
            verbose=1
        ),
        keras.callbacks.ReduceLROnPlateau(
            monitor='val_loss',
            factor=0.5,
            patience=3,
            min_lr=1e-7,
            verbose=1
        ),
        keras.callbacks.ModelCheckpoint(
            MODEL_OUTPUT,
            monitor='val_accuracy',
            save_best_only=True,
            verbose=1
        )
    ]
    
    # Phase 1: Train with frozen base
    print("\n[3/5] Phase 1: Training with frozen base model...")
    print(f"Training for {EPOCHS_PHASE1} epochs...")
    
    model.fit(
        train_gen,
        validation_data=test_gen,
        epochs=EPOCHS_PHASE1,
        callbacks=callbacks,
        verbose=1
    )
    
    # Phase 2: Fine-tuning
    print("\n[4/5] Phase 2: Fine-tuning last 30 layers...")
    
    # Unfreeze the last 30 layers of base model
    base_model.trainable = True
    for layer in base_model.layers[:-30]:
        layer.trainable = False
    
    # Recompile with lower learning rate
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=0.0001),
        loss='categorical_crossentropy',
        metrics=['accuracy']
    )
    
    print(f"Training for {EPOCHS_PHASE2} more epochs...")
    
    model.fit(
        train_gen,
        validation_data=test_gen,
        epochs=EPOCHS_PHASE2,
        callbacks=callbacks,
        verbose=1
    )
    
    # Evaluate
    print("\n[5/5] Evaluating model...")
    results = model.evaluate(test_gen)
    print(f"\nFinal Test Loss: {results[0]:.4f}")
    print(f"Final Test Accuracy: {results[1]:.4f} ({results[1]*100:.2f}%)")
    
    # Copy model to backend folder as well
    import shutil
    if os.path.exists(MODEL_OUTPUT):
        shutil.copy(MODEL_OUTPUT, f"backend/{MODEL_OUTPUT}")
        print(f"\nModel copied to backend/{MODEL_OUTPUT}")
    
    print("\n" + "=" * 60)
    print("TRAINING COMPLETE!")
    print(f"Model saved as: {MODEL_OUTPUT}")
    print("=" * 60)
    
    return model

if __name__ == "__main__":
    train_model()
