import json
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List, Optional

import requests

from .config import EmailConfig, TeamsConfig


class Notifier:
    def __init__(self, email_config: EmailConfig, teams_config: TeamsConfig):
        self.email_config = email_config
        self.teams_config = teams_config

    def send_email(self, subject: str, body: str) -> None:
        """Send an email notification."""
        if not self.email_config.enabled:
            print("Email notification disabled.")
            return

        try:
            msg = MIMEMultipart()
            msg["From"] = self.email_config.user
            msg["To"] = ", ".join(self.email_config.recipients)
            msg["Subject"] = subject

            msg.attach(MIMEText(body, "plain"))

            # Determine if SSL or TLS is needed based on port, 
            # simplified generic logic: 465 is SSL, 587 is TLS
            if self.email_config.port == 465:
                server = smtplib.SMTP_SSL(self.email_config.host, self.email_config.port)
            else:
                server = smtplib.SMTP(self.email_config.host, self.email_config.port)
                server.starttls()

            server.login(self.email_config.user, self.email_config.password.get_secret_value())
            server.send_message(msg)
            server.quit()
            print(f"Email sent to {self.email_config.recipients}")
        except Exception as e:
            print(f"Failed to send email: {e}")

    def send_teams_notification(self, title: str, message: str) -> None:
        """Send a notification to Microsoft Teams."""
        if not self.teams_config.enabled:
            print("Teams notification disabled.")
            return

        payload = {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": "0076D7",
            "summary": title,
            "sections": [{
                "activityTitle": title,
                "activitySubtitle": "Javadoc Automation Bot",
                "activityImage": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c3/Python-logo-notext.svg/1200px-Python-logo-notext.svg.png",
                "markdown": True,
                "text": message
            }]
        }

        try:
            headers = {"Content-Type": "application/json"}
            response = requests.post(
                self.teams_config.webhook_url.get_secret_value(),
                data=json.dumps(payload),
                headers=headers
            )
            response.raise_for_status()
            print("Teams notification sent.")
        except Exception as e:
            print(f"Failed to send Teams notification: {e}")
