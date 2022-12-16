import os
from dotenv import load_dotenv

from flask import Flask, jsonify, render_template, request, flash, redirect, session, g
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError

from forms import UserAddForm, LoginForm, MessageForm, CSRFOnlyForm, UserEditForm
from models import db, connect_db, User, Message, Like

load_dotenv()

CURR_USER_KEY = "curr_user"

app = Flask(__name__)

# Get DB_URI from environ variable (useful for production/testing) or,
# if not set there, use development local db.
app.config['DEBUG'] = True
# db = SQLAlchemy(SQLALCHEMY_URI, app=app, record_queries=True)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = (
    os.environ['DATABASE_URL'].replace("postgres://", "postgresql://"))
app.config['SQLALCHEMY_ECHO'] = False
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = True
app.config['SECRET_KEY'] = os.environ['SECRET_KEY']
app.config['SQLALCHEMY_RECORD_QUERIES'] = True
toolbar = DebugToolbarExtension(app)

connect_db(app)


##############################################################################
# User signup/login/logout


@app.before_request
def add_user_to_g():
    """If we're logged in, add curr user to Flask global."""
    # breakpoint()
    if CURR_USER_KEY in session: # creates single source of truth throughout entire session. by setting user through user id in session
        g.user = User.query.get(session[CURR_USER_KEY])

    else:
        g.user = None

@app.before_request
def add_csrf_form_to_g():
    """ Add CSRF form to Flask global. """
    g.csrf_form = CSRFOnlyForm()


def do_login(user):
    """Log in user."""

    session[CURR_USER_KEY] = user.id


def do_logout():
    """Log out user."""

    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]


@app.route('/signup', methods=["GET", "POST"])
def signup():
    """Handle user signup.

    Create new user and add to DB. Redirect to home page.

    If form not valid, present form.

    If there already is a user with that username: flash message
    and re-present form.
    """

    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]
    form = UserAddForm()

    if form.validate_on_submit():
        try:
            user = User.signup(
                username=form.username.data,
                password=form.password.data,
                email=form.email.data,
                image_url=form.image_url.data or User.image_url.default.arg,
            )
            db.session.commit()

        except IntegrityError:
            flash("Username already taken", 'danger')
            return render_template('users/signup.html', form=form)

        do_login(user)

        return redirect("/")

    else:
        return render_template('users/signup.html', form=form)


@app.route('/login', methods=["GET", "POST"])
def login():
    """Handle user login and redirect to homepage on success."""

    form = LoginForm()

    if form.validate_on_submit():
        user = User.authenticate(
            form.username.data,
            form.password.data)

        if user:
            do_login(user)
            flash(f"Hello, {user.username}!", "success")
            return redirect("/")

        flash("Invalid credentials.", 'danger')

    return render_template('users/login.html', form=form)


@app.post('/logout')
def logout():
    """Handle logout of user and redirect to homepage."""

    # IMPLEMENT THIS AND FIX BUG
    # DO NOT CHANGE METHOD ON ROUTE

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    # Note: Added csrf form to g
    form = g.csrf_form

    if form.validate_on_submit():
        # breakpoint()
        flash("You have successfully logged out.")
        do_logout()

    return redirect("/")




##############################################################################
# General user routes:

@app.get('/users')
def list_users():
    """Page with listing of users.

    Can take a 'q' param in querystring to search by that username.
    """

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    search = request.args.get('q')

    if not search:
        users = User.query.all()
    else:
        users = User.query.filter(User.username.like(f"%{search}%")).all()

    return render_template('users/index.html', users=users)


@app.get('/users/<int:user_id>')
def show_user(user_id):
    """Show user profile."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    user = User.query.get_or_404(user_id)

    return render_template('users/show.html', user=user)


@app.get('/users/<int:user_id>/following')
def show_following(user_id):
    """Show list of people this user is following."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    user = User.query.get_or_404(user_id)
    return render_template('users/following.html', user=user)


