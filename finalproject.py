import cgi
import urllib
import json
from google.appengine.api import users
from google.appengine.ext import ndb
import os
from google.appengine.ext.webapp import template
import webapp2

DEFAULT_FORUM_NAME = 'mep505'

def forum_key(forum_name=DEFAULT_FORUM_NAME):
    return ndb.Key('forum', forum_name)

class Question(ndb.Model):
    author = ndb.UserProperty()
    title = ndb.StringProperty(indexed=False)
    content = ndb.StringProperty(indexed=False)
    tags = ndb.JsonProperty()
    date = ndb.DateTimeProperty(auto_now_add=True)
    
class Answer(ndb.Model):
    author = ndb.UserProperty()
    title = ndb.StringProperty(indexed=False)
    content = ndb.StringProperty(indexed=False)
    date = ndb.DateTimeProperty(auto_now_add=True)

class Vote(ndb.Model):
    author = ndb.UserProperty()
    vote = ndb.BooleanProperty()

class NewQuestion (webapp2.RequestHandler):
    def post(self):
        if users.get_current_user():
            question=Question(parent=forum_key())
            question.content = self.request.get('content')
            question.author=users.get_current_user()
            question.title=self.request.get('title')
            question.put()
        self.redirect('/')

class QuestionDetail(webapp2.RequestHandler):
    def get(self):
        question=self.request.get('question')

class MainPage(webapp2.RequestHandler):
    def get(self):
        questions = Question.query(ancestor=forum_key()).order(-Question.date)
        if users.get_current_user():
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'
        
        template_values = {
            'user' : users.get_current_user(),
            'questions' : questions,
            'url': url,
            'url_linktext': url_linktext,
        }
        
        path = os.path.join(os.path.dirname(__file__), 'index.html')
        self.response.out.write(template.render(path, template_values))
        

application = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/NewQuestion', NewQuestion),
    ('/QuestionDetail', QuestionDetail),
], debug=True)