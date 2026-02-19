"""
Machine Learning Service

This service loads the trained ML model and uses it to predict
fraud probability for new transactions.
"""

import joblib
import numpy as np
from datetime import datetime
import os

class MLFraudDetector:
    """
    ML-based fraud detection service
    
    This wraps our trained Random Forest model and provides
    an easy-to-use interface for making predictions.
    """
    
    def __init__(self):
        """Load the trained model"""
        self.model = None
        self.feature_columns = None
        self.load_model()
    
    def load_model(self):
        """Load the trained model from disk"""
        try:
            model_path = 'fraud_detection_model.pkl'
            features_path = 'feature_columns.pkl'
            
            if os.path.exists(model_path) and os.path.exists(features_path):
                self.model = joblib.load(model_path)
                self.feature_columns = joblib.load(features_path)
                print("✅ ML model loaded successfully")
            else:
                print("⚠️  ML model not found. Run train_ml_model.py first.")
                print("   Falling back to rule-based detection only.")
        
        except Exception as e:
            print(f"⚠️  Error loading ML model: {str(e)}")
            print("   Falling back to rule-based detection only.")
    
    def extract_features(self, transaction, user_history):
        """
        Extract features from a transaction
        
        This converts raw transaction data into the format
        the ML model expects.
        """
        
        # Parse timestamp
        timestamp = transaction.get('timestamp', datetime.utcnow())
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        
        hour = timestamp.hour
        day_of_week = timestamp.weekday()
        
        # Calculate features
        amount = transaction.get('amount', 0)
        
        features = {
            'amount': amount,
            'hour': hour,
            'day_of_week': day_of_week,
            'is_weekend': 1 if day_of_week >= 5 else 0,
            'is_night': 1 if (hour >= 23 or hour <= 5) else 0,
            'amount_rounded': 1 if (amount % 10000 == 0 and amount >= 50000) else 0,
            'is_large': 1 if amount > 200000 else 0,
            'is_structuring_amount': 1 if (45000 <= amount <= 49999) else 0,
            'transactions_in_hour': len([
                t for t in user_history 
                if (timestamp - t.get('timestamp', datetime.min)).total_seconds() < 3600
            ]),
            'recipient_age_days': 30,  # Default: assume established recipient
            'is_new_recipient': 0,     # Default: not new
            'is_international': 1 if transaction.get('is_international', False) else 0
        }
        
        return features
    
    def predict(self, transaction, user_history):
        """
        Predict fraud probability for a transaction
        
        Returns:
            {
                'ml_fraud_probability': float (0-1),
                'ml_prediction': 'fraud' or 'legitimate',
                'ml_confidence': float (0-100),
                'ml_available': bool
            }
        """
        
        # If model not loaded, return default
        if self.model is None:
            return {
                'ml_fraud_probability': 0.5,
                'ml_prediction': 'unknown',
                'ml_confidence': 0,
                'ml_available': False
            }
        
        try:
            # Extract features
            features_dict = self.extract_features(transaction, user_history)
            
            # Convert to array in correct order
            feature_array = np.array([
                features_dict[col] for col in self.feature_columns
            ]).reshape(1, -1)
            
            # Make prediction
            fraud_probability = self.model.predict_proba(feature_array)[0][1]
            prediction = 'fraud' if fraud_probability > 0.5 else 'legitimate'
            confidence = max(fraud_probability, 1 - fraud_probability) * 100
            
            return {
                'ml_fraud_probability': round(fraud_probability, 4),
                'ml_prediction': prediction,
                'ml_confidence': round(confidence, 2),
                'ml_available': True,
                'ml_features_used': list(self.feature_columns)
            }
        
        except Exception as e:
            print(f"Error in ML prediction: {str(e)}")
            return {
                'ml_fraud_probability': 0.5,
                'ml_prediction': 'error',
                'ml_confidence': 0,
                'ml_available': False,
                'error': str(e)
            }
    
    def explain_prediction(self, transaction, user_history):
        """
        Explain why the model made its prediction
        
        Returns feature contributions to the decision
        """
        
        if self.model is None:
            return "ML model not available"
        
        try:
            features_dict = self.extract_features(transaction, user_history)
            feature_array = np.array([
                features_dict[col] for col in self.feature_columns
            ]).reshape(1, -1)
            
            # Get feature importances
            importances = self.model.feature_importances_
            
            # Calculate contribution of each feature
            contributions = []
            for i, col in enumerate(self.feature_columns):
                contributions.append({
                    'feature': col,
                    'value': features_dict[col],
                    'importance': round(importances[i], 4)
                })
            
            # Sort by importance
            contributions.sort(key=lambda x: x['importance'], reverse=True)
            
            return contributions[:5]  # Top 5 contributors
        
        except Exception as e:
            return f"Error explaining prediction: {str(e)}"