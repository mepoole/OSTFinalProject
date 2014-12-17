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
from google.appengine.ext.blobstore import BlobInfo
from google.appengine.ext.webapp import blobstore_handlers
template.register_template_library('templatetags.imagerender')
import urllib2


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
    modDate= ndb.DateTimeProperty(auto_now=True)
    
class Answer(ndb.Model):
    author = ndb.UserProperty()
    title = ndb.StringProperty()
    content = ndb.StringProperty(indexed=False)
    image = ndb.BlobKeyProperty()
    imageURL = ndb.StringProperty()
    date = ndb.DateTimeProperty(auto_now_add=True)
    modDate= ndb.DateTimeProperty(auto_now=True)

class Vote(ndb.Model):
    author = ndb.UserProperty()
    voteType = ndb.StringProperty()
    #true if an up vote, false if a down vote
    vote = ndb.BooleanProperty()

class Favorites(ndb.Model):
    author = ndb.UserProperty()
    question=ndb.KeyProperty(kind=Question)
    
class Image (webapp2.RequestHandler):
    def get(self):
        if self.request.get('questionKey'):
            questionKey=self.request.get('questionKey')
            question=ndb.Key(urlsafe=questionKey).get()
            self.redirect(str(question.imageURL))
        
class QuestionDetail(webapp2.RequestHandler):
    def get(self):
        if self.request.get('questionKey'):
            questionKey=self.request.get('questionKey')
            question=ndb.Key(urlsafe=questionKey).get()
            votes = Vote.query(ancestor=question.key).fetch()
            questionUp=0
            questionDown=0
            for vote in votes:
                if vote.vote:
                    questionUp += 1
                else:
                    questionDown += 1
            questionVotes=(questionUp, questionDown)
            template_values = {
            'user' : users.get_current_user(),
            'question' : question,
            'questionVotes' : questionVotes
        }
        
            path = os.path.join(os.path.dirname(__file__), 'QuestionDetail.html')
            self.response.out.write(template.render(path, template_values))

class QuestionActivity(webapp2.RequestHandler):
    def get(self):
        if self.request.get('questionKey'):
            upload_url = blobstore.create_upload_url('/upload')
            questionKey=ndb.Key(urlsafe=self.request.get('questionKey'))
            question=questionKey.get()
            votes = Vote.query(Vote.voteType=="question", ancestor=questionKey).fetch()
            questionUp=0
            questionDown=0
            for vote in votes:
                if vote.vote:
                    questionUp += 1
                else:
                    questionDown += 1
            questionVotes=(questionUp, questionDown)
            answers = Answer.query(ancestor=questionKey).order(-Answer.date)
            answerVotes = Vote.query(ancestor=questionKey).fetch()
            #create a list to store answers, and total number of votes for them
            answersAndVotes=[]
            for answer in answers:
                answerVotes = Vote.query(ancestor=answer.key).fetch()
                totalUp=0
                totalDown=0
                for vote in answerVotes:
                    if vote.vote:
                        totalUp += 1
                    else:
                        totalDown += 1
                answersAndVotes.append((answer, totalUp, totalDown))
            #sort answers by difference between up and down votes
            answersAndVotes.sort(key=lambda a: a[2] - a[1])
            
            if users.get_current_user():
                loginUrl = users.create_logout_url(self.request.uri)
                loginUrl_linktext = 'Logout'
            else:
                loginUrl = users.create_login_url(self.request.uri)
                loginUrl_linktext = 'Login'
            template_values = {
            'user' : users.get_current_user(),
            'question' : question,
            'questionVotes' : questionVotes,
            'answersAndVotes' : answersAndVotes,
            'answers' : answers,
            'upload_url' : upload_url,
            'loginUrl': loginUrl,
            'loginUrl_linktext': loginUrl_linktext,
        }
        
            path = os.path.join(os.path.dirname(__file__), 'QuestionActivity.html')
            self.response.out.write(template.render(path, template_values))

class Edit(webapp2.RequestHandler):
    def get(self):
        if self.request.get('key'):
            upload_url = blobstore.create_upload_url('/upload')
            key=ndb.Key(urlsafe=self.request.get('key'))
            item=key.get()
            template_values = {
            'user' : users.get_current_user(),
            'upload_url' : upload_url,
            'item' : item,
            'type' : self.request.get('type'),
        }
            path = os.path.join(os.path.dirname(__file__), 'Edit.html')
            self.response.out.write(template.render(path, template_values))
    
