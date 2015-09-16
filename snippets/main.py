import functools
import logging
import os
import urllib

# from google.appengine.api import users
# from google.appengine.ext import webapp
# from google.appengine.ext.webapp import template
# from google.appengine.ext.webapp import util

from flask import Flask
from flask import redirect
from flask import render_template
from flask import request
from flask.ext.sqlalchemy import SQLAlchemy

from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.mutable import Mutable


# from emails import (DigestEmail,
#                     OneDigestEmail,
#                     OneReminderEmail,
#                     ReminderEmail)
# from dateutil import date_for_retrieval
# from model import (compute_following,
#                    Snippet,
#                    User,
#                    user_from_email)


app = Flask(__name__)
app.debug = True


app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://localhost:5432/snippets'
db = SQLAlchemy(app)


class MutableList(Mutable, list):
    def append(self, value):
        list.append(self, value)
        self.changed()

    def remove(self, value):
        list.remove(self, value)
        self.changed()

    @classmethod
    def coerce(cls, key, value):
        if not isinstance(value, MutableList):
            if isinstance(value, list):
                return MutableList(value)
            return Mutable.coerce(key, value)
        else:
            return value


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    email = db.Column(db.String(120), unique=True)
    enabled = db.Column(db.Boolean())
    following = db.Column(MutableList.as_mutable(postgresql.ARRAY(db.String(80))), default=[])
    tags = db.Column(MutableList.as_mutable(postgresql.ARRAY(db.String())), default=[])
    tags_following = db.Column(MutableList.as_mutable(postgresql.ARRAY(db.String())), default=[])

    def __init__(self, username, email):
        self.username = username
        self.email = email

    def __repr__(self):
        return '<User %r>' % self.username


# class Snippet(db.Model):
#     user = db.ReferenceProperty(User)
#     text = db.TextProperty()
#     date = db.DateProperty()


def get_user(request):
    user = User.query.filter_by(username='steder').first()
    if user is None:
        user = User('steder', 'steder@gmail.com')
    db.session.add(user)
    return user


def compute_following(current_user, users):
    """Return set of email addresses being followed by this user."""
    email_set = set(current_user.following)
    print "email_set:", email_set
    tag_set = set(current_user.tags_following)
    following = set()
    for u in users:
        if ((u.email in email_set) or
                (len(tag_set.intersection(u.tags)) > 0)):
            following.add(u.email)
    print "following:", following
    return following

#
# def user_from_email(email):
#     email = email.lower()
#     logging.debug('looking up user with email %s', email)
#     return User.all().filter("email =", email).fetch(1)[0]
#
#
# def create_or_replace_snippet(user, text, date):
#     # Delete existing (yeah, yeah, should be a transaction)
#     for existing in Snippet.all().filter("date =", date).filter("user =", user).fetch(10):
#         existing.delete()
#
#     # Write new
#     snippet = Snippet(text=text, user=user, date=date)
#     snippet.put()

# def authenticated(method):
#     @functools.wraps(method)
#     def wrapper(self, *args, **kwargs):
#         # TODO: handle post requests separately
#         user = users.get_current_user()
#         if not user:
#             self.redirect(users.create_login_url(self.request.uri))
#             return None
#         return method(self, *args, **kwargs)
#     return wrapper


def commit(route):
    @functools.wraps(route)
    def wrapper(*args, **kwargs):
        try:
            r = route(*args, **kwargs)
        except:
            db.session.rollback()
            raise
        else:
            db.session.commit()
        return r
    return wrapper


@app.route("/")
@commit
def index():
    user = get_user(request)

    # Update tags if sent
    tags = request.args.get('tags')
    if tags is not None:
        user.tags = [s.strip() for s in tags.split(',')]
    # Fetch user list and display
    raw_users = User.query.order_by('email').limit(500)
    following = compute_following(user, raw_users)
    all_users = [(u, u.email in following) for u in raw_users]
    all_tags = set()
    for u in raw_users:
        all_tags.update(u.tags)

    all_tags = [(t, t in user.tags_following) for t in all_tags]

    template_values = {
        'current_user' : user,
        'all_users': all_users,
        'all_tags': all_tags
    }
    return render_template('index.html', **template_values)


@app.route('/follow')
@commit
def follow():
    """Follow a user or tag."""
    user = get_user(request)
    desired_tag = request.args.get('tag')
    desired_user = request.args.get('user')
    continue_url = request.args.get('continue')

    if desired_tag and (desired_tag not in user.tags_following):
        user.tags_following.append(desired_tag)

    if desired_user and (desired_user not in user.following):
        user.following.append(desired_user)

    return redirect(continue_url)


@app.route("/unfollow")
@commit
def unfollow():
    user = get_user(request)
    desired_tag = request.args.get('tag')
    desired_user = request.args.get('user')
    continue_url = request.args.get('continue')

    if desired_tag and (desired_tag in user.tags_following):
        user.tags_following.remove(desired_tag)

    if desired_user and (desired_user in user.following):
        user.following.remove(desired_user)

    return redirect(continue_url)


@app.route("/foobar")
def user_snippets(email):
    """Show a given user's snippets."""

    user = get_user(request)
    email = urllib.unquote_plus(email)
    desired_user = user_from_email(email)
    snippets = desired_user.snippet_set
    snippets = sorted(snippets, key=lambda s: s.date, reverse=True)
    following = email in user.following
    tags = [(t, t in user.tags_following) for t in desired_user.tags]

    template_values = {
        'current_user' : user,
        'user': desired_user,
        'snippets': snippets,
        'following': following,
        'tags': tags
    }
    render_template('user.html', **template_values)


# class TagHandler(BaseHandler):
#     """View this week's snippets in a given tag."""
#     @authenticated
#     def get(self, tag):
#         user = self.get_user()
#         d = date_for_retrieval()
#         all_snippets = Snippet.all().filter("date =", d).fetch(500)
#         if (tag != 'all'):
#             all_snippets = [s for s in all_snippets if tag in s.user.tags]
#         following = tag in user.tags_following

#         template_values = {
#                            'current_user' : user,
#                            'snippets': all_snippets,
#                            'following': following,
#                            'tag': tag
#                            }
#         self.render('tag', template_values)


# def main():
#     logging.getLogger().setLevel(logging.DEBUG)
#     application = webapp.WSGIApplication(
#                                          [('/', MainHandler),
#                                           ('/user/(.*)', UserHandler),
#                                           ('/tag/(.*)', TagHandler),
#                                           ('/follow', FollowHandler),
#                                           ('/unfollow', UnfollowHandler),
#                                           ('/reminderemail', ReminderEmail),
#                                           ('/digestemail', DigestEmail),
#                                           ('/onereminder', OneReminderEmail),
#                                           ('/onedigest', OneDigestEmail)],
#                                           debug=True)
#     util.run_wsgi_app(application)

