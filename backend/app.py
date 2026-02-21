"""
FinGuard AI - Backend Server
This is the main server that handles all requests from the frontend.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from rules import AMLRules, KYCVerifier
from datetime import datetime
import json
import os
from ml_service import MLFraudDetector
from werkzeug.utils import secure_filename
from ocr_service import OCRService
import os
import logging  # ← ADD THIS LINE
from face_recognition_service import FaceRecognitionService
from chatbot_service import IntelligentChatbot, prepare_chatbot_context
from report_service import ReportService
from audit_service import AuditService
from database_service import DatabaseService
from websocket_service import WebSocketService
from config import settings

# Create Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = settings.SECRET_KEY
CORS(app)  # Allow frontend to talk to backend


db_service = DatabaseService()
ws_service = WebSocketService(app)
aml_engine = AMLRules()
kyc_verifier = KYCVerifier()
ml_detector = MLFraudDetector()
ocr_service = OCRService()
face_service = FaceRecognitionService()
chatbot = IntelligentChatbot()
report_service = ReportService()
audit_service = AuditService()


UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'bmp', 'tiff'}
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# In-memory storage (  no database needed)
transactions = []
alerts = []
users = {}

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/api/kyc/ocr', methods=['POST'])
def ocr_document():
    """
    Extract text from uploaded document image using OCR
    
    Expected: multipart/form-data with 'document' file
    Optional: 'document_type' (pan/aadhaar/auto)
    """
    try:
        # Check if file was uploaded
        if 'document' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file uploaded'
            }), 400
        
        file = request.files['document']
        
        # Check if file has a name
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400
        
        # Check if file type is allowed
        if not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'error': f'File type not allowed. Allowed types: {", ".join(ALLOWED_EXTENSIONS)}'
            }), 400
        
        # Save file securely
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        logging.info(f"File uploaded: {filepath}")
        
        # Get document type (optional)
        document_type = request.form.get('document_type', 'auto')
        
        # Process with OCR
        result = ocr_service.process_document(filepath, document_type)
        
        # Add file info to result
        result['uploaded_file'] = filename
        result['file_size'] = os.path.getsize(filepath)
        
        return jsonify({
            'success': True,
            'data': result
        })
        
    except Exception as e:
        logging.error(f"OCR error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
            # In the OCR endpoint, after successful verification:
    audit_service.log_kyc_verification(
        document_type=result['document_type'],
        result=result,
        user_id='system'
    )

# Load sample data if exists
def load_sample_data():
    """Load sample data for demo purposes"""
    data_file = '../data/sample_data.json'
    if os.path.exists(data_file):
        with open(data_file, 'r') as f:
            data = json.load(f)
            return data
    return {'transactions': [], 'users': {}}

sample_data = load_sample_data()
transactions = sample_data.get('transactions', [])
users = sample_data.get('users', {})

@app.route('/api/reports/generate', methods=['POST'])
def generate_report():
    """Generate PDF compliance report"""
    try:
        print("\n📄 Generating compliance report...")
        
        # Get dashboard stats
        stats = {
            'total_transactions': len(transactions),
            'flagged_transactions': sum(1 for t in transactions if t.get('flagged')),
            'open_alerts': sum(1 for a in alerts if a.get('status') == 'OPEN'),
            'average_risk_score': sum(t.get('risk_score', 0) for t in transactions) / len(transactions) if transactions else 0,
            'total_volume': sum(t.get('amount', 0) for t in transactions),
            'flagging_rate': (sum(1 for t in transactions if t.get('flagged')) / len(transactions) * 100) if transactions else 0
        }
        
        # Generate report
        report_path = report_service.generate_transaction_report(
            transactions,
            alerts,
            stats
        )
        
        # Log audit event
        audit_service.log_event('report_generated', {
            'report_type': 'transaction_report',
            'report_path': report_path
        })
        
        print(f"✅ Report generated: {report_path}")
        
        return jsonify({
            'success': True,
            'data': {
                'report_path': report_path,
                'filename': os.path.basename(report_path),
                'timestamp': datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        print(f"❌ Error generating report: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/audit/trail', methods=['GET'])
def get_audit_trail():
    """Get audit trail"""
    try:
        event_type = request.args.get('event_type')
        
        entries = audit_service.get_audit_trail(event_type=event_type)
        
        return jsonify({
            'success': True,
            'data': {
                'entries': entries[-50:],  # Last 50 entries
                'total_count': len(entries)
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/kyc/face-compare', methods=['POST'])
def compare_faces():
    """
    Compare faces in two images for identity verification
    """
    try:
        print("\n" + "="*60)
        print("FACE COMPARISON REQUEST RECEIVED")
        print("="*60)
        
        # Check if both files were uploaded
        if 'document_image' not in request.files:
            print("❌ Error: document_image not in request")
            return jsonify({
                'success': False,
                'error': 'Document image not uploaded'
            }), 400
        
        if 'selfie_image' not in request.files:
            print("❌ Error: selfie_image not in request")
            return jsonify({
                'success': False,
                'error': 'Selfie image not uploaded'
            }), 400
        
        doc_file = request.files['document_image']
        selfie_file = request.files['selfie_image']
        
        print(f"📁 Received files:")
        print(f"   Document: {doc_file.filename}")
        print(f"   Selfie: {selfie_file.filename}")
        
        # Check filenames
        if doc_file.filename == '' or selfie_file.filename == '':
            print("❌ Error: Empty filename")
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400
        
        # Check file types
        if not allowed_file(doc_file.filename) or not allowed_file(selfie_file.filename):
            print(f"❌ Error: Invalid file type")
            return jsonify({
                'success': False,
                'error': f'File type not allowed. Allowed types: {", ".join(ALLOWED_EXTENSIONS)}'
            }), 400
        
        # Save files securely
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        doc_filename = secure_filename(doc_file.filename)
        doc_filename = f"{timestamp}_doc_{doc_filename}"
        doc_filepath = os.path.join(app.config['UPLOAD_FOLDER'], doc_filename)
        
        print(f"💾 Saving document to: {doc_filepath}")
        doc_file.save(doc_filepath)
        
        if not os.path.exists(doc_filepath):
            print(f"❌ Error: Failed to save document file")
            return jsonify({
                'success': False,
                'error': 'Failed to save document file'
            }), 500
        
        print(f"✅ Document saved successfully")
        
        selfie_filename = secure_filename(selfie_file.filename)
        selfie_filename = f"{timestamp}_selfie_{selfie_filename}"
        selfie_filepath = os.path.join(app.config['UPLOAD_FOLDER'], selfie_filename)
        
        print(f"💾 Saving selfie to: {selfie_filepath}")
        selfie_file.save(selfie_filepath)
        
        if not os.path.exists(selfie_filepath):
            print(f"❌ Error: Failed to save selfie file")
            return jsonify({
                'success': False,
                'error': 'Failed to save selfie file'
            }), 500
        
        print(f"✅ Selfie saved successfully")
        
        # Compare faces
        print(f"\n🔍 Starting face comparison...")
        result = face_service.compare_faces(doc_filepath, selfie_filepath)
        
        print(f"✅ Face comparison completed")
        
        # Check if comparison was successful
        if not result.get('success', False):
            error_msg = result.get('error', 'Unknown error during face comparison')
            print(f"❌ Face comparison failed: {error_msg}")
            return jsonify({
                'success': False,
                'error': error_msg
            }), 400
        
        # Create comparison image
        print(f"\n🖼️  Creating comparison image...")
        comparison_filename = f"{timestamp}_comparison.jpg"
        comparison_filepath = os.path.join(app.config['UPLOAD_FOLDER'], comparison_filename)
        
        try:
            face_service.create_comparison_image(doc_filepath, selfie_filepath, comparison_filepath)
            print(f"✅ Comparison image created")
        except Exception as e:
            print(f"⚠️  Warning: Could not create comparison image: {str(e)}")
            comparison_filename = None
        
        # Add file info to result
        result['files'] = {
            'document': doc_filename,
            'selfie': selfie_filename,
            'comparison': comparison_filename
        }
        
        print(f"\n✅ Request completed successfully")
        print("="*60)
        
        return jsonify({
            'success': True,
            'data': result
        })
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        
        print(f"\n❌ EXCEPTION IN FACE COMPARISON:")
        print("="*60)
        print(error_trace)
        print("="*60)
        
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}',
            'details': error_trace if app.debug else None
        }), 500



# ============================================
# API ENDPOINT 1: KYC Verification
# ============================================
@app.route('/api/kyc/verify', methods=['POST'])
def verify_kyc():
    """
    Verify KYC documents
    
    Expected input:
    {
        "document_type": "PAN" or "AADHAAR",
        "document_number": "ABCDE1234F",
        "full_name": "John Doe"
    }
    """
    try:
        data = request.json
        doc_type = data.get('document_type', '').upper()
        doc_number = data.get('document_number', '')
        full_name = data.get('full_name', '')
        
        # Verify the document
        result = kyc_verifier.verify_document(doc_type, doc_number)
        
        # Add timestamp
        result['timestamp'] = datetime.now().isoformat()
        result['full_name'] = full_name
        result['document_type'] = doc_type
        
        return jsonify({
            'success': True,
            'data': result
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400



        
@app.route('/api/aml/check', methods=['POST'])
def check_transaction():
    """Check if a transaction is suspicious (WITH MONGODB + WEBSOCKET)"""
    try:
        data = request.json
        
        # Get user's transaction history from MongoDB
        user_id = data.get('user_id', 'unknown')
        
        if db_service.is_connected():
            user_history_docs = db_service.get_user_transactions(user_id, limit=100)
            user_history = user_history_docs
        else:
            # Fallback to in-memory
            user_history = [t for t in transactions if t.get('user_id') == user_id]
        
        # Convert history to proper format
        history_dicts = []
        for t in user_history:
            hist_item = {
                'id': t.get('id'),
                'amount': t.get('amount'),
                'transaction_type': t.get('transaction_type'),
                'recipient_id': t.get('recipient_id')
            }
            # Handle timestamp conversion
            ts = t.get('timestamp')
            if isinstance(ts, str):
                try:
                    hist_item['timestamp'] = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                except:
                    hist_item['timestamp'] = datetime.now()
            elif isinstance(ts, datetime):
                hist_item['timestamp'] = ts
            else:
                hist_item['timestamp'] = datetime.now()
            
            history_dicts.append(hist_item)
        
        # Prepare transaction dict
        txn_dict = {
            'id': f"TXN{datetime.now().strftime('%Y%m%d%H%M%S')}",
            'user_id': user_id,
            'amount': data.get('amount'),
            'timestamp': datetime.now(),
            'transaction_type': data.get('transaction_type', 'transfer'),
            'recipient_id': data.get('recipient'),
            'recipient_account': data.get('recipient'),
            'location': data.get('location', ''),
            'description': data.get('description', '')
        }
        
        # RULE-BASED ANALYSIS
        rule_result = aml_engine.check_transaction(txn_dict, history_dicts)
        
        # ML-BASED ANALYSIS
        ml_result = ml_detector.predict(txn_dict, history_dicts)
        
        # COMBINED ANALYSIS
        combined_risk_score = int(
            rule_result['risk_score'] * 0.6 +
            ml_result['ml_fraud_probability'] * 100 * 0.4
        )
        
        is_flagged = bool(
            rule_result['is_flagged'] or 
            ml_result['ml_fraud_probability'] > 0.7
        )
        
        # HELPER FUNCTION TO CONVERT TYPES
        def convert_to_json_serializable(obj):
            """Convert numpy, datetime, and ObjectId types to JSON serializable types"""
            import numpy as np
            from bson import ObjectId
            
            if isinstance(obj, ObjectId):
                return str(obj)
            elif isinstance(obj, (np.integer, np.floating)):
                return float(obj)
            elif isinstance(obj, np.bool_):
                return bool(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, datetime):
                return obj.isoformat()
            elif isinstance(obj, dict):
                return {key: convert_to_json_serializable(value) for key, value in obj.items()}
            elif isinstance(obj, list):
                return [convert_to_json_serializable(item) for item in obj]
            else:
                return obj
        
        # Create transaction record with proper type conversion
        transaction = {
            'id': txn_dict['id'],
            'user_id': user_id,
            'amount': float(data.get('amount')),
            'recipient': str(data.get('recipient')),
            'description': str(data.get('description', '')),
            'timestamp': datetime.now(),
            'risk_score': int(combined_risk_score),
            'rule_risk_score': int(rule_result['risk_score']),
            'ml_fraud_probability': float(ml_result['ml_fraud_probability']),
            'ml_prediction': str(ml_result['ml_prediction']),
            'risk_level': str(rule_result['risk_level']),
            'is_flagged': bool(is_flagged),
            'flag_reasons': convert_to_json_serializable(rule_result['flags']),
            'status': 'completed'
        }
        
        # SAVE TO MONGODB (this adds _id field)
        if db_service.is_connected():
            mongo_id = db_service.save_transaction(transaction)
            print(f"✅ Transaction saved to MongoDB: {transaction['id']}")
        else:
            transactions.append(transaction)
            print(f"✅ Transaction saved to memory: {transaction['id']}")
        
        # Create JSON-safe version for WebSocket and response (remove _id)
        transaction_clean = {k: v for k, v in transaction.items() if k != '_id'}
        transaction_for_output = convert_to_json_serializable(transaction_clean)
        
        # EMIT WEBSOCKET EVENT
        ws_service.emit_new_transaction(transaction_for_output)
        print(f"📤 WebSocket: New transaction emitted")
        
        # Create alerts if flagged
        if is_flagged and rule_result['flags']:
            for flag in rule_result['flags']:
                alert = {
                    'id': f"ALT{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    'transaction_id': transaction['id'],
                    'severity': str(flag.get('severity', 'medium')),
                    'alert_type': str(flag.get('alert_type', '')),
                    'title': str(flag.get('title', '')),
                    'description': str(flag.get('description', '')),
                    'metadata': convert_to_json_serializable(flag.get('metadata', {})),
                    'ml_fraud_probability': float(ml_result['ml_fraud_probability']),
                    'status': 'open',
                    'created_at': datetime.now()
                }
                
                # SAVE TO MONGODB
                if db_service.is_connected():
                    db_service.save_alert(alert)
                    print(f"✅ Alert saved to MongoDB: {alert['id']}")
                else:
                    alerts.append(alert)
                
                # Create JSON-safe version for WebSocket (remove _id)
                alert_clean = {k: v for k, v in alert.items() if k != '_id'}
                alert_for_output = convert_to_json_serializable(alert_clean)
                
                # EMIT WEBSOCKET EVENT
                ws_service.emit_new_alert(alert_for_output)
                print(f"📤 WebSocket: New alert emitted")
        
        # Update user statistics
        if db_service.is_connected():
            user = db_service.get_user(user_id)
            if not user:
                user = {
                    'id': user_id,
                    'total_transactions': 0,
                    'total_volume': 0,
                    'flagged_transactions': 0
                }
            
            user['total_transactions'] = int(user.get('total_transactions', 0) + 1)
            user['total_volume'] = float(user.get('total_volume', 0) + data.get('amount', 0))
            if is_flagged:
                user['flagged_transactions'] = int(user.get('flagged_transactions', 0) + 1)
            
            db_service.save_user(user)
            print(f"✅ User stats updated: {user_id}")
        
        # EMIT STATS UPDATE
        if db_service.is_connected():
            stats = db_service.get_dashboard_stats()
            ws_service.emit_stats_update(stats)
            print(f"📤 WebSocket: Stats update emitted")
        
        # Get ML explanation
        ml_explanation = ml_detector.explain_prediction(txn_dict, history_dicts)
        
        print(f"\n{'='*60}")
        print(f"✅ TRANSACTION PROCESSED SUCCESSFULLY")
        print(f"{'='*60}")
        print(f"Transaction ID: {transaction['id']}")
        print(f"Risk Score: {combined_risk_score}/100")
        print(f"Flagged: {is_flagged}")
        print(f"{'='*60}\n")
        
        # Return JSON-safe response (everything converted)
        response_data = {
            'success': True,
            'data': {
                'transaction': transaction_for_output,
                'rule_analysis': convert_to_json_serializable(rule_result),
                'ml_analysis': convert_to_json_serializable(ml_result),
                'ml_explanation': convert_to_json_serializable(ml_explanation),
                'combined_risk_score': int(combined_risk_score),
                'decision': 'FLAGGED' if is_flagged else 'APPROVED'
            }
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        print(f"\n❌ Error checking transaction: {str(e)}")
        import traceback
        traceback.print_exc()
        print()
        
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/transactions/recent', methods=['GET'])
def get_recent_transactions():
    """Get recent transactions (FROM MONGODB)"""
    try:
        limit = int(request.args.get('limit', 10))
        
        if db_service.is_connected():
            recent = db_service.get_transactions(limit=limit)
            print(f"📊 Retrieved {len(recent)} transactions from MongoDB")
        else:
            recent = transactions[-limit:] if len(transactions) > limit else transactions
            recent = recent[::-1]  # Reverse to show newest first
            print(f"📊 Retrieved {len(recent)} transactions from memory")
        
        return jsonify({
            'success': True,
            'data': recent
        })
        
    except Exception as e:
        print(f"❌ Error getting transactions: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/alerts/recent', methods=['GET'])
def get_recent_alerts():
    """Get recent alerts (FROM MONGODB)"""
    try:
        limit = int(request.args.get('limit', 10))
        
        if db_service.is_connected():
            recent = db_service.get_alerts(limit=limit)
            print(f"🚨 Retrieved {len(recent)} alerts from MongoDB")
        else:
            recent = alerts[-limit:] if len(alerts) > limit else alerts
            recent = recent[::-1]
            print(f"🚨 Retrieved {len(recent)} alerts from memory")
        
        return jsonify({
            'success': True,
            'data': recent
        })
        
    except Exception as e:
        print(f"❌ Error getting alerts: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
# ============================================
# API ENDPOINT 3: Dashboard Statistics
# ============================================
@app.route('/api/dashboard/stats', methods=['GET'])
def get_dashboard_stats():
    """Get dashboard statistics (FROM MONGODB)"""
    try:
        if db_service.is_connected():
            stats = db_service.get_dashboard_stats()
        else:
            # Fallback to in-memory
            total_transactions = len(transactions)
            flagged_count = sum(1 for t in transactions if t.get('flagged', False))
            total_volume = sum(t.get('amount', 0) for t in transactions)
            open_alerts = sum(1 for a in alerts if a.get('status') == 'open')
            avg_risk = sum(t.get('risk_score', 0) for t in transactions) / total_transactions if total_transactions > 0 else 0
            
            stats = {
                'total_transactions': total_transactions,
                'flagged_transactions': flagged_count,
                'total_volume': total_volume,
                'open_alerts': open_alerts,
                'average_risk_score': round(avg_risk, 2),
                'flagging_rate': round((flagged_count / total_transactions * 100) if total_transactions > 0 else 0, 2)
            }
        
        return jsonify({
            'success': True,
            'data': stats
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/chat', methods=['POST'])
def chat():
    """
    Intelligent chatbot endpoint using GPT
    """
    try:
        data = request.json
        message = data.get('message', '').strip()
        
        if not message:
            return jsonify({
                'success': False,
                'error': 'Message cannot be empty'
            }), 400
        
        print(f"\n💬 Chat message: {message}")
        
        # Prepare context data
        context_data = prepare_chatbot_context(
            transactions=transactions,
            alerts=alerts,
            stats={
                'total_transactions': len(transactions),
                'flagged_transactions': sum(1 for t in transactions if t.get('flagged')),
                'open_alerts': sum(1 for a in alerts if a.get('status') == 'OPEN'),
                'average_risk_score': sum(t.get('risk_score', 0) for t in transactions) / len(transactions) if transactions else 0
            }
        )
        
        # Get chatbot response
        response_text = chatbot.chat(message, context_data)
        
        print(f"🤖 Response: {response_text[:100]}...")
        
        return jsonify({
            'success': True,
            'data': {
                'response': response_text,
                'timestamp': datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        print(f"❌ Chat error: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
# ============================================
# API ENDPOINT 5: Get Recent Transactions
# ============================================@app.route('/api/transactions/recent', methods=['GET'])
def get_recent_transactions():
    """Get recent transactions (FROM MONGODB)"""
    try:
        limit = int(request.args.get('limit', 10))
        
        if db_service.is_connected():
            recent = db_service.get_transactions(limit=limit)
        else:
            recent = transactions[-limit:] if len(transactions) > limit else transactions
            recent = recent[::-1]  # Reverse
        
        return jsonify({
            'success': True,
            'data': recent
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ============================================
# API ENDPOINT 6: Get Recent Alerts
# ============================================@app.route('/api/alerts/recent', methods=['GET'])
def get_recent_alerts():
    """Get recent alerts (FROM MONGODB)"""
    try:
        limit = int(request.args.get('limit', 10))
        
        if db_service.is_connected():
            recent = db_service.get_alerts(limit=limit)
        else:
            recent = alerts[-limit:] if len(alerts) > limit else alerts
            recent = recent[::-1]
        
        return jsonify({
            'success': True,
            'data': recent
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ============================================
# Start the server
# ============================================
if __name__ == '__main__':
    print("🚀 FinGuard AI Backend Starting...")
    print("📍 Server running on: http://localhost:5000")
    print("📚 API Endpoints:")
    print("   - POST /api/kyc/verify")
    print("   - POST /api/aml/check")
    print("   - GET  /api/dashboard/stats")
    print("   - POST /api/chat")
    print("   - GET  /api/transactions/recent")
    print("   - GET  /api/alerts/recent")
    print("\n✨ Ready to accept requests!\n")
    print("🚀 FinGuard AI Backend Starting...")
    print("📍 Server running on: http://localhost:5000")
    print(f"📦 MongoDB: {'Connected' if db_service.is_connected() else 'Not connected (using in-memory)'}")
    print("🔌 WebSocket: Enabled")
    print("\n✨ Ready to accept requests!\n")
    
    # Use socketio.run instead of app.run for WebSocket support
    ws_service.socketio.run(app, debug=True, host='127.0.0.1', port=5000)
    # app.run(debug=True, host='127.0.0.1', port=5000)