class UploadHandler(blobstore_handlers.BlobstoreUploadHandler):
    #handles all question and answer creations and edits
  def post(self):
    #new question being submitted
    if self.request.get('form') == 'question':
        question=Question(parent=forum_key())
        question.content = self.request.get('content')
        question.author=users.get_current_user()
        question.title=self.request.get('title')
        question.tags=self.request.get('tags', allow_multiple=True)
        upload_files = self.get_uploads('image')
        if upload_files:
            blob_info = upload_files[0]
            question.image=blob_info.key()
            question.imageURL = images.get_serving_url(blob_info.key())
        question.put()
        self.redirect('/')
    #new answer being submitted
    elif self.request.get('form') == 'answer':
        answer=Answer(parent=ndb.Key(urlsafe=self.request.get('questionKey')))
        answer.content = self.request.get('content')
        answer.author=users.get_current_user()
        answer.title=self.request.get('title')
        upload_files = self.get_uploads('image')
        if upload_files:
            blob_info = upload_files[0]
            answer.image=blob_info.key()
            answer.imageURL = images.get_serving_url(blob_info.key())
        answer.put()
        redirectURL = "/QuestionActivity?questionKey=%s" % self.request.get('questionKey')
        self.redirect(redirectURL)
    #answer edit submitted
    elif self.request.get('form') == 'editAnswer':
        answerKey=ndb.Key(urlsafe=self.request.get('key'))
        answer=answerKey.get()
        answer.content = self.request.get('content')
        answer.title=self.request.get('title')
        upload_files = self.get_uploads('image')
        if upload_files:
            blob_info = upload_files[0]
            answer.image=blob_info.key()
            answer.imageURL = images.get_serving_url(blob_info.key())
        answer.put()
        redirectURL = "/QuestionActivity?questionKey=%s" % answerKey.parent().urlsafe()
        self.redirect(redirectURL)
    #question edit submitted
    elif self.request.get('form') == 'editQuestion':
        question=ndb.Key(urlsafe=self.request.get('key')).get()
        question.content = self.request.get('content')
        question.author=users.get_current_user()
        question.title=self.request.get('title')
        question.tags=self.request.get('tags', allow_multiple=True)
        upload_files = self.get_uploads('image')
        if upload_files:
            blob_info = upload_files[0]
            question.image=blob_info.key()
            question.imageURL = images.get_serving_url(blob_info.key())
        question.put()
        self.redirect('/')

class ProcessVote(webapp2.RequestHandler):
    def post(self):
        if self.request.get('key'):
            #check to see if vote already exists
            getVote = Vote.query(Vote.author==users.get_current_user(), Vote.voteType ==self.request.get('type'), ancestor=ndb.Key(urlsafe=self.request.get('key'))).get()         
            if getVote:
                if self.request.get('vote') == "up":
                    getVote.vote=True
                else:
                    getVote.vote=False
                getVote.put()
            else:
                vote=Vote(parent=ndb.Key(urlsafe=self.request.get('key')))
                vote.author=users.get_current_user()
                if self.request.get('vote') == "up":
                    vote.vote=True
                else:
                    vote.vote=False
                vote.voteType=self.request.get('type') 
                vote.put()
            prevURL = os.getenv('HTTP_REFERER')
            self.redirect(prevURL)

class AddFavorite(webapp2.RequestHandler):
    def post(self):
        if users.get_current_user() and self.request.get('key'):
            #add a favorite
            if self.request.get('action')=="add":
                favorite=Favorites()
                favorite.author=users.get_current_user()
                favorite.question=ndb.Key(urlsafe=self.request.get('key'))
                favorite.put()
                prevURL = os.getenv('HTTP_REFERER')
                self.redirect(prevURL)
            #remove a favorite
            elif self.request.get('action')=="remove":
                favorites=Favorites.query(Favorites.author==users.get_current_user(), Favorites.question==ndb.Key(urlsafe=self.request.get('key'))).fetch()
                for favorite in favorites:
                   favorite.key.delete()
                   prevURL = os.getenv('HTTP_REFERER')
                   self.redirect(prevURL)
    
