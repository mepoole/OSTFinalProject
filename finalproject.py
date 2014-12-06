import cgi
import urllib
import json
from google.appengine.api import users
from google.appengine.ext import ndb
import os
from google.appengine.api import images
from google.appengine.ext.webapp import template
import webapp2
from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers


DEFAULT_FORUM_NAME = 'mep505'

def forum_key(forum_name=DEFAULT_FORUM_NAME):
    return ndb.Key('forum', forum_name)
    

class Question(ndb.Model):
    author = ndb.UserProperty()
    title = ndb.StringProperty()
    content = ndb.StringProperty(indexed=False)
    tags = ndb.JsonProperty()
    image = ndb.BlobKeyProperty()
    imageURL = ndb.StringProperty()
    date = ndb.DateTimeProperty(auto_now_add=True)
    
class Answer(ndb.Model):
    author = ndb.UserProperty()
    title = ndb.StringProperty()
    content = ndb.StringProperty(indexed=False)
    image = ndb.BlobProperty()
    date = ndb.DateTimeProperty(auto_now_add=True)

class Vote(ndb.Model):
    author = ndb.UserProperty()
    vote = ndb.BooleanProperty()

class QuestionDetail(webapp2.RequestHandler):
    def get(self):
        if self.request.get('questionKey'):
            questionKey=self.request.get('questionKey')
            question=ndb.Key(urlsafe=questionKey).get()
            template_values = {
            'user' : users.get_current_user(),
            'question' : question,
        }
        
        path = os.path.join(os.path.dirname(__file__), 'QuestionDetail.html')
        self.response.out.write(template.render(path, template_values))

                
class UploadHandler(blobstore_handlers.BlobstoreUploadHandler):
  def post(self):
    question=Question(parent=forum_key())
    question.content = self.request.get('content')
    question.author=users.get_current_user()
    question.title=self.request.get('title')
    question.tags=self.request.get('tags', allow_multiple=True)
    upload_files = self.get_uploads('image')  # 'file' is file upload field in the form
    blob_info = upload_files[0]
    question.image=blob_info.key()
    question.imageURL = images.get_serving_url(blob_info.key())
    question.put()
    self.redirect('/')

class MainPage(webapp2.RequestHandler):
    def get(self):
        upload_url = blobstore.create_upload_url('/upload')
        offset=0
        entriesPerPage=10
        #variable to determine whether to add a "next" or "prev" link
        nextLink=False
        prevLink=False
        if self.request.get('offset') and self.request.get('offset') != '0':
            offset=int(self.request.get('offset'))
            prevLink=True
        questions = Question.query(ancestor=forum_key()).order(-Question.date)
        questions=questions.fetch(entriesPerPage+1, offset=offset)
        if len(questions)==entriesPerPage+1:
            offset=offset+entriesPerPage
            nextLink=True
        #for question in questions:
            #question.key.delete()
        if users.get_current_user():
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'
        
        template_values = {
            'user' : users.get_current_user(),
            'questions' : questions,
            'offset': offset,
            'nextLink': nextLink,
            'prevLink' : prevLink,
            'url': url,
            'url_linktext': url_linktext,
            'upload_url': upload_url,
        }
        
        path = os.path.join(os.path.dirname(__file__), 'index.html')
        self.response.out.write(template.render(path, template_values))
        

application = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/QuestionDetail', QuestionDetail),
    ('/upload', UploadHandler),
], debug=True)