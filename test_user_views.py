"""User View tests."""

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


class UserBaseViewTestCase(TestCase):
    def setUp(self):
        User.query.delete()

        u1 = User.signup("u1", "u1@email.com", "password", None)
        u2 = User.signup("u2", "u2@email.com", "password", None)
        u3 = User.signup("u3", "u3@email.com", "password", None)
        u4 = User.signup("u4", "u4@email.com", "password", None)

        db.session.flush()
        db.session.commit()

        self.u1_id = u1.id
        self.u2_id = u2.id
        self.u3_id = u3.id
        self.u4_id = u4.id

        self.u1 = u1
        self.u2 = u2
        self.u3 = u3
        self.u4 = u4

        self.client = app.test_client()


class UserFollowUnfollowTestCase(UserBaseViewTestCase):
    def test_see_followers_page(self):
        """Test to go to other user's followers page when logged in"""
        with self.client as client:
            with client.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            resp_follow = client.post(f"/users/follow/{self.u2_id}", follow_redirects=True)
            self.assertEqual(resp_follow.status_code, 200)

            resp_followers_page = client.get(f"/users/{self.u2_id}/followers")
            resp_followers_page_html = resp_followers_page.get_data(as_text=True)
            self.assertIn(self.u1.username, resp_followers_page_html)
            self.assertEqual(resp_followers_page.status_code, 200)


    def test_cant_followers_page_not_logged_in(self):
        """test to not be able to go to other user's followers page when not logged in"""
        with self.client as client:
            resp = client.get(f"/users/{self.u2_id}/followers", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.request.path, "/")



    # // When you’re logged in, can you see the follower / following pages for any user?
    # // When you’re logged out, are you disallowed from visiting a user’s follower / following pages?