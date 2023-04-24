import os
import time

import pymongo


class DiscussionSummary:
    """
    A class to handle discussion summaries in a MongoDB database.
    Summary is constantly updated upon customer interaction with the
    penpal. Only one summary exists per customer/penpal pair and
    the generation is non-deterministic. Summaries are used as clues
    for the penpal about past conversations.
    """

    def __init__(self):
        db_hostname = os.environ.get("MAIL_DB_HOSTNAME")
        db_port = os.environ.get("MAIL_DB_PORT")
        db_name = os.environ.get("MAIL_DB_NAME")
        db_user = os.environ.get("MAIL_DB_USER")
        db_password = os.environ.get("MAIL_DB_PASSWORD")
        self.mongo_db_uri = (
            f"mongodb://{db_user}:{db_password}@{db_hostname}:{db_port}/{db_name}"
        )

    def _add_summary(self, customer_id, penpal_id, summary):
        """
        Add a new summary to the database.

        :param customer_id: The ID of the customer.
        :param penpal_id: The ID of the penpal.
        :param summary: The summary text.
        :return: The result of the insertion operation.
        """
        with pymongo.MongoClient(self.mongo_db_uri) as client:
            db = client.robomail
            summaries = db.discussion_summaries

            temp_sum = {
                "customer_id": customer_id,
                "penpal_id": penpal_id,
                "summary": summary,
                "time_added": int(time.time()),
                "time_modified": int(time.time()),
                "iteration": 1,
            }

            return summaries.insert_one(temp_sum)

    def update_summary(self, customer_id, penpal_id, summary):
        """
        Update an existing summary or add a new one if it doesn't exist.

        :param customer_id: The ID of the customer.
        :param penpal_id: The ID of the penpal.
        :param summary: The updated summary text.
        :return: The result of the update or insertion operation.
        """
        with pymongo.MongoClient(self.mongo_db_uri) as client:
            db = client.robomail
            if self.summary_exists(customer_id, penpal_id):
                return db.discussion_summaries.update_one(
                    {"customer_id": customer_id, "penpal_id": penpal_id},
                    {
                        "$set": {"summary": summary, "time_modified": int(time.time())},
                        "$inc": {"iteration": 1},
                    },
                )
            else:
                return self._add_summary(customer_id, penpal_id, summary)

    def get_summary(self, customer_id, penpal_id):
        """
        Retrieve a summary from the database.

        :param customer_id: The ID of the customer.
        :param penpal_id: The ID of the penpal.
        :return: The summary document, or None if not found.
        """
        with pymongo.MongoClient(self.mongo_db_uri) as client:
            db = client.robomail
            return db.discussion_summaries.find_one(
                {"customer_id": customer_id, "penpal_id": penpal_id}
            )

    def summary_exists(self, customer_id, penpal_id):
        """
        Check whether a summary for a customer/penpal pair already exists.

        :param customer_id: The ID of the customer.
        :param penpal_id: The ID of the penpal.
        :return: True if a customer/penpal pair already has a summary and otherwise false.
        """
        with pymongo.MongoClient(self.mongo_db_uri) as client:
            db = client.robomail
            return (
                db.discussion_summaries.find_one(
                    {"customer_id": customer_id, "penpal_id": penpal_id}
                )
                != None
            )
