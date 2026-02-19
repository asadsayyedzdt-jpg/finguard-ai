"""
Audit Trail Service

Logs all system activities for compliance and security
"""

import json
from datetime import datetime
import os

class AuditService:
    """
    Comprehensive audit trail logging
    
    Logs:
    - All API requests
    - Document verifications
    - Face comparisons
    - Transaction evaluations
    - Alert actions
    - User activities
    """
    
    def __init__(self):
        self.audit_dir = 'audit_logs'
        if not os.path.exists(self.audit_dir):
            os.makedirs(self.audit_dir)
        
        # Current log file
        date_str = datetime.now().strftime('%Y%m%d')
        self.log_file = os.path.join(self.audit_dir, f'audit_{date_str}.jsonl')
        
        print("✅ Audit Service initialized")
    
    def log_event(self, event_type, event_data, user_id=None, ip_address=None):
        """
        Log an audit event
        
        Args:
            event_type: Type of event (e.g., 'kyc_verification', 'transaction_check')
            event_data: Dictionary with event details
            user_id: User who performed the action
            ip_address: IP address of request
        """
        
        audit_entry = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'event_data': event_data,
            'user_id': user_id,
            'ip_address': ip_address
        }
        
        # Append to log file (JSONL format - one JSON per line)
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(audit_entry) + '\n')
    
    def log_kyc_verification(self, document_type, result, user_id=None):
        """Log KYC verification event"""
        self.log_event(
            'kyc_verification',
            {
                'document_type': document_type,
                'verification_result': result.get('validation', {}).get('is_valid'),
                'confidence': result.get('ocr_confidence'),
                'extracted_data': result.get('extracted_details')
            },
            user_id=user_id
        )
    
    def log_face_comparison(self, similarity, verdict, user_id=None):
        """Log face comparison event"""
        self.log_event(
            'face_comparison',
            {
                'similarity_percentage': similarity,
                'verdict': verdict,
                'is_match': 'MATCH' in verdict.upper()
            },
            user_id=user_id
        )
    
    def log_transaction_check(self, transaction_id, risk_score, flagged, user_id=None):
        """Log transaction check event"""
        self.log_event(
            'transaction_check',
            {
                'transaction_id': transaction_id,
                'risk_score': risk_score,
                'flagged': flagged
            },
            user_id=user_id
        )
    
    def log_alert_action(self, alert_id, action, user_id=None):
        """Log alert action (assign, resolve, etc.)"""
        self.log_event(
            'alert_action',
            {
                'alert_id': alert_id,
                'action': action
            },
            user_id=user_id
        )
    
    def get_audit_trail(self, start_date=None, end_date=None, event_type=None):
        """
        Retrieve audit trail
        
        Args:
            start_date: Filter from this date
            end_date: Filter until this date
            event_type: Filter by event type
        
        Returns:
            List of audit entries
        """
        
        entries = []
        
        # Read all log files
        for filename in os.listdir(self.audit_dir):
            if filename.startswith('audit_') and filename.endswith('.jsonl'):
                filepath = os.path.join(self.audit_dir, filename)
                
                with open(filepath, 'r') as f:
                    for line in f:
                        try:
                            entry = json.loads(line.strip())
                            
                            # Apply filters
                            if event_type and entry.get('event_type') != event_type:
                                continue
                            
                            # Date filtering would go here
                            
                            entries.append(entry)
                        except:
                            continue
        
        return entries