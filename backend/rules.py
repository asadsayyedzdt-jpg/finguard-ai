"""
AML Rules Engine - Checks if transactions are suspicious
Simple and easy to understand!
"""

from datetime import datetime, timedelta

class AMLRules:
    """
    This class contains all the rules to check if a transaction is suspicious.
    Think of it like a security guard checking each transaction.
    """
    
    def __init__(self):
        # These are our thresholds (limits)
        self.large_amount = 200000  # ₹2 lakhs
        self.structuring_amount = 49999  # Just below ₹50k reporting limit
        
    def check_transaction(self, transaction, user_history):
        """
        Main function that checks a transaction against all rules.
        
        Args:
            transaction: The current transaction to check
            user_history: List of user's previous transactions
            
        Returns:
            Dictionary with risk_score, is_flagged, and reasons
        """
        risk_score = 0
        flags = []
        
        # Rule 1: Large Transaction
        if transaction['amount'] > self.large_amount:
            risk_score += 30
            flags.append({
                'rule': 'Large Transaction',
                'severity': 'MEDIUM',
                'message': f"Amount ₹{transaction['amount']:,} exceeds ₹{self.large_amount:,}"
            })
        
        # Rule 2: Unusual Time (11 PM to 5 AM)
        hour = datetime.now().hour
        if hour >= 23 or hour <= 5:
            risk_score += 15
            flags.append({
                'rule': 'Unusual Time',
                'severity': 'LOW',
                'message': f"Transaction at {hour}:00 hours (unusual time)"
            })
        
        # Rule 3: Round Amount (suspiciously round numbers)
        if transaction['amount'] >= 50000 and transaction['amount'] % 10000 == 0:
            risk_score += 20
            flags.append({
                'rule': 'Round Amount',
                'severity': 'LOW',
                'message': f"Suspiciously round amount: ₹{transaction['amount']:,}"
            })
        
        # Rule 4: Rapid Movement (multiple transactions quickly)
        if len(user_history) >= 3:
            risk_score += 40
            flags.append({
                'rule': 'Rapid Movement',
                'severity': 'HIGH',
                'message': f"{len(user_history)} transactions in short time"
            })
        
        # Rule 5: Structuring Pattern (multiple transactions just below limit)
        structuring_count = sum(1 for t in user_history 
                               if 45000 <= t.get('amount', 0) <= self.structuring_amount)
        if structuring_count >= 2:
            risk_score += 50
            flags.append({
                'rule': 'Structuring',
                'severity': 'CRITICAL',
                'message': f"{structuring_count} transactions near ₹50k limit (possible structuring)"
            })
        
        # Determine overall risk level
        if risk_score >= 70:
            risk_level = "CRITICAL"
        elif risk_score >= 50:
            risk_level = "HIGH"
        elif risk_score >= 30:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"
        
        return {
            'risk_score': min(risk_score, 100),  # Cap at 100
            'risk_level': risk_level,
            'is_flagged': risk_score >= 50,  # Flag if risk >= 50
            'flags': flags,
            'total_rules_checked': 5
        }


class KYCVerifier:
    """
    KYC Document Verification Logic
    Checks if uploaded documents are valid
    """
    
    def verify_pan(self, pan_number):
        """
        Verify PAN card number format
        Format: ABCDE1234F (5 letters, 4 numbers, 1 letter)
        """
        import re
        
        if not pan_number or len(pan_number) != 10:
            return {
                'valid': False,
                'message': 'PAN must be 10 characters'
            }
        
        # Check format using regex
        pattern = r'^[A-Z]{5}[0-9]{4}[A-Z]$'
        if re.match(pattern, pan_number.upper()):
            return {
                'valid': True,
                'message': 'PAN format is valid',
                'confidence': 95
            }
        else:
            return {
                'valid': False,
                'message': 'Invalid PAN format'
            }
    
    def verify_aadhaar(self, aadhaar_number):
        """
        Verify Aadhaar number format
        Format: 12 digits
        """
        # Remove spaces
        aadhaar = aadhaar_number.replace(' ', '')
        
        if not aadhaar.isdigit() or len(aadhaar) != 12:
            return {
                'valid': False,
                'message': 'Aadhaar must be 12 digits'
            }
        
        return {
            'valid': True,
            'message': 'Aadhaar format is valid',
            'confidence': 92
        }
    
    def verify_document(self, doc_type, doc_number):
        """
        Main verification function for any document
        """
        if doc_type.lower() == 'pan':
            return self.verify_pan(doc_number)
        elif doc_type.lower() == 'aadhaar':
            return self.verify_aadhaar(doc_number)
        else:
            return {
                'valid': False,
                'message': 'Unsupported document type'
            }

