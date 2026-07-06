# step 3
# email the meeting summary to the user via Gmail SMTP 

import os
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()

GMAIL_ADDRESS = os.environ["GMAIL_ADDRESS"]
GMAIL_APP_PASSWORD = os.environ["GMAIL_APP_PASSWORD"].replace(" ", "")


# turn the markdown summary into simple html and email it
def send_summary_email(to_email: str, summary_md: str) -> None:
    # very light markdown -> html (headings + line breaks) so it looks okay in email
    html_body = "".join(
        f"<h3>{line[3:]}</h3>" if line.startswith("## ")
        else f"{line}<br>"
        for line in summary_md.splitlines()
    )

    msg = EmailMessage()
    msg["From"] = GMAIL_ADDRESS
    msg["To"] = to_email
    msg["Subject"] = "Your Meeting Summary"
    msg.set_content(summary_md)  # plain-text fallback
    msg.add_alternative(
        f"<div style='font-family:sans-serif'>{html_body}</div>", subtype="html"
    )

    # Gmail's secure SMTP over SSL
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
        server.send_message(msg)


if __name__ == "__main__":
    # manual test:  
    # python send_email.py you@example.com
    import sys
    send_summary_email(sys.argv[1], "## Summary\nThis is a test email from Meeting Reader.")
    print("Sent!")
