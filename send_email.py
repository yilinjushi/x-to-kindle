"""
send_email.py — Send a file or text via Gmail SMTP (App Password auth)

Usage:
    # Send plain text body
    python send_email.py --to you@gmail.com --subject "X书签" --body "hello"

    # Send file as attachment
    python send_email.py --to you@gmail.com --subject "X书签" --attach bookmarks_kindle.txt

Config file: L:/FilenPersonal/aitool/email_config.json
    {
        "gmail_user": "your@gmail.com",
        "app_password": "xxxx xxxx xxxx xxxx"
    }
"""

import sys
import json
import smtplib
import argparse
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from app_config import GMAIL_APP_PASSWORD, GMAIL_USER

CONFIG_FILE = Path(__file__).resolve().parent / "email_config.json"


def load_config() -> dict:
    if GMAIL_USER and GMAIL_APP_PASSWORD:
        return {
            "gmail_user": GMAIL_USER,
            "app_password": GMAIL_APP_PASSWORD,
        }

    path = CONFIG_FILE
    if not path.exists():
        print(
            "ERROR: Missing Gmail credentials. Set GMAIL_USER and GMAIL_APP_PASSWORD, "
            "or create email_config.json.",
            file=sys.stderr,
        )
        sys.exit(1)

    with open(path, encoding="utf-8") as f:
        config = json.load(f)

    if not config.get("gmail_user") or not config.get("app_password"):
        print("ERROR: email_config.json must have 'gmail_user' and 'app_password'", file=sys.stderr)
        sys.exit(1)
    return config


def send_email(to: str, subject: str, body: str = "", attach: str = None):
    config = load_config()
    gmail_user = config["gmail_user"]
    app_password = config["app_password"]

    if attach:
        msg = MIMEMultipart()
        msg["From"] = gmail_user
        msg["To"] = to
        msg["Subject"] = subject

        msg.attach(MIMEText(body or "", "plain", "utf-8"))

        attach_path = Path(attach)
        if not attach_path.exists():
            print(f"ERROR: Attachment not found: {attach}", file=sys.stderr)
            sys.exit(1)

        with open(attach_path, "rb") as f:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header(
            "Content-Disposition",
            "attachment",
            filename=("utf-8", "", attach_path.name)
        )
        msg.attach(part)
    else:
        msg = MIMEText(body or "", "plain", "utf-8")
        msg["From"] = gmail_user
        msg["To"] = to
        msg["Subject"] = subject

    print(f"Sending to {to} via {gmail_user}...")
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(gmail_user, app_password)
        server.sendmail(gmail_user, to, msg.as_string())

    print(f"Sent: \"{subject}\" -> {to}")


def main():
    parser = argparse.ArgumentParser(description="Send email via Gmail SMTP")
    parser.add_argument("--to", required=True, help="Recipient email address")
    parser.add_argument("--subject", required=True, help="Email subject")
    parser.add_argument("--body", default="", help="Plain text body")
    parser.add_argument("--attach", default=None, help="Path to file attachment")
    args = parser.parse_args()

    send_email(to=args.to, subject=args.subject, body=args.body, attach=args.attach)


if __name__ == "__main__":
    if sys.stdout.encoding.lower() != 'utf-8':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    main()