class HighRiskGeographyRule(AMLRules):
    """Flag transactions to/from high-risk countries"""
    
    def __init__(self):
        super().__init__("High-Risk Geography", "high")
        # Simplified high-risk indicators
        self.high_risk_keywords = ['offshore', 'international', 'foreign', 'overseas']
    
    def evaluate(self, transaction: Dict, user_history: List[Dict]) -> Tuple[int, Optional[Dict]]:
        location = transaction.get('location', '').lower()
        description = transaction.get('description', '').lower()
        
        # Check for high-risk keywords
        is_high_risk = any(keyword in location or keyword in description 
                          for keyword in self.high_risk_keywords)
        
        if is_high_risk:
            return 40, {
                'alert_type': 'high_risk_geography',
                'severity': self.severity,
                'title': 'High-Risk Geography',
                'description': 'Transaction involves high-risk or international location',
                'metadata': {
                    'location': location,
                    'risk_type': 'geographical'
                }
            }
        
        return 0, None


class NewRecipientRule(AMLRules):
    """Flag transactions to new/unknown recipients"""
    
    def __init__(self):
        super().__init__("New Recipient", "medium")
    
    def evaluate(self, transaction: Dict, user_history: List[Dict]) -> Tuple[int, Optional[Dict]]:
        recipient_id = transaction.get('recipient_id')
        
        if not recipient_id:
            return 0, None
        
        # Check if this recipient has been used before
        historical_recipients = {t.get('recipient_id') for t in user_history if t.get('recipient_id')}
        
        if recipient_id not in historical_recipients:
            amount = transaction.get('amount', 0)
            
            # Higher risk if large amount to new recipient
            if amount > 100000:
                return 35, {
                    'alert_type': 'new_recipient',
                    'severity': 'high',
                    'title': 'Large Amount to New Recipient',
                    'description': f'₹{amount:,.2f} sent to first-time recipient',
                    'metadata': {
                        'amount': amount,
                        'recipient_id': recipient_id,
                        'is_new': True
                    }
                }
            else:
                return 20, {
                    'alert_type': 'new_recipient',
                    'severity': self.severity,
                    'title': 'New Recipient',
                    'description': f'Transaction to first-time recipient',
                    'metadata': {
                        'recipient_id': recipient_id,
                        'is_new': True
                    }
                }
        
        return 0, None


class AmountSpikeRule(AMLRules):
    """Detect sudden spikes in transaction amounts"""
    
    def __init__(self):
        super().__init__("Amount Spike", "medium")
    
    def evaluate(self, transaction: Dict, user_history: List[Dict]) -> Tuple[int, Optional[Dict]]:
        current_amount = transaction.get('amount', 0)
        
        if len(user_history) < 5:
            return 0, None  # Not enough history
        
        # Calculate average of recent transactions
        recent_amounts = [t.get('amount', 0) for t in user_history[-10:]]
        avg_amount = sum(recent_amounts) / len(recent_amounts)
        
        # Check if current amount is significantly higher
        if current_amount > avg_amount * 5:  # 5x spike
            return 35, {
                'alert_type': 'amount_spike',
                'severity': self.severity,
                'title': 'Unusual Amount Spike',
                'description': f'Amount ₹{current_amount:,.2f} is {current_amount/avg_amount:.1f}x higher than average ₹{avg_amount:,.2f}',
                'metadata': {
                    'current_amount': current_amount,
                    'average_amount': avg_amount,
                    'spike_multiplier': current_amount / avg_amount
                }
            }
        
        return 0, None


