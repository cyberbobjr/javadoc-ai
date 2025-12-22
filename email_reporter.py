"""
Email reporting module for Javadoc automation.
Sends reports of documented elements via email.
"""

import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict
from datetime import datetime


logger = logging.getLogger(__name__)


class EmailReporter:
    """Handles email reporting for Javadoc automation."""
    
    def __init__(self, smtp_server: str, smtp_port: int, from_email: str, 
                 password: str, to_emails: List[str], subject_template: str):
        """
        Initialize email reporter.
        
        Args:
            smtp_server: SMTP server address
            smtp_port: SMTP server port
            from_email: Sender email address
            password: Email password
            to_emails: List of recipient email addresses
            subject_template: Subject template (can include {date})
        """
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.from_email = from_email
        self.password = password
        self.to_emails = to_emails if isinstance(to_emails, list) else [to_emails]
        self.subject_template = subject_template
    
    def send_report(self, date_str: str, stats: Dict, documented_files: List[Dict]) -> bool:
        """
        Send email report of documented elements.
        
        Args:
            date_str: Date string for the report
            stats: Dictionary with statistics (total_files, total_classes, total_methods, etc.)
            documented_files: List of dictionaries with file information
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.from_email
            msg['To'] = ', '.join(self.to_emails)
            msg['Subject'] = self.subject_template.format(date=date_str)
            
            # Create HTML report
            html_content = self._create_html_report(date_str, stats, documented_files)
            text_content = self._create_text_report(date_str, stats, documented_files)
            
            # Attach both plain text and HTML versions
            part1 = MIMEText(text_content, 'plain')
            part2 = MIMEText(html_content, 'html')
            msg.attach(part1)
            msg.attach(part2)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.from_email, self.password)
                server.send_message(msg)
            
            logger.info(f"Email report sent to {', '.join(self.to_emails)}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email report: {e}")
            return False
    
    def _create_text_report(self, date_str: str, stats: Dict, documented_files: List[Dict]) -> str:
        """Create plain text report."""
        lines = [
            f"Javadoc Generation Report - {date_str}",
            "=" * 50,
            "",
            "Summary:",
            f"  Total files processed: {stats.get('total_files', 0)}",
            f"  Total classes documented: {stats.get('total_classes', 0)}",
            f"  Total methods documented: {stats.get('total_methods', 0)}",
            f"  Total elements documented: {stats.get('total_elements', 0)}",
            "",
            "Files processed:",
            ""
        ]
        
        for file_info in documented_files:
            lines.append(f"  {file_info.get('file_path', 'Unknown')}")
            lines.append(f"    Classes: {file_info.get('classes', 0)}, Methods: {file_info.get('methods', 0)}")
            if file_info.get('elements'):
                for element in file_info['elements']:
                    lines.append(f"      - {element}")
            lines.append("")
        
        return '\n'.join(lines)
    
    def _create_html_report(self, date_str: str, stats: Dict, documented_files: List[Dict]) -> str:
        """Create HTML report."""
        html = f"""
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                h1 {{
                    color: #2c3e50;
                    border-bottom: 3px solid #3498db;
                    padding-bottom: 10px;
                }}
                h2 {{
                    color: #34495e;
                    margin-top: 30px;
                }}
                .summary {{
                    background-color: #ecf0f1;
                    padding: 15px;
                    border-radius: 5px;
                    margin: 20px 0;
                }}
                .stat {{
                    display: inline-block;
                    margin: 10px 20px 10px 0;
                }}
                .stat-label {{
                    font-weight: bold;
                    color: #7f8c8d;
                }}
                .stat-value {{
                    font-size: 24px;
                    color: #2980b9;
                    font-weight: bold;
                }}
                .file-list {{
                    list-style-type: none;
                    padding: 0;
                }}
                .file-item {{
                    background-color: #fff;
                    border: 1px solid #bdc3c7;
                    border-radius: 5px;
                    padding: 15px;
                    margin: 10px 0;
                }}
                .file-path {{
                    font-family: monospace;
                    color: #16a085;
                    font-weight: bold;
                }}
                .element-list {{
                    list-style-type: disc;
                    margin-left: 30px;
                    color: #7f8c8d;
                }}
                .footer {{
                    margin-top: 40px;
                    padding-top: 20px;
                    border-top: 1px solid #bdc3c7;
                    text-align: center;
                    color: #7f8c8d;
                    font-size: 12px;
                }}
            </style>
        </head>
        <body>
            <h1>Javadoc Generation Report</h1>
            <p><strong>Date:</strong> {date_str}</p>
            
            <div class="summary">
                <h2>Summary</h2>
                <div class="stat">
                    <div class="stat-label">Files Processed</div>
                    <div class="stat-value">{stats.get('total_files', 0)}</div>
                </div>
                <div class="stat">
                    <div class="stat-label">Classes Documented</div>
                    <div class="stat-value">{stats.get('total_classes', 0)}</div>
                </div>
                <div class="stat">
                    <div class="stat-label">Methods Documented</div>
                    <div class="stat-value">{stats.get('total_methods', 0)}</div>
                </div>
                <div class="stat">
                    <div class="stat-label">Total Elements</div>
                    <div class="stat-value">{stats.get('total_elements', 0)}</div>
                </div>
            </div>
            
            <h2>Documented Files</h2>
            <ul class="file-list">
        """
        
        for file_info in documented_files:
            html += f"""
                <li class="file-item">
                    <div class="file-path">{file_info.get('file_path', 'Unknown')}</div>
                    <div>Classes: {file_info.get('classes', 0)} | Methods: {file_info.get('methods', 0)}</div>
            """
            
            if file_info.get('elements'):
                html += '<ul class="element-list">'
                for element in file_info['elements']:
                    html += f'<li>{element}</li>'
                html += '</ul>'
            
            html += '</li>'
        
        html += """
            </ul>
            
            <div class="footer">
                <p>Generated by Javadoc AI Automation System</p>
                <p>This is an automated message. Please do not reply.</p>
            </div>
        </body>
        </html>
        """
        
        return html
