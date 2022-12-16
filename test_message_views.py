"""Message View tests."""

# run these tests like:
#
#    FLASK_DEBUG=False python -m unittest test_message_views.py


import os
from unittest import TestCase

from models import db, Message, User, connect_db

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler_test"

# Now we can import app

from app import app, CURR_USER_KEY

app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

# This is a bit of hack, but don't use Flask DebugToolbar

app.config['DEBUG_TB_HOSTS'] = ['dont-show-debug-toolbar']

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

connect_db(app)

db.drop_all()
db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class MessageBaseViewTestCase(TestCase):
    def setUp(self):
        User.query.delete()

        u1 = User.signup("u1", "u1@email.com", "password", None)
        u2 = User.signup("u2", "u2@email.com", "password", None)

        db.session.flush()

        m1 = Message(text="m1-text", user_id=u1.id)
        db.session.add_all([m1])
        db.session.commit()

        self.u1_id = u1.id
        self.m1_id = m1.id

        self.u1 = u1
        self.m1 = m1

        self.u2 = u2

        self.client = app.test_client()


class MessageAddViewTestCase(MessageBaseViewTestCase):
    def test_add_message(self):
        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:
        with self.client as client:
            with client.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            # Now, that session setting is saved, so we can have
            # the rest of ours test
            resp = client.post("/messages/new", data={"text": "Hello"}, follow_redirects=True)

            self.assertEqual(resp.status_code, 200)

            message = Message.query.filter_by(text="Hello").one()
            html = resp.get_data(as_text=True)
            self.assertIn(message.text, html)

    def test_add_message_invalid_data(self):
        """Submits message with invalid data"""

        with self.client as client:
            with client.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id
            resp = client.post("/messages/new", data={"text": ""})
            html = resp.get_data(as_text=True)
            self.assertIn("This field is required.", html)
            self.assertEqual(resp.status_code, 200)

    def test_add_message_not_authenticated(self):
        """Submits message with invalid data"""

        with self.client as client:
            resp = client.post("/messages/new", data={"text": "test"}, follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.request.path, "/")


    def test_show_message(self):
        """Check message shows up on page when authenticated"""

        with self.client as client:
            with client.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            resp = client.get(f'/messages/{self.m1_id}')
            self.assertEqual(resp.status_code, 200)
            html = resp.get_data(as_text=True)
            message = Message.query.get(self.m1_id)
            self.assertIn(message.text, html)


    def test_delete_message(self):
        """Check message was deleted successfully when authenticated"""

        with self.client as client:
            with client.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            # messages = self.u1.messages # <-- if assigned, this copy will get stored in memorey
            resp = client.post(f'/messages/{self.m1_id}/delete', follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            html = resp.get_data(as_text=True)
            self.assertIn(self.u1.username, html)

            self.assertEqual(len(self.u1.messages), 0)

    def test_delete_message_not_authenticated(self):
        """Test delete message when not authenticated """

        with self.client as client:
            resp = client.post(f"/messages/{self.m1_id}/delete", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.request.path, "/")


    def test_delete_message_different_user(self):
        """Check message was not deleted for wrong user"""

        with self.client as client:
            with client.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u2.id

            resp = client.post(f'/messages/{self.m1_id}/delete', follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(len(self.u1.messages), 1)