class FrequencyAnomalyRule(AMLRules):
    """Detect unusual transaction frequency patterns"""
    
    def __init__(self):
        super().__init__("Frequency Anomaly", "medium")
    
    def evaluate(self, transaction: Dict, user_history: List[Dict]) -> Tuple[int, Optional[Dict]]:
        current_time = transaction.get('timestamp', datetime.utcnow())
        if isinstance(current_time, str):
            current_time = datetime.fromisoformat(current_time.replace('Z', '+00:00'))
        
        # Count transactions in last 24 hours
        day_ago = current_time - timedelta(days=1)
        today_count = sum(1 for t in user_history 
                         if t.get('timestamp', datetime.min) > day_ago)
        
        # Calculate average daily transaction count
        if len(user_history) >= 7:
            week_ago = current_time - timedelta(days=7)
            week_transactions = [t for t in user_history 
                               if t.get('timestamp', datetime.min) > week_ago]
            avg_daily = len(week_transactions) / 7
            
            # Flag if today is significantly above average
            if today_count > avg_daily * 3:
                return 30, {
                    'alert_type': 'frequency_anomaly',
                    'severity': self.severity,
                    'title': 'Unusual Transaction Frequency',
                    'description': f'{today_count} transactions today vs average of {avg_daily:.1f} per day',
                    'metadata': {
                        'today_count': today_count,
                        'average_daily': avg_daily
                    }
                }
        
        return 0, None


class ConsecutiveRoundAmountsRule(AMLRules):
    """Flag multiple consecutive round amount transactions"""
    
    def __init__(self):
        super().__init__("Consecutive Round Amounts", "high")
    
    def evaluate(self, transaction: Dict, user_history: List[Dict]) -> Tuple[int, Optional[Dict]]:
        current_amount = transaction.get('amount', 0)
        
        # Check if current is round
        if current_amount % 10000 != 0 or current_amount < 50000:
            return 0, None
        
        # Check recent history for round amounts
        current_time = transaction.get('timestamp', datetime.utcnow())
        if isinstance(current_time, str):
            current_time = datetime.fromisoformat(current_time.replace('Z', '+00:00'))
        
        day_ago = current_time - timedelta(days=1)
        recent_round = [t for t in user_history 
                       if t.get('timestamp', datetime.min) > day_ago 
                       and t.get('amount', 0) % 10000 == 0 
                       and t.get('amount', 0) >= 50000]
        
        if len(recent_round) >= 2:
            total = sum(t.get('amount', 0) for t in recent_round) + current_amount
            return 45, {
                'alert_type': 'consecutive_round_amounts',
                'severity': self.severity,
                'title': 'Multiple Round Amount Transactions',
                'description': f'{len(recent_round) + 1} round amount transactions in 24 hours, total ₹{total:,.2f}',
                'metadata': {
                    'count': len(recent_round) + 1,
                    'total_amount': total
                }
            }
        
        return 0, None


class SmallAmountTestingRule(AMLRules):
    """Detect small test transactions before large ones"""
    
    def __init__(self):
        super().__init__("Small Amount Testing", "low")
    
    def evaluate(self, transaction: Dict, user_history: List[Dict]) -> Tuple[int, Optional[Dict]]:
        current_amount = transaction.get('amount', 0)
        
        # Only check if current transaction is large
        if current_amount < 100000:
            return 0, None
        
        current_time = transaction.get('timestamp', datetime.utcnow())
        if isinstance(current_time, str):
            current_time = datetime.fromisoformat(current_time.replace('Z', '+00:00'))
        
        # Check for small transactions in last hour
        hour_ago = current_time - timedelta(hours=1)
        recent_small = [t for t in user_history 
                       if t.get('timestamp', datetime.min) > hour_ago 
                       and 1 <= t.get('amount', 0) <= 100]
        
        if len(recent_small) >= 1:
            return 25, {
                'alert_type': 'small_amount_testing',
                'severity': self.severity,
                'title': 'Possible Account Testing',
                'description': f'Small test transaction(s) followed by large amount ₹{current_amount:,.2f}',
                'metadata': {
                    'test_count': len(recent_small),
                    'large_amount': current_amount
                }
            }
        
        return 0, None


class WeekendTransactionRule(AMLRules):
    """Flag large transactions on weekends"""
    
    def __init__(self):
        super().__init__("Weekend Transaction", "low")
    
    def evaluate(self, transaction: Dict, user_history: List[Dict]) -> Tuple[int, Optional[Dict]]:
        timestamp = transaction.get('timestamp', datetime.utcnow())
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        
        amount = transaction.get('amount', 0)
        
        # Check if weekend (Saturday=5, Sunday=6)
        if timestamp.weekday() >= 5 and amount > 100000:
            return 15, {
                'alert_type': 'weekend_transaction',
                'severity': self.severity,
                'title': 'Large Weekend Transaction',
                'description': f'₹{amount:,.2f} transaction on weekend',
                'metadata': {
                    'day': timestamp.strftime('%A'),
                    'amount': amount
                }
            }
        
        return 0, None