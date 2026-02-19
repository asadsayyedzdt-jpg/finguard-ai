"""
Generate Training Data for ML Model

This script creates 5,000 synthetic transactions with realistic patterns.
Some are fraudulent, some are legitimate.
"""

import random
import json
from datetime import datetime, timedelta
import pandas as pd

def generate_training_data(num_samples=5000):
    """
    Generate synthetic transaction data
    
    We create two types of transactions:
    1. Legitimate (80%) - normal patterns
    2. Fraudulent (20%) - suspicious patterns
    """
    
    transactions = []
    
    # We'll create 100 fake users
    user_ids = [f"user{i:03d}" for i in range(100)]
    
    # Start date: 6 months ago
    start_date = datetime.now() - timedelta(days=180)
    
    print(f"Generating {num_samples} transactions...")
    
    for i in range(num_samples):
        # Randomly decide if this is fraud (20% chance)
        is_fraud = random.random() < 0.2
        
        if is_fraud:
            # FRAUDULENT TRANSACTION PATTERNS
            # These have suspicious characteristics
            
            # Higher amounts (₹1L - ₹10L)
            amount = random.uniform(100000, 1000000)
            
            # Often round numbers
            if random.random() < 0.6:  # 60% chance
                amount = round(amount / 10000) * 10000
            
            # Unusual hours (11 PM - 5 AM)
            hour = random.choice([23, 0, 1, 2, 3, 4, 5])
            
            # Often to new recipients
            recipient_age_days = random.randint(0, 30)  # New relationship
            
            # Rapid transactions (multiple in short time)
            transactions_in_hour = random.randint(3, 10)
            
            # Often international or high-risk locations
            is_international = random.random() < 0.4  # 40% chance
            
            # Structuring pattern (near ₹50k limit)
            is_structuring = random.random() < 0.3  # 30% chance
            if is_structuring:
                amount = random.uniform(45000, 49999)
        
        else:
            # LEGITIMATE TRANSACTION PATTERNS
            # These look normal
            
            # Lower amounts (₹100 - ₹50k)
            amount = random.uniform(100, 50000)
            
            # Normal hours (9 AM - 9 PM)
            hour = random.randint(9, 21)
            
            # Established recipients
            recipient_age_days = random.randint(30, 365)
            
            # Normal transaction frequency
            transactions_in_hour = random.randint(0, 2)
            
            # Mostly domestic
            is_international = random.random() < 0.1  # 10% chance
            
            # No structuring
            is_structuring = False
        
        # Create timestamp
        days_ago = random.randint(0, 180)
        transaction_date = start_date + timedelta(days=days_ago)
        transaction_date = transaction_date.replace(hour=hour)
        
        # Random user
        user_id = random.choice(user_ids)
        
        # Calculate features that ML model will use
        transaction = {
            # Basic info
            'transaction_id': f"TXN{i:06d}",
            'user_id': user_id,
            'amount': round(amount, 2),
            'timestamp': transaction_date.isoformat(),
            
            # Features for ML model
            'hour': hour,
            'day_of_week': transaction_date.weekday(),
            'is_weekend': 1 if transaction_date.weekday() >= 5 else 0,
            'is_night': 1 if (hour >= 23 or hour <= 5) else 0,
            'amount_rounded': 1 if (amount % 10000 == 0 and amount >= 50000) else 0,
            'is_large': 1 if amount > 200000 else 0,
            'is_structuring_amount': 1 if (45000 <= amount <= 49999) else 0,
            'transactions_in_hour': transactions_in_hour,
            'recipient_age_days': recipient_age_days,
            'is_new_recipient': 1 if recipient_age_days < 30 else 0,
            'is_international': 1 if is_international else 0,
            
            # Label (what we're trying to predict)
            'is_fraud': 1 if is_fraud else 0
        }
        
        transactions.append(transaction)
        
        # Progress indicator
        if (i + 1) % 500 == 0:
            print(f"Generated {i + 1}/{num_samples} transactions...")
    
    # Convert to DataFrame (like an Excel spreadsheet)
    df = pd.DataFrame(transactions)
    
    # Save to CSV file
    df.to_csv('training_data.csv', index=False)
    
    # Print statistics
    fraud_count = df['is_fraud'].sum()
    legit_count = len(df) - fraud_count
    
    print(f"\n✅ Training data generated!")
    print(f"Total transactions: {len(df)}")
    print(f"Fraudulent: {fraud_count} ({fraud_count/len(df)*100:.1f}%)")
    print(f"Legitimate: {legit_count} ({legit_count/len(df)*100:.1f}%)")
    print(f"Saved to: training_data.csv")
    
    return df

if __name__ == "__main__":
    generate_training_data(5000)