"""
Train Machine Learning Model for Fraud Detection

This script:
1. Loads the training data
2. Trains a Random Forest model
3. Evaluates its performance
4. Saves the trained model
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
import joblib

def train_model():
    """Train fraud detection model"""
    
    print("🤖 Training Fraud Detection Model...\n")
    
    # STEP 1: Load training data
    print("📂 Loading training data...")
    df = pd.read_csv('training_data.csv')
    print(f"   Loaded {len(df)} transactions")
    
    # STEP 2: Prepare features and labels
    print("\n🔧 Preparing features...")
    
    # Features: Everything except transaction_id, user_id, timestamp, and is_fraud
    feature_columns = [
        'amount', 'hour', 'day_of_week', 'is_weekend', 'is_night',
        'amount_rounded', 'is_large', 'is_structuring_amount',
        'transactions_in_hour', 'recipient_age_days', 'is_new_recipient',
        'is_international'
    ]
    
    X = df[feature_columns]  # Features (inputs)
    y = df['is_fraud']       # Labels (outputs - what we want to predict)
    
    print(f"   Features: {len(feature_columns)}")
    print(f"   Feature names: {feature_columns}")
    
    # STEP 3: Split data into training and testing sets
    print("\n✂️  Splitting data...")
    # 80% for training, 20% for testing
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    print(f"   Training set: {len(X_train)} transactions")
    print(f"   Testing set: {len(X_test)} transactions")
    
    # STEP 4: Train the model
    print("\n🌲 Training Random Forest model...")
    print("   (This creates 100 decision trees that vote on predictions)")
    
    model = RandomForestClassifier(
        n_estimators=100,      # 100 decision trees
        max_depth=10,          # Maximum depth of each tree
        min_samples_split=10,  # Minimum samples to split a node
        random_state=42,       # For reproducibility
        n_jobs=-1              # Use all CPU cores
    )
    
    model.fit(X_train, y_train)
    print("   ✅ Model trained!")
    
    # STEP 5: Evaluate the model
    print("\n📊 Evaluating model performance...")
    
    # Make predictions on test set
    y_pred = model.predict(X_test)
    y_pred_proba = model.predict_proba(X_test)[:, 1]  # Probability of fraud
    
    # Calculate metrics
    print("\n" + "="*60)
    print("CLASSIFICATION REPORT")
    print("="*60)
    print(classification_report(y_test, y_pred, 
                                target_names=['Legitimate', 'Fraud']))
    
    # Confusion Matrix
    cm = confusion_matrix(y_test, y_pred)
    print("\n" + "="*60)
    print("CONFUSION MATRIX")
    print("="*60)
    print(f"                Predicted Legit    Predicted Fraud")
    print(f"Actually Legit      {cm[0][0]:6d}            {cm[0][1]:6d}")
    print(f"Actually Fraud      {cm[1][0]:6d}            {cm[1][1]:6d}")
    
    # ROC AUC Score (higher is better, 1.0 is perfect)
    auc_score = roc_auc_score(y_test, y_pred_proba)
    print(f"\n🎯 ROC AUC Score: {auc_score:.4f}")
    print("   (1.0 = perfect, 0.5 = random guessing)")
    
    # Feature Importance
    print("\n" + "="*60)
    print("FEATURE IMPORTANCE")
    print("="*60)
    print("(Which features matter most for predictions?)\n")
    
    feature_importance = pd.DataFrame({
        'feature': feature_columns,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    for idx, row in feature_importance.iterrows():
        bar = '█' * int(row['importance'] * 100)
        print(f"{row['feature']:25s} {bar} {row['importance']:.4f}")
    
    # STEP 6: Save the model
    print("\n💾 Saving model...")
    joblib.dump(model, 'fraud_detection_model.pkl')
    joblib.dump(feature_columns, 'feature_columns.pkl')
    print("   ✅ Model saved to: fraud_detection_model.pkl")
    print("   ✅ Features saved to: feature_columns.pkl")
    
    print("\n" + "="*60)
    print("🎉 MODEL TRAINING COMPLETE!")
    print("="*60)
    print("\nYour ML model is ready to detect fraud in real-time!")
    
    return model, feature_columns

if __name__ == "__main__":
    train_model()