@app.get('/users/<int:user_id>/followers')
def show_followers(user_id):
    """Show list of followers of this user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    user = User.query.get_or_404(user_id)
    return render_template('users/followers.html', user=user)


@app.post('/users/follow/<int:follow_id>')
def start_following(follow_id):
    """Add a follow for the currently-logged-in user.

    Redirect to following page for the current user.
    """

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    followed_user = User.query.get_or_404(follow_id)
    g.user.following.append(followed_user)
    db.session.commit()

    return redirect(f"/users/{g.user.id}/following")


@app.post('/users/stop-following/<int:follow_id>')
def stop_following(follow_id):
    """Have currently-logged-in-user stop following this user.

    Redirect to following page for the current user.
    """

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    followed_user = User.query.get(follow_id)
    g.user.following.remove(followed_user)
    db.session.commit()

    return redirect(f"/users/{g.user.id}/following")


@app.route('/users/profile', methods=["GET", "POST"])
def profile():
    """
    Update profile for current user.
    Password has to be entered and be correct for profile to update.
    """

    if not g.user: # confirms user is logged in vs session where user could be loggedout.
        flash("Access unauthorized.", "danger")
        return redirect("/")

    # user = User.query.get(g.user.id)
    form = UserEditForm(obj=g.user)


    if form.validate_on_submit():

        password = form.password.data

        if User.authenticate(username=g.user.username, password=password):
            g.user.username = form.data.get("username", g.user.username)
            g.user.email = form.data.get("email", g.user.email)
            g.user.image_url = form.data.get("image_url", g.user.image_url)
            g.user.header_image_url = form.data.get("header_image_url", g.user.header_image_url)
            g.user.bio = form.data.get("bio", g.user.bio)

            db.session.commit()

            return redirect(f"/users/{g.user.id}")
        else:
            flash("Password is not correct. Please try again.")

    return render_template("users/edit.html", form=form)


@app.post('/users/delete')
def delete_user():
    """Delete user.

    Redirect to signup page.
    """

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    do_logout()

    db.session.delete(g.user)
    db.session.commit()

    return redirect("/signup")


##############################################################################
# Messages routes:

@app.route('/messages/new', methods=["GET", "POST"])
def add_message():
    """Add a message:

    Show form if GET. If valid, update message and redirect to user page.
    """

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    form = MessageForm()

    if form.validate_on_submit():
        msg = Message(text=form.text.data)
        g.user.messages.append(msg)
        db.session.commit()

        return redirect(f"/users/{g.user.id}")

    return render_template('messages/create.html', form=form)


@app.get('/messages/<int:message_id>')
def show_message(message_id):
    """Show a message."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    msg = Message.query.get_or_404(message_id)

    liked_messages_ids = [message.id for message in g.user.liked_messages ]

    if message_id in liked_messages_ids: #able to add property on objects as a one time thing
        msg.is_liked = True
    else:
        msg.is_liked = False

    return render_template('messages/show.html', message=msg)


@app.post('/messages/<int:message_id>/delete')
def delete_message(message_id):
    """Delete a message.

    Check that this message was written by the current user.
    Redirect to user page on success.
    """

    msg = Message.query.get_or_404(message_id)

    if not g.user or g.user.id != msg.user_id:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    db.session.delete(msg)
    db.session.commit()

    return redirect(f"/users/{g.user.id}")


@app.post('/messages/<int:message_id>/like')
def like_message(message_id):
    """ Allows a user to “like” or "unlike" a warble.
        Returns: Redirect to "/"
    """

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    message = Message.query.get_or_404(message_id)

    if message.user == g.user:
        flash("You cannot like your own warble.", "danger")
        return redirect("/")


    form = g.csrf_form

    if form.validate_on_submit():

        # get all message_ids of liked messages
        # like_message_ids = [message.id for message in g.user.liked_messages]

        # Like.query.get(message_id=message., ) in g.user.like

        if message in g.user.liked_messages:
        # if message_id in like_message_ids:
            g.user.liked_messages.remove(message)
            # db.session.commit()
        else:
            # handles unfilled star
            g.user.liked_messages.append(message) #adding message to a list of messages (users's liked messages)

        db.session.commit()

    return redirect(f"/users/{g.user.id}")

@app.get('/users/<int:user_id>/likes')
def list_like_messages(user_id):
    """Shows list of liked messages"""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    user = User.query.get_or_404(user_id)

    return render_template('messages/liked_messages.html', user=user)





##############################################################################
# Homepage and error pages


@app.get('/')
def homepage():
    """Show homepage:

    - anon users: no messages
    - logged in: 100 most recent messages of followed_users
    """


    if g.user:
        following_users_id = [user.id for user in g.user.following]+[g.user.id]

        messages = (Message
                    .query
                    .filter(Message.user_id.in_(following_users_id))
                    .order_by(Message.timestamp.desc())
                    .limit(100)
                    .all())

        # TODO: I don't like this b/c it doesn't seem efficient

        liked_messages_ids = [message.id for message in g.user.liked_messages]

        for message in messages:
            if message.id in liked_messages_ids:
                message.is_liked = True
            else:
                message.is_liked = False

        return render_template('home.html', messages=messages)

    else:
        return render_template('home-anon.html')



@app.errorhandler(404)
def page_note_found(e):
    """ Show a custom 404 page """
    return render_template("404.html")



##############################################################################
# Turn off all caching in Flask
#   (useful for dev; in production, this kind of stuff is typically
#   handled elsewhere)
#
# https://stackoverflow.com/questions/34066804/disabling-caching-in-flask

@app.after_request
def add_header(response):
    """Add non-caching headers on every request."""

    # https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Cache-Control
    response.cache_control.no_store = True
    return response




# ============================= API ===============================

@app.post('/api/messages/<int:message_id>/like')
def like_message_api(message_id):
    """
    Allows a user to “like” or "unlike" a warble.

    Returns: {message: {id, text, user_id }}
    """

    # TODO: refactor this

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    message = Message.query.get_or_404(message_id)

    if message.user == g.user:
        flash("You cannot like your own warble.", "danger")
        return redirect("/")

    serialized = message.serialize()

    return (jsonify(message=serialized), 201)