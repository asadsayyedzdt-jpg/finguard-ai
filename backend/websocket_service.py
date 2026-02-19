"""
WebSocket Service for Real-Time Updates

Sends live updates to connected clients when:
- New transaction is created
- Alert is generated
- Dashboard stats change
"""

from flask_socketio import SocketIO, emit
from datetime import datetime
from bson import ObjectId
import json

class WebSocketService:
    """
    WebSocket service for real-time updates
    """
    
    def __init__(self, app=None):
        """Initialize WebSocket service"""
        
        if app:
            self.socketio = SocketIO(app, cors_allowed_origins="*")
            self.setup_events()
            print("✅ WebSocket service initialized")
        else:
            self.socketio = None
    
    def setup_events(self):
        """Setup WebSocket event handlers"""
        
        @self.socketio.on('connect')
        def handle_connect():
            print(f"🔌 Client connected")
            emit('connection_response', {
                'status': 'connected', 
                'timestamp': datetime.now().isoformat()
            })
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            print(f"🔌 Client disconnected")
    
    def _ensure_json_serializable(self, data):
        """
        Ensure all data is JSON serializable
        Handles: datetime, ObjectId, numpy types
        """
        import numpy as np
        
        if isinstance(data, ObjectId):
            return str(data)
        elif isinstance(data, datetime):
            return data.isoformat()
        elif isinstance(data, (np.integer, np.floating)):
            return float(data)
        elif isinstance(data, np.bool_):
            return bool(data)
        elif isinstance(data, np.ndarray):
            return data.tolist()
        elif isinstance(data, dict):
            return {key: self._ensure_json_serializable(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._ensure_json_serializable(item) for item in data]
        elif isinstance(data, tuple):
            return tuple(self._ensure_json_serializable(item) for item in data)
        else:
            return data
    
    def emit_new_transaction(self, transaction_data):
        """Emit new transaction event to all clients"""
        
        if self.socketio:
            try:
                # Ensure data is JSON serializable
                safe_data = self._ensure_json_serializable(transaction_data)
                
                self.socketio.emit('new_transaction', {
                    'transaction': safe_data,
                    'timestamp': datetime.now().isoformat()
                })
                print(f"📤 Emitted new transaction: {safe_data.get('id')}")
            except Exception as e:
                print(f"❌ Error emitting transaction: {str(e)}")
    
    def emit_new_alert(self, alert_data):
        """Emit new alert event to all clients"""
        
        if self.socketio:
            try:
                # Ensure data is JSON serializable
                safe_data = self._ensure_json_serializable(alert_data)
                
                self.socketio.emit('new_alert', {
                    'alert': safe_data,
                    'timestamp': datetime.now().isoformat()
                })
                print(f"📤 Emitted new alert: {safe_data.get('id')}")
            except Exception as e:
                print(f"❌ Error emitting alert: {str(e)}")
    
    def emit_stats_update(self, stats_data):
        """Emit dashboard stats update"""
        
        if self.socketio:
            try:
                # Ensure data is JSON serializable
                safe_data = self._ensure_json_serializable(stats_data)
                
                self.socketio.emit('stats_update', {
                    'stats': safe_data,
                    'timestamp': datetime.now().isoformat()
                })
                print(f"📤 Emitted stats update")
            except Exception as e:
                print(f"❌ Error emitting stats: {str(e)}")
    
    def emit_alert_status_change(self, alert_id, new_status):
        """Emit alert status change"""
        
        if self.socketio:
            try:
                self.socketio.emit('alert_status_changed', {
                    'alert_id': str(alert_id),
                    'new_status': new_status,
                    'timestamp': datetime.now().isoformat()
                })
                print(f"📤 Emitted alert status change: {alert_id}")
            except Exception as e:
                print(f"❌ Error emitting alert status: {str(e)}")