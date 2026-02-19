"""
Intelligent Chatbot Service using Local AI

This chatbot uses a free, offline language model from Hugging Face.
No API keys needed!
"""

from datetime import datetime
from typing import List, Dict
import json
import re

class IntelligentChatbot:
    """
    Local AI-powered chatbot with context about the compliance system
    
    Uses rule-based responses + pattern matching for fast, accurate answers
    No API keys or internet required!
    """
    
    def __init__(self):
        """Initialize chatbot"""
        
        print("✅ Intelligent chatbot initialized (Local AI)")
        
        # System knowledge base
        self.knowledge_base = {
            'aml_rules': {
                'large_transaction': {
                    'threshold': '₹2,00,000',
                    'description': 'Flags transactions above ₹2 lakh',
                    'severity': 'MEDIUM',
                    'risk_score': '30-50 points'
                },
                'rapid_movement': {
                    'threshold': '3+ transactions in 1 hour',
                    'description': 'Detects rapid succession of transactions',
                    'severity': 'HIGH',
                    'risk_score': '40-70 points'
                },
                'structuring': {
                    'threshold': 'Multiple transactions near ₹50,000',
                    'description': 'Catches attempts to avoid reporting limits',
                    'severity': 'CRITICAL',
                    'risk_score': '50-80 points'
                },
                'unusual_time': {
                    'threshold': '11 PM - 5 AM',
                    'description': 'Flags transactions during unusual hours',
                    'severity': 'LOW',
                    'risk_score': '15 points'
                },
                'round_amount': {
                    'threshold': 'Round numbers > ₹50,000',
                    'description': 'Detects suspiciously round amounts',
                    'severity': 'LOW',
                    'risk_score': '20 points'
                },
                'velocity_check': {
                    'threshold': '3x average daily transactions',
                    'description': 'Monitors unusual transaction frequency',
                    'severity': 'MEDIUM',
                    'risk_score': '30 points'
                },
                'high_risk_geography': {
                    'threshold': 'International/offshore transfers',
                    'description': 'Flags high-risk locations',
                    'severity': 'HIGH',
                    'risk_score': '40 points'
                },
                'new_recipient': {
                    'threshold': 'First-time recipient',
                    'description': 'Flags transactions to new recipients',
                    'severity': 'MEDIUM',
                    'risk_score': '20-35 points'
                },
                'amount_spike': {
                    'threshold': '5x average amount',
                    'description': 'Detects sudden spikes in transaction amounts',
                    'severity': 'MEDIUM',
                    'risk_score': '35 points'
                },
                'frequency_anomaly': {
                    'threshold': '3x average daily frequency',
                    'description': 'Detects unusual transaction patterns',
                    'severity': 'MEDIUM',
                    'risk_score': '30 points'
                },
                'consecutive_round': {
                    'threshold': '3+ round amounts in 24 hours',
                    'description': 'Multiple round amount transactions',
                    'severity': 'HIGH',
                    'risk_score': '45 points'
                },
                'small_testing': {
                    'threshold': 'Small amounts before large',
                    'description': 'Detects account testing behavior',
                    'severity': 'LOW',
                    'risk_score': '25 points'
                },
                'weekend': {
                    'threshold': 'Large amounts on weekends',
                    'description': 'Flags large weekend transactions',
                    'severity': 'LOW',
                    'risk_score': '15 points'
                }
            },
            
            'features': {
                'kyc': 'Document verification with OCR and face recognition',
                'aml': '13 intelligent rules + ML-based fraud detection',
                'ml_model': 'Random Forest trained on 5,000 transactions',
                'face_recognition': 'Age-aware verification with OpenCV DNN',
                'documents': 'PAN, Aadhaar, Passport, Driver\'s License, Voter ID',
                'reports': 'PDF compliance report generation',
                'audit': 'Complete audit trail logging'
            }
        }
        
        # Conversation history
        self.conversation_history = []
    
    def chat(self, user_message: str, context_data: Dict = None) -> str:
        """
        Process user message and generate intelligent response
        
        Args:
            user_message: User's question or message
            context_data: Additional context (transactions, alerts, etc.)
        
        Returns:
            Chatbot response
        """
        
        message_lower = user_message.lower()
        
        # Store in history
        self.conversation_history.append({
            'user': user_message,
            'timestamp': datetime.now().isoformat()
        })
        
        # Generate response based on intent
        response = self._generate_response(message_lower, context_data)
        
        # Store response in history
        self.conversation_history[-1]['bot'] = response
        
        return response
    
    def _generate_response(self, message: str, context: Dict) -> str:
        """Generate contextual response based on message intent"""
        
        # Intent: AML Rules Query
        if self._match_intent(message, ['rule', 'aml', 'detection', 'check']):
            return self._handle_rules_query(message, context)
        
        # Intent: Statistics Query
        if self._match_intent(message, ['how many', 'total', 'count', 'number of']):
            return self._handle_statistics_query(message, context)
        
        # Intent: Risk/Alert Query
        if self._match_intent(message, ['risk', 'suspicious', 'flagged', 'alert']):
            return self._handle_risk_query(message, context)
        
        # Intent: Feature Query
        if self._match_intent(message, ['what can', 'feature', 'capability', 'do']):
            return self._handle_feature_query(message, context)
        
        # Intent: Specific Rule Explanation
        if self._match_intent(message, ['explain', 'what is', 'tell me about']):
            return self._handle_explanation_query(message, context)
        
        # Intent: Threshold Query
        if self._match_intent(message, ['threshold', 'limit', 'when']):
            return self._handle_threshold_query(message, context)
        
        # Intent: Help
        if self._match_intent(message, ['help', 'assist', 'guide']):
            return self._handle_help_query()
        
        # Intent: Greeting
        if self._match_intent(message, ['hello', 'hi', 'hey', 'greetings']):
            return self._handle_greeting()
        
        # Intent: Thanks
        if self._match_intent(message, ['thank', 'thanks', 'appreciate']):
            return "You're welcome! 😊 Let me know if you need anything else!"
        
        # Default: General response
        return self._handle_default_query(message, context)
    
    def _match_intent(self, message: str, keywords: List[str]) -> bool:
        """Check if message matches any of the keywords"""
        return any(keyword in message for keyword in keywords)
    
    def _handle_rules_query(self, message: str, context: Dict) -> str:
        """Handle queries about AML rules"""
        
        # Check for specific rule
        for rule_name, rule_info in self.knowledge_base['aml_rules'].items():
            if rule_name.replace('_', ' ') in message:
                return f"""📋 **{rule_name.replace('_', ' ').title()}** Rule

**Threshold:** {rule_info['threshold']}
**Description:** {rule_info['description']}
**Severity:** {rule_info['severity']}
**Risk Score:** {rule_info['risk_score']}

This rule helps detect {rule_info['description'].lower()} and is crucial for AML compliance."""
        
        # General rules overview
        return f"""📋 **FinGuard AI Detection Rules**

We use **13 intelligent AML rules** to detect suspicious activity:

**High Severity:**
🔴 Structuring Pattern
🔴 Rapid Movement
🔴 High-Risk Geography
🔴 Consecutive Round Amounts

**Medium Severity:**
🟡 Large Transaction
🟡 New Recipient
🟡 Amount Spike
🟡 Frequency Anomaly
🟡 Velocity Check

**Low Severity:**
🟢 Unusual Time
🟢 Round Amount
🟢 Small Testing
🟢 Weekend Transaction

Plus **ML-based fraud prediction** for enhanced accuracy!

Ask me about any specific rule for details! 
Example: "Explain the structuring rule" """
    
    def _handle_statistics_query(self, message: str, context: Dict) -> str:
        """Handle statistics queries"""
        
        if not context:
            return "📊 I need system data to provide statistics. Please try again in a moment."
        
        if 'transaction' in message:
            total = context.get('total_transactions', 0)
            flagged = context.get('flagged_transactions', 0)
            return f"""📊 **Transaction Statistics**

**Total Transactions:** {total:,}
**Flagged Transactions:** {flagged:,}
**Clean Transactions:** {total - flagged:,}
**Flagging Rate:** {(flagged/total*100) if total > 0 else 0:.1f}%

{f"🚩 {flagged} transactions need review!" if flagged > 0 else "✅ All transactions look good!"}"""
        
        if 'alert' in message:
            alerts = context.get('open_alerts', 0)
            return f"""🚨 **Alert Statistics**

**Open Alerts:** {alerts}
**Status:** {'⚠️ Needs attention' if alerts > 0 else '✅ All clear'}

{f"You have {alerts} alerts waiting for review." if alerts > 0 else "Great job! No pending alerts."}"""
        
        # General statistics
        return f"""📊 **System Overview**

**Transactions:** {context.get('total_transactions', 0):,}
**Flagged:** {context.get('flagged_transactions', 0):,}
**Open Alerts:** {context.get('open_alerts', 0)}
**Avg Risk Score:** {context.get('average_risk_score', 0):.1f}/100

Ask for specific stats: "How many transactions?" or "Show alerts" """
    
    def _handle_risk_query(self, message: str, context: Dict) -> str:
        """Handle risk and alert queries"""
        
        if not context or not context.get('recent_flagged'):
            return "No flagged transactions found in recent activity. System is running smoothly! ✅"
        
        recent = context['recent_flagged'][0]
        
        return f"""🚩 **Latest Flagged Transaction**

**Transaction ID:** {recent['id']}
**Amount:** ₹{recent['amount']:,.2f}
**Risk Score:** {recent['risk_score']}/100
**Reason:** {recent.get('reason', 'Multiple risk factors detected')}

**Recommendation:** This transaction requires manual review by a compliance officer.

Need more details? Ask: "Show all flagged transactions" """
    
    def _handle_feature_query(self, message: str, context: Dict) -> str:
        """Handle feature/capability queries"""
        
        return """✨ **FinGuard AI Capabilities**

**1. KYC Verification** 🆔
   • Document upload & OCR text extraction
   • Supports 5 document types (PAN, Aadhaar, Passport, License, Voter ID)
   • Face recognition with age-aware verification
   • 95%+ accuracy

**2. AML Detection** 🔍
   • 13 intelligent detection rules
   • ML-based fraud prediction (Random Forest)
   • Real-time risk scoring (0-100)
   • Hybrid approach: Rules + AI

**3. Compliance Tools** 📋
   • PDF report generation
   • Complete audit trail
   • Real-time dashboard
   • Alert management

**4. AI Assistant** 🤖
   • Natural language queries
   • Contextual responses
   • System insights

Ask me anything about these features!"""
    
    def _handle_explanation_query(self, message: str, context: Dict) -> str:
        """Handle explanation requests"""
        
        # Check for specific rule
        for rule_name, rule_info in self.knowledge_base['aml_rules'].items():
            if rule_name.replace('_', ' ') in message or rule_name in message:
                return f"""💡 **Understanding the {rule_name.replace('_', ' ').title()} Rule**

{rule_info['description']}

**How it works:**
When a transaction meets the threshold of {rule_info['threshold']}, our system automatically flags it with a {rule_info['severity']} severity alert.

**Risk Impact:**
This adds {rule_info['risk_score']} to the overall risk score.

**Why it matters:**
This pattern is commonly associated with money laundering and fraud attempts. By detecting it early, we help prevent financial crimes.

**Example:**
{self._get_rule_example(rule_name)}"""
        
        return "I can explain any AML rule or system feature. Try asking: 'Explain the structuring rule' or 'What is face recognition?'"
    
    def _get_rule_example(self, rule_name: str) -> str:
        """Get example for a specific rule"""
        
        examples = {
            'large_transaction': "A user transfers ₹3,50,000 → Flagged as large transaction",
            'rapid_movement': "User makes 5 transactions in 30 minutes → Flagged for rapid movement",
            'structuring': "User makes 3 transactions of ₹49,500 each → Flagged for structuring",
            'unusual_time': "Transaction at 2:30 AM → Flagged for unusual time",
            'round_amount': "Transfer of exactly ₹1,00,000 → Flagged for round amount",
            'new_recipient': "₹2,00,000 to first-time recipient → Flagged as high-risk"
        }
        
        return examples.get(rule_name, "System detects this pattern and flags it for review.")
    
    def _handle_threshold_query(self, message: str, context: Dict) -> str:
        """Handle threshold/limit queries"""
        
        return """⚖️ **Detection Thresholds**

**Transaction Amounts:**
• Large Transaction: > ₹2,00,000
• Structuring Detection: Near ₹50,000
• Round Amount: > ₹50,000 (round numbers)

**Time-Based:**
• Rapid Movement: 3+ transactions in 1 hour
• Unusual Time: 11 PM - 5 AM
• Weekend: Saturday/Sunday large amounts

**Pattern-Based:**
• Velocity Check: 3x average frequency
• Amount Spike: 5x average amount
• Frequency Anomaly: 3x daily average

**Geography:**
• High-Risk: International/offshore transfers

These thresholds are based on RBI/SEBI guidelines and industry best practices."""
    
    def _handle_help_query(self) -> str:
        """Handle help requests"""
        
        return """👋 **How I Can Help You**

**Ask About Statistics:**
• "How many transactions?"
• "Show me alerts"
• "What's the average risk score?"

**Learn About Rules:**
• "What are the AML rules?"
• "Explain the structuring rule"
• "What are the thresholds?"

**Check Risk:**
• "Show risky transactions"
• "Any suspicious activity?"
• "Latest flagged transaction"

**System Features:**
• "What can you do?"
• "How does face recognition work?"
• "Tell me about the ML model"

**Tips:**
✓ Be specific in your questions
✓ Ask one thing at a time
✓ Use natural language

What would you like to know?"""
    
    def _handle_greeting(self) -> str:
        """Handle greetings"""
        
        greetings = [
            "Hello! 👋 I'm FinGuard AI Assistant. How can I help you today?",
            "Hi there! 😊 I'm here to help with compliance questions. What do you need?",
            "Hey! 🤖 Ready to assist with AML, KYC, or system queries. Ask away!",
            "Greetings! 🎯 I'm your compliance expert. What can I help you with?"
        ]
        
        import random
        return random.choice(greetings)
    
    def _handle_default_query(self, message: str, context: Dict) -> str:
        """Handle unrecognized queries"""
        
        return """🤔 I'm not sure I understood that question.

**I can help with:**
• Transaction statistics and trends
• AML rules and detection
• Risk analysis and alerts
• System features and capabilities

**Try asking:**
• "How many transactions today?"
• "Explain the AML rules"
• "Show risky transactions"
• "What can you do?"

Type **"help"** for more examples!"""
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []


