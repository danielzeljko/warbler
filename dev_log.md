Logout Bugs:
    1. Wrong method being used
    2. Added CSRF form to g
    3. Created CSRF form in forms

Profile Bugs:
    1. Fixed user bio and location
    2. Fixed header image in user detail page
    3. Fixed editing of user profile

User Cards:
    1. Fix user bio not appearing

Home page:
    1. Fixed home page for when user logged. Messages only being shown from followed users and logged in user.


How is the logged in user being kept track of?
 - First the user's instance is added to the session inside of `do_login`. Secondly, the user is being added to the `g` object in every request that is made in the `before_request` method.

What is Flask’s g object?
 - G object is an application context where we can store data for every request. Its a one-time use-case for every request being made. It gets torn down after the request is made.

What is the purpose of add_user_to_g?
 - It keeps track of if a user is logged in. If a user is logged in, the user is then assigned to the `g.user` key-value as the user's instance.

What does @app.before_request mean?
 - Before every request is made, it is a decorator that that will execute before every request. It is similar to unittest's `setup` feature (typically paired with `tear down`)


 Likes:
    1. created like_messages.html
    2. create post route to lke a message.


12/15/22
1. Changed model relationships
    - user.liked_messages
2. Show like button on homepage as well
3. Updated like views to use new model relationships
