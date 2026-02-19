"""
MongoDB Database Service

Handles all database operations for real-time data storage
"""

from pymongo import MongoClient, ASCENDING, DESCENDING
from datetime import datetime
import os
from bson import ObjectId
import json

class DatabaseService:
    """
    MongoDB service for persistent data storage
    
    Collections:
    - transactions: All transaction records
    - alerts: All alert records
    - users: User profiles
    - audit_logs: System audit trail
    - kyc_verifications: KYC verification records
    """
    
    def __init__(self, connection_string=None):
        """Initialize MongoDB connection"""
        
        # Use provided connection string or environment variable
        if connection_string is None:
            connection_string = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
        
        try:
            # Connect to MongoDB
            self.client = MongoClient(connection_string)
            
            # Database
            self.db = self.client['finguard_ai']
            
            # Collections
            self.transactions = self.db['transactions']
            self.alerts = self.db['alerts']
            self.users = self.db['users']
            self.audit_logs = self.db['audit_logs']
            self.kyc_verifications = self.db['kyc_verifications']
            
            # Create indexes for better performance
            self._create_indexes()
            
            # Test connection
            self.client.server_info()
            
            print("✅ MongoDB connected successfully")
            print(f"📦 Database: {self.db.name}")
            print(f"📊 Collections: {self.db.list_collection_names()}")
            
        except Exception as e:
            print(f"❌ MongoDB connection failed: {str(e)}")
            print("   Using in-memory storage as fallback")
            self.client = None
            self.db = None
    
    def _create_indexes(self):
        """Create database indexes for performance"""
        
        try:
            # Transaction indexes
            self.transactions.create_index([("timestamp", DESCENDING)])
            self.transactions.create_index([("user_id", ASCENDING)])
            self.transactions.create_index([("flagged", ASCENDING)])
            self.transactions.create_index([("risk_score", DESCENDING)])
            
            # Alert indexes
            self.alerts.create_index([("created_at", DESCENDING)])
            self.alerts.create_index([("status", ASCENDING)])
            self.alerts.create_index([("severity", ASCENDING)])
            self.alerts.create_index([("transaction_id", ASCENDING)])
            
            # User indexes
            self.users.create_index([("email", ASCENDING)], unique=True)
            self.users.create_index([("account_number", ASCENDING)], unique=True)
            
            # Audit log indexes
            self.audit_logs.create_index([("timestamp", DESCENDING)])
            self.audit_logs.create_index([("event_type", ASCENDING)])
            
            print("✅ Database indexes created")
            
        except Exception as e:
            print(f"⚠️  Warning: Could not create indexes: {str(e)}")
    
    def is_connected(self):
        """Check if MongoDB is connected"""
        return self.client is not None and self.db is not None
    
    # ============================================
    # TRANSACTION OPERATIONS
    # ============================================
    
    def save_transaction(self, transaction_data):
        """
        Save transaction to database
        
        Args:
            transaction_data: Dictionary with transaction details
        
        Returns:
            Inserted document ID
        """
        
        if not self.is_connected():
            return None
        
        try:
            # Add timestamp if not present
            if 'timestamp' not in transaction_data:
                transaction_data['timestamp'] = datetime.utcnow()
            
            # Convert string timestamp to datetime if needed
            if isinstance(transaction_data.get('timestamp'), str):
                transaction_data['timestamp'] = datetime.fromisoformat(
                    transaction_data['timestamp'].replace('Z', '+00:00')
                )
            
            # Insert transaction
            result = self.transactions.insert_one(transaction_data)
            
            print(f"✅ Transaction saved: {result.inserted_id}")
            
            return str(result.inserted_id)
            
        except Exception as e:
            print(f"❌ Error saving transaction: {str(e)}")
            return None
    
    def get_transactions(self, limit=100, skip=0, flagged_only=False, user_id=None):
        """Get transactions from database"""
        
        if not self.is_connected():
            return []
        
        try:
            # Build query
            query = {}
            if flagged_only:
                query['is_flagged'] = True
            if user_id:
                query['user_id'] = user_id
            
            # Get transactions
            cursor = self.transactions.find(query).sort('timestamp', DESCENDING).skip(skip).limit(limit)
            
            # Convert to list and handle ObjectId
            transactions = []
            for doc in cursor:
                # Convert ObjectId to string
                if '_id' in doc:
                    doc['_id'] = str(doc['_id'])
                # Convert datetime to ISO string
                if 'timestamp' in doc and isinstance(doc['timestamp'], datetime):
                    doc['timestamp'] = doc['timestamp'].isoformat()
                transactions.append(doc)
            
            return transactions
            
        except Exception as e:
            print(f"❌ Error getting transactions: {str(e)}")
            return []
    def get_transaction_by_id(self, transaction_id):
        """Get a specific transaction by ID"""
        
        if not self.is_connected():
            return None
        
        try:
            transaction = self.transactions.find_one({'id': transaction_id})
            if transaction:
                transaction['_id'] = str(transaction['_id'])
            return transaction
            
        except Exception as e:
            print(f"❌ Error getting transaction: {str(e)}")
            return None
    
    def get_user_transactions(self, user_id, limit=100):
        """Get all transactions for a specific user"""
        
        return self.get_transactions(limit=limit, user_id=user_id)
    
    # ============================================
    # ALERT OPERATIONS
    # ============================================
    
    def save_alert(self, alert_data):
        """Save alert to database"""
        
        if not self.is_connected():
            return None
        
        try:
            # Add timestamp if not present
            if 'created_at' not in alert_data:
                alert_data['created_at'] = datetime.utcnow()
            
            # Insert alert
            result = self.alerts.insert_one(alert_data)
            
            print(f"✅ Alert saved: {result.inserted_id}")
            
            return str(result.inserted_id)
            
        except Exception as e:
            print(f"❌ Error saving alert: {str(e)}")
            return None
    
    def get_alerts(self, limit=100, status=None, severity=None):
        """Get alerts from database"""
        
        if not self.is_connected():
            return []
        
        try:
            # Build query
            query = {}
            if status:
                query['status'] = status
            if severity:
                query['severity'] = severity
            
            # Get alerts
            cursor = self.alerts.find(query).sort('created_at', DESCENDING).limit(limit)
            
            # Convert to list
            alerts = []
            for doc in cursor:
                # Convert ObjectId to string
                if '_id' in doc:
                    doc['_id'] = str(doc['_id'])
                # Convert datetime to ISO string
                if 'created_at' in doc and isinstance(doc['created_at'], datetime):
                    doc['created_at'] = doc['created_at'].isoformat()
                alerts.append(doc)
            
            return alerts
            
        except Exception as e:
            print(f"❌ Error getting alerts: {str(e)}")
            return []
    
    def update_alert_status(self, alert_id, status, resolution_notes=None, resolved_by=None):
        """Update alert status"""
        
        if not self.is_connected():
            return False
        
        try:
            update_data = {
                'status': status,
                'updated_at': datetime.utcnow()
            }
            
            if resolution_notes:
                update_data['resolution_notes'] = resolution_notes
                update_data['resolved_at'] = datetime.utcnow()
                update_data['resolved_by'] = resolved_by
            
            result = self.alerts.update_one(
                {'id': alert_id},
                {'$set': update_data}
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            print(f"❌ Error updating alert: {str(e)}")
            return False
    
    # ============================================
    # USER OPERATIONS
    # ============================================
    
    def save_user(self, user_data):
        """Save or update user"""
        
        if not self.is_connected():
            return None
        
        try:
            # Check if user exists
            existing = self.users.find_one({'id': user_data.get('id')})
            
            if existing:
                # Update existing user
                result = self.users.update_one(
                    {'id': user_data.get('id')},
                    {'$set': user_data}
                )
                return user_data.get('id')
            else:
                # Insert new user
                result = self.users.insert_one(user_data)
                return str(result.inserted_id)
            
        except Exception as e:
            print(f"❌ Error saving user: {str(e)}")
            return None
    
    def get_user(self, user_id):
        """Get user by ID"""
        
        if not self.is_connected():
            return None
        
        try:
            user = self.users.find_one({'id': user_id})
            if user:
                user['_id'] = str(user['_id'])
            return user
            
        except Exception as e:
            print(f"❌ Error getting user: {str(e)}")
            return None
    
    # ============================================
    # KYC VERIFICATION OPERATIONS
    # ============================================
    
    def save_kyc_verification(self, kyc_data):
        """Save KYC verification record"""
        
        if not self.is_connected():
            return None
        
        try:
            if 'timestamp' not in kyc_data:
                kyc_data['timestamp'] = datetime.utcnow()
            
            result = self.kyc_verifications.insert_one(kyc_data)
            
            print(f"✅ KYC verification saved: {result.inserted_id}")
            
            return str(result.inserted_id)
            
        except Exception as e:
            print(f"❌ Error saving KYC verification: {str(e)}")
            return None
    
    def get_kyc_verifications(self, user_id=None, limit=50):
        """Get KYC verification records"""
        
        if not self.is_connected():
            return []
        
        try:
            query = {}
            if user_id:
                query['user_id'] = user_id
            
            cursor = self.kyc_verifications.find(query).sort('timestamp', DESCENDING).limit(limit)
            
            verifications = []
            for doc in cursor:
                doc['_id'] = str(doc['_id'])
                verifications.append(doc)
            
            return verifications
            
        except Exception as e:
            print(f"❌ Error getting KYC verifications: {str(e)}")
            return []
    
    # ============================================
    # AUDIT LOG OPERATIONS
    # ============================================
    
    def save_audit_log(self, log_data):
        """Save audit log entry"""
        
        if not self.is_connected():
            return None
        
        try:
            if 'timestamp' not in log_data:
                log_data['timestamp'] = datetime.utcnow()
            
            result = self.audit_logs.insert_one(log_data)
            
            return str(result.inserted_id)
            
        except Exception as e:
            print(f"❌ Error saving audit log: {str(e)}")
            return None
    
    def get_audit_logs(self, event_type=None, limit=100):
        """Get audit logs"""
        
        if not self.is_connected():
            return []
        
        try:
            query = {}
            if event_type:
                query['event_type'] = event_type
            
            cursor = self.audit_logs.find(query).sort('timestamp', DESCENDING).limit(limit)
            
            logs = []
            for doc in cursor:
                doc['_id'] = str(doc['_id'])
                logs.append(doc)
            
            return logs
            
        except Exception as e:
            print(f"❌ Error getting audit logs: {str(e)}")
            return []
    
    # ============================================
    # STATISTICS & ANALYTICS
    # ============================================
    
    def get_dashboard_stats(self):
        """Get dashboard statistics"""
        
        if not self.is_connected():
            return {
                'total_transactions': 0,
                'flagged_transactions': 0,
                'open_alerts': 0,
                'average_risk_score': 0,
                'total_volume': 0
            }
        
        try:
            # Total transactions
            total_transactions = self.transactions.count_documents({})
            
            # Flagged transactions
            flagged_transactions = self.transactions.count_documents({'flagged': True})
            
            # Open alerts
            open_alerts = self.alerts.count_documents({'status': 'open'})
            
            # Average risk score
            pipeline = [
                {'$group': {
                    '_id': None,
                    'avg_risk': {'$avg': '$risk_score'},
                    'total_volume': {'$sum': '$amount'}
                }}
            ]
            result = list(self.transactions.aggregate(pipeline))
            
            avg_risk_score = result[0]['avg_risk'] if result else 0
            total_volume = result[0]['total_volume'] if result else 0
            
            return {
                'total_transactions': total_transactions,
                'flagged_transactions': flagged_transactions,
                'open_alerts': open_alerts,
                'average_risk_score': round(avg_risk_score, 2),
                'total_volume': round(total_volume, 2),
                'flagging_rate': round((flagged_transactions / total_transactions * 100) if total_transactions > 0 else 0, 2)
            }
            
        except Exception as e:
            print(f"❌ Error getting stats: {str(e)}")
            return {}
    
    def get_transactions_by_date_range(self, start_date, end_date):
        """Get transactions within date range"""
        
        if not self.is_connected():
            return []
        
        try:
            query = {
                'timestamp': {
                    '$gte': start_date,
                    '$lte': end_date
                }
            }
            
            cursor = self.transactions.find(query).sort('timestamp', DESCENDING)
            
            transactions = []
            for doc in cursor:
                doc['_id'] = str(doc['_id'])
                transactions.append(doc)
            
            return transactions
            
        except Exception as e:
            print(f"❌ Error getting transactions by date: {str(e)}")
            return []
    
    # ============================================
    # UTILITY METHODS
    # ============================================
    
    def clear_all_data(self):
        """Clear all data (use with caution!)"""
        
        if not self.is_connected():
            return False
        
        try:
            self.transactions.delete_many({})
            self.alerts.delete_many({})
            self.users.delete_many({})
            self.kyc_verifications.delete_many({})
            self.audit_logs.delete_many({})
            
            print("✅ All data cleared")
            return True
            
        except Exception as e:
            print(f"❌ Error clearing data: {str(e)}")
            return False
    
    def get_collection_stats(self):
        """Get statistics for all collections"""
        
        if not self.is_connected():
            return {}
        
        try:
            return {
                'transactions': self.transactions.count_documents({}),
                'alerts': self.alerts.count_documents({}),
                'users': self.users.count_documents({}),
                'kyc_verifications': self.kyc_verifications.count_documents({}),
                'audit_logs': self.audit_logs.count_documents({})
            }
            
        except Exception as e:
            print(f"❌ Error getting collection stats: {str(e)}")
            return {}