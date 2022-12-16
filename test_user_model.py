"""User model tests."""

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


class UserModelTestCase(TestCase):
    def setUp(self):
        User.query.delete()

        u1 = User.signup("u1", "u1@email.com", "password", None)
        u2 = User.signup("u2", "u2@email.com", "password", None)

        db.session.commit()
        self.u1_id = u1.id
        self.u2_id = u2.id

        self.u1 = u1
        self.u2 = u2

        self.client = app.test_client()

    def tearDown(self):
        db.session.rollback()

    def test_user_model(self):
        """ Test fresh user with no messages and followers """
        u1 = User.query.get(self.u1_id)

        # User should have no messages & no followers
        self.assertEqual(len(u1.messages), 0)
        self.assertEqual(len(u1.followers), 0)


    def test_is_not_following(self):
        """ Test u1 not following u2"""
        self.assertEqual(self.u1.is_following(self.u2), False)


    def test_is_following(self):
        """ Test u1 following u2 """
        self.u1.following.append(self.u2)
        self.assertEqual(self.u1.is_following(self.u2), True)

    def test_is_followed_by(self):
        """ Test u2 following u1"""

        self.u1.followers.append(self.u2)
        self.assertEqual(self.u1.is_followed_by(self.u2), True)

    def test_is_not_followed_by(self):
        """ Test u2 not following u1"""
        self.assertEqual(self.u1.is_followed_by(self.u2), False)


    def test_user_signed_up(self):
        """ Test user signed up successfully """
        self.assertIsInstance(self.u1, User)

    def test_user_empty_password(self):
        """
        Does User.signup fail to create a new user if password empty?
        """

        with self.assertRaises(ValueError):
            User.signup("notCoolUser", "niki@manaj.com", "", None)
            db.session.commit()

    def test_user_username_duplicates(self):
        """
        Does User.signup fail to create a new user if username already taken?
        """

        # note: must be imported from correct library
        with self.assertRaises(SQLIntegrityError):
            User.signup("notCoolUser", "niki@manaj.com", "asdasd", None)
            User.signup("notCoolUser", "asdasd@manaj.com", "asdasd", None)
            db.session.commit()

    def test_user_email_duplicates(self):
        """
        Does User.signup fail to create a new user if email already taken?
        """
        with self.assertRaises(SQLIntegrityError):
            User.signup("notCoolUser", "niki@mansdaj.com", "asdasd", None)
            User.signup("asdasdasda", "niki@mansdaj.com", "asdasd", None)
            db.session.commit()


    def test_user_authentication_valid_data(self):
        """
        Does User.authenticate successfully return a user
        when given a valid username and password?
        """