class FavoritesView(webapp2.RequestHandler):
    def get(self):
        if users.get_current_user():
            favorites=Favorites.query(Favorites.author==users.get_current_user()).fetch()
            questions=[]
            for favorite in favorites:
                questions.append(favorite.question.get())
                #create a list to store questions, and total number of votes for them
            questionAndVotes= []
            for question in questions:
                totalUp=0
                totalDown=0
                votes = Vote.query(Vote.voteType=="question", ancestor=question.key).fetch()
                for vote in votes:
                    if vote.vote:
                        totalUp += 1
                    else:
                        totalDown += 1
                questionAndVotes.append((question, totalUp, totalDown))
            template_values = {
                'user': users.get_current_user(),
                'questionAndVotes': questionAndVotes,
                'favorites':favorites
            }
        
            path = os.path.join(os.path.dirname(__file__), 'FavoritesView.html')
            self.response.out.write(template.render(path, template_values))

class RSS(webapp2.RequestHandler):
    def get(self):
        if self.request.get('question'):
            questionKey=ndb.Key(urlsafe=self.request.get('question'))
            question=questionKey.get()
            answers = Answer.query(ancestor=questionKey).order(-Answer.date)
            template_values = {
                'question': question,
                'answers': answers
            }
            self.response.headers['Content-Type'] = 'application/rss+xml'
            path = os.path.join(os.path.dirname(__file__), 'RSS.xml')
            self.response.out.write(template.render(path, template_values))


class MainPage(webapp2.RequestHandler):
    def get(self):
        favoriteKeys=[]
        if users.get_current_user():
            loginUrl = users.create_logout_url(self.request.uri)
            loginUrl_linktext = 'Logout'
            #if a user is logged in, get their favorites
            favorites=Favorites.query(Favorites.author==users.get_current_user()).fetch()
            for favorite in favorites:
                favoriteKeys.append(favorite.question)
        else:
            loginUrl = users.create_login_url(self.request.uri)
            loginUrl_linktext = 'Login'
        upload_url = blobstore.create_upload_url('/upload')
        
        #implement paging
        offset=0
        entriesPerPage=10
        nextLink=False
        prevLink=False
        if self.request.get('offset') and self.request.get('offset') != '0':
            offset=int(self.request.get('offset'))
            prevLink=True
            
        #return tagged entries only
        if self.request.get('tag'):
            questionsRaw=Question.query(ancestor=forum_key()).order(-Question.modDate).fetch()
            questions =[]
            for question in questionsRaw:
                if self.request.get('tag') in question.tags:
                    questions.append(question)
        #default view 
        else:
            questions = Question.query(ancestor=forum_key()).order(-Question.modDate)
            questions=questions.fetch(entriesPerPage+1, offset=offset)
            
        if len(questions)==entriesPerPage+1:
            offset=offset+entriesPerPage
            nextLink=True
            
        #create a list to store questions, and total number of votes for them
        questionAndVotes= []
        for question in questions:
            totalUp=0
            totalDown=0
            votes = Vote.query(Vote.voteType=="question", ancestor=question.key).fetch()
            for vote in votes:
                if vote.vote:
                    totalUp += 1
                else:
                    totalDown += 1
            questionAndVotes.append((question, totalUp, totalDown))
        template_values = {
            'user' : users.get_current_user(),
            'questionAndVotes' : questionAndVotes,
            'offset': offset,
            'nextLink': nextLink,
            'prevLink' : prevLink,
            'loginUrl': loginUrl,
            'loginUrl_linktext': loginUrl_linktext,
            'upload_url': upload_url,
            'favoritesKeys': favoriteKeys
        }
        
        path = os.path.join(os.path.dirname(__file__), 'index.html')
        self.response.out.write(template.render(path, template_values))
        

application = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/QuestionDetail', QuestionDetail),
    ('/QuestionActivity', QuestionActivity),
    ('/upload', UploadHandler),
    ('/Edit', Edit),
    ('/ProcessVote', ProcessVote),
    ('/AddFavorite', AddFavorite),
    ('/FavoritesView', FavoritesView),
    ('/RSS', RSS),
    ('/Image', Image)
], debug=True)