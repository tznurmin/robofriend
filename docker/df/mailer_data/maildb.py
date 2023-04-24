import os

import pymongo


class MailDB:
    """
    MailDB is a class that handles email-related database operations.
    It provides methods for saving, finding, and updating email records in a MongoDB database.
    Use environment variables to define the critical parameters for operation.
    """

    def __init__(self):
        """
        Initialise MailDB object by fetching database connection details from environment variables
        and constructing the MongoDB connection URI.
        """
        db_hostname = os.environ.get("MAIL_DB_HOSTNAME")
        db_port = os.environ.get("MAIL_DB_PORT")
        db_name = os.environ.get("MAIL_DB_NAME")
        db_user = os.environ.get("MAIL_DB_USER")
        db_password = os.environ.get("MAIL_DB_PASSWORD")
        self.mongo_db_uri = (
            f"mongodb://{db_user}:{db_password}@{db_hostname}:{db_port}/{db_name}"
        )

    def save_emails(self, mails):
        """
        Save emails to the database.

        :param mails: Dictionary containing email objects with unique keys.
        :return: List of ObjectIds of the inserted emails.
        """
        ids = []
        with pymongo.MongoClient(self.mongo_db_uri) as client:
            db = client.robomail
            mails_db = db.mails

            for mid in mails:
                new_email = mails[mid]
                ids.append(mails_db.insert_one(new_email).inserted_id)
            return ids

    def find_new_emails(self):
        """
        Find new emails in the database.

        :return: List of new email records.
        """
        with pymongo.MongoClient(self.mongo_db_uri) as client:
            db = client.robomail
            mails_db = db.mails
            return [mail for mail in mails_db.find({"state": "new"})]

    def find_emails_by_customer_id(self, customer_id):
        """
        Find emails by customer_id in the database.

        :param customer_id: Unique identifier of the customer.
        :return: List of email records associated with the given customer_id, sorted by time_added in ascending order.
        """
        with pymongo.MongoClient(self.mongo_db_uri) as client:
            db = client.robomail
            mails_db = db.mails
            return [
                mail
                for mail in mails_db.find({"customer_id": customer_id}).sort(
                    "time_added", pymongo.ASCENDING
                )
            ]

    def outgoing_email(self):
        """
        Find outgoing emails in the database.

        :return: List of pending email records.
        """
        with pymongo.MongoClient(self.mongo_db_uri) as client:
            db = client.robomail
            mails_db = db.mails
            return [mail for mail in mails_db.find({"state": "pending"})]

    def first_email(self, customer_id):
        """
        Check if it's the first email for a given customer_id.
        Initial exchange if only one email found from the DB.

        :param customer_id: Unique identifier of the customer.
        :return: True if it's the first email for the given customer_id, otherwise False.
        """
        with pymongo.MongoClient(self.mongo_db_uri) as client:
            db = client.robomail
            mails_db = db.mails
            return (
                len([mail for mail in mails_db.find({"customer_id": customer_id})]) < 2
            )

    def find_email(self, mid):
        """
        Find an email by its unique ID.

        :param mid: Unique identifier of the email.
        :return: Email record associated with the given mid, or None if not found.
        """
        with pymongo.MongoClient(self.mongo_db_uri) as client:
            db = client.robomail
            mails_db = db.mails
            return mails_db.find_one({"_id": mid})

    def add_mail_bullets(self, m_id, bullets):
        """
        Add bullet points to an already existing email.

        :param m_id: Unique identifier of the email.
        :param bullets: List of bullet points to be added to the email.
        """
        self.update_email(m_id, {"bullets": bullets})

    def update_email(self, m_id, new_data):
        """
        Update email data with new_data.

        :param m_id: Unique identifier of the email.
        :param new_data: Dictionary containing the new data to be updated in the email record.
        """
        with pymongo.MongoClient(self.mongo_db_uri) as client:
            db = client.robomail
            mails_db = db.mails
            mails_db.update_one({"_id": m_id}, {"$set": new_data})
