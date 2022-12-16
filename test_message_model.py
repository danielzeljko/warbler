"""Message model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase

from models import db, User, Message, Follows, connect_db

from psycopg2.errors import UniqueViolation

from sqlalchemy.exc import IntegrityError as SQLIntegrityError

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler_test"

# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

connect_db(app)

db.drop_all()
db.create_all()


class MessageModelTestCase(TestCase):
    def setUp(self):
        Message.query.delete()
        User.query.delete()

        u1 = User.signup("u1", "u1@email.com", "password", None)

        db.session.commit()
        self.u1_id = u1.id
        self.u1 = u1

        self.client = app.test_client()

    def tearDown(self):
        db.session.rollback()

    def test_adding_message(self):

        new_msg = Message(user_id=self.u1_id, text="test")
        db.session.add(new_msg)
        db.session.commit()

        self.assertIn(new_msg, self.u1.messages)

    def test_message_empty_text(self):
        with self.assertRaises(SQLIntegrityError):
            new_msg = Message(user_id=self.u1_id, text=None)
            db.session.add(new_msg)
            db.session.commit()

