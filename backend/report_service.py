"""
Compliance Report Generation Service

Generates PDF reports for:
- Transaction analysis
- Alert summaries
- Compliance audits
"""

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib import colors
from datetime import datetime
import os

class ReportService:
    """Generate compliance reports in PDF format"""
    
    def __init__(self):
        self.reports_dir = 'reports'
        if not os.path.exists(self.reports_dir):
            os.makedirs(self.reports_dir)
        
        print("✅ Report Service initialized")
    
    def generate_transaction_report(self, transactions, alerts, stats):
        """
        Generate comprehensive transaction report
        
        Args:
            transactions: List of transactions
            alerts: List of alerts
            stats: Dashboard statistics
        
        Returns:
            Path to generated PDF file
        """
        
        # Create filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"transaction_report_{timestamp}.pdf"
        filepath = os.path.join(self.reports_dir, filename)
        
        # Create PDF
        doc = SimpleDocTemplate(filepath, pagesize=letter)
        story = []
        styles = getSampleStyleSheet()
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#2563eb'),
            spaceAfter=30,
            alignment=1  # Center
        )
        story.append(Paragraph("FinGuard AI", title_style))
        story.append(Paragraph("Compliance Transaction Report", styles['Heading2']))
        story.append(Spacer(1, 0.3*inch))
        
        # Report metadata
        report_date = datetime.now().strftime('%B %d, %Y at %I:%M %p')
        story.append(Paragraph(f"<b>Generated:</b> {report_date}", styles['Normal']))
        story.append(Spacer(1, 0.2*inch))
        
        # Executive Summary
        story.append(Paragraph("Executive Summary", styles['Heading2']))
        story.append(Spacer(1, 0.1*inch))
        
        summary_data = [
            ['Metric', 'Value'],
            ['Total Transactions', str(stats.get('total_transactions', 0))],
            ['Flagged Transactions', str(stats.get('flagged_transactions', 0))],
            ['Open Alerts', str(stats.get('open_alerts', 0))],
            ['Average Risk Score', f"{stats.get('average_risk_score', 0):.2f}/100"],
            ['Total Volume', f"₹{stats.get('total_volume', 0):,.2f}"],
            ['Flagging Rate', f"{stats.get('flagging_rate', 0):.2f}%"]
        ]
        
        summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2563eb')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Flagged Transactions
        story.append(Paragraph("Flagged Transactions", styles['Heading2']))
        story.append(Spacer(1, 0.1*inch))
        
        flagged = [t for t in transactions if t.get('flagged', False)]
        
        if flagged:
            flagged_data = [['ID', 'Amount', 'Risk Score', 'Status']]
            for t in flagged[-10:]:  # Last 10 flagged
                flagged_data.append([
                    t.get('id', 'N/A')[:12],
                    f"₹{t.get('amount', 0):,.0f}",
                    f"{t.get('risk_score', 0)}/100",
                    t.get('risk_level', 'N/A')
                ])
            
            flagged_table = Table(flagged_data, colWidths=[2*inch, 1.5*inch, 1.5*inch, 1.5*inch])
            flagged_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ef4444')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(flagged_table)
        else:
            story.append(Paragraph("No flagged transactions in this period.", styles['Normal']))
        
        story.append(Spacer(1, 0.3*inch))
        
        # Alert Summary
        story.append(Paragraph("Alert Summary", styles['Heading2']))
        story.append(Spacer(1, 0.1*inch))
        
        if alerts:
            alert_data = [['Alert ID', 'Severity', 'Type', 'Status']]
            for alert in alerts[-10:]:  # Last 10 alerts
                alert_data.append([
                    alert.get('id', 'N/A')[:12],
                    alert.get('severity', 'N/A'),
                    alert.get('alert_type', 'N/A').replace('_', ' ').title(),
                    alert.get('status', 'N/A')
                ])
            
            alert_table = Table(alert_data, colWidths=[2*inch, 1.5*inch, 2*inch, 1.5*inch])
            alert_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f59e0b')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(alert_table)
        else:
            story.append(Paragraph("No alerts in this period.", styles['Normal']))
        
        # Footer
        story.append(Spacer(1, 0.5*inch))
        story.append(Paragraph(
            "This report was automatically generated by FinGuard AI Compliance System.",
            styles['Italic']
        ))
        
        # Build PDF
        doc.build(story)
        
        print(f"✅ Report generated: {filepath}")
        return filepath