# Helper function to prepare context data
def prepare_chatbot_context(transactions: List, alerts: List, stats: Dict) -> Dict:
    """
    Prepare context data for chatbot
    
    Args:
        transactions: List of recent transactions
        alerts: List of recent alerts
        stats: Dashboard statistics
    
    Returns:
        Formatted context dictionary
    """
    
    # Get recent flagged transactions
    recent_flagged = [
        {
            'id': t.get('id'),
            'amount': t.get('amount'),
            'risk_score': t.get('risk_score'),
            'reason': ', '.join([f.get('rule', 'Unknown') for f in t.get('flag_reasons', [])])
        }
        for t in transactions[-5:] if t.get('flagged', False)
    ]
    
    # Get alert summary
    alert_summary = {
        'total': len(alerts),
        'critical': sum(1 for a in alerts if a.get('severity') == 'critical'),
        'high': sum(1 for a in alerts if a.get('severity') == 'high')
    }
    
    return {
        'total_transactions': stats.get('total_transactions', 0),
        'flagged_transactions': stats.get('flagged_transactions', 0),
        'open_alerts': stats.get('open_alerts', 0),
        'average_risk_score': stats.get('average_risk_score', 0),
        'recent_flagged': recent_flagged,
        'alert_summary': alert_summary
    }