import base64
import os
import random
import time
from email.mime.text import MIMEText

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from mongo_client.maildb import MailDB


class PenpalMailer:
    """Handles sending and receiving emails using the Gmail API."""

    accepted_types = {"text/plain", "text/html"}

    def __init__(self):
        scopes = [
            "https://www.googleapis.com/auth/gmail.readonly",
            "https://www.googleapis.com/auth/gmail.compose",
            "https://www.googleapis.com/auth/gmail.modify",
        ]

        self.penpal_id = os.environ.get("PENPAL_ID")
        self.penpal_name = os.environ.get("PENPAL_NAME")
        self.penpal_email = os.environ.get("PENPAL_EMAIL")

        # ok to crash here
        self.polling_interval = int(os.environ.get("EMAIL_POLLING_INTERVAL"))

        self.creds = Credentials.from_authorized_user_file("token.json", scopes)
        self.db_conn = MailDB()

    def wait(self):
        """Pause execution for the specified polling interval."""
        time.sleep(self.polling_interval + random.random())

    def send_mail(self):
        """Send outgoing emails stored in the database (state == 'pending')."""
        outgoing = self.db_conn.outgoing_email()
        for email in outgoing:
            penpal_email_local, penpal_email_domain = self.penpal_email.split("@")

            message_id = email["_id"]
            message = MIMEText(email["body"])
            message["to"] = email["From"]
            message[
                "from"
            ] = f"{self.penpal_name} <{penpal_email_local}+{email['customer_id']}@{penpal_email_domain}>"
            message["subject"] = f"Re: {email['Subject']}"

            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

            try:
                with build("gmail", "v1", credentials=self.creds) as service:
                    sent_message = (
                        service.users()
                        .messages()
                        .send(userId="me", body={"raw": raw_message})
                        .execute()
                    )
                    self.db_conn.update_email(message_id, {"state": "sent"})
                    print(f'Message sent. Message ID: {sent_message["id"]}')
            except HttpError as error:
                print(f"An error occurred: {error}")

    def archive_downloaded(self, message_ids):
        """Archive downloaded emails by removing the 'INBOX' label."""
        try:
            with build("gmail", "v1", credentials=self.creds) as service:
                labels = service.users().labels().list(userId="me").execute()
                inbox_label_id = None
                for label in labels["labels"]:
                    if label["name"] == "INBOX":
                        inbox_label_id = label["id"]
                        break
                for message_id in message_ids:
                    service.users().messages().modify(
                        userId="me",
                        id=message_id,
                        body={"removeLabelIds": [inbox_label_id]},
                    ).execute()

        except HttpError as error:
            print(f"An error occurred: {error}")

    def check_mail(self):
        """Fetch new emails from the inbox and save them to the database."""
        try:
            with build("gmail", "v1", credentials=self.creds) as service:

                # Extract these headers
                headers = {"From", "To", "Subject", "Received", "Date", "Reply-To"}
                data = {}

                # Fetches all messages that are in the inbox (== not archived)
                results = (
                    service.users().messages().list(userId="me", q="in:inbox").execute()
                )
                if "messages" not in results:
                    print("No new mail")
                    return
                for message in results["messages"]:
                    mid = message["id"]
                    data[mid] = {}
                    data[mid]["time_added"] = int(time.time())

                    mail = (
                        service.users()
                        .messages()
                        .get(userId="me", id=message["id"])
                        .execute()
                    )
                    for header in mail["payload"]["headers"]:
                        if header["name"] in headers:
                            data[mid][header["name"]] = header["value"]
                    data[mid]["_id"] = f"{self.penpal_id}_{mid}"

                    # Customer ID must be present in the as address tag, otherwise the email data is not processed further
                    if "+" in data[mid]["To"]:
                        data[mid]["customer_id"] = (
                            data[mid]["To"].split("+")[1].split("@")[0].strip()
                        )
                        data[mid]["state"] = "new"
                    else:
                        data[mid]["customer_id"] = None
                        data[mid]["state"] = "error"
                    parts = mail["payload"].get("parts", [])
                    if len(parts) == 0:
                        if mail["payload"]["mimeType"] in self.accepted_types:
                            data[mid]["body"] = base64.urlsafe_b64decode(
                                mail["payload"]["body"]["data"]
                            ).decode("utf-8")
                    else:
                        for part in mail["payload"]["parts"]:
                            if part["mimeType"] in self.accepted_types:
                                # text/plain is prioritised
                                if part["mimeType"] == "text/plain":
                                    data[mid]["body"] = base64.urlsafe_b64decode(
                                        part["body"]["data"]
                                    ).decode("utf-8")
                                    break
                                elif part["mimeType"] == "text/html":
                                    data[mid]["body"] = base64.urlsafe_b64decode(
                                        part["body"]["data"]
                                    ).decode("utf-8")
                    # The message is not processed further if no text is found or the text is suspiciously long
                    if (
                        "body" not in data[mid]
                        or len(data[mid]["body"].split(" ")) > 5000
                    ):
                        data[mid]["state"] = "error"
                # Save the processed email data to the database
                self.db_conn.save_emails(data)
                # Archive the downloaded messages in Gmail
                self.archive_downloaded(list(data.keys()))

        except HttpError as error:
            print(f"An error occurred: {error}")


if __name__ == "__main__":
    mailer = PenpalMailer()
    while True:
        mailer.check_mail()
        time.sleep(random.random())
        mailer.send_mail()
        mailer.wait()