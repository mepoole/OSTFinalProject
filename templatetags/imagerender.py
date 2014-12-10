from google.appengine.ext.webapp import template
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe
from django.template.defaultfilters import escape
import re

# ...
register = template.create_template_register()

@register.filter(name='imagerender')
def imagerender(text, autoescape=None):
    
    words=text.split()
    for i, word in enumerate(words):
        #checking for image links
        if re.match("(^https?://[^\s]+[(\.jpg), (\.gif), (\.png)]$)", word):
            words[i] = "<img src='"+word+ "'>"
            words[i]=mark_safe(words[i])
        #check if it's an image from the blob store
        elif re.match("(^http://localhost:9080/_ah/img/)", word):
            words[i] = "<img src='"+word+ "'>"
            words[i]=mark_safe(words[i])
        #checking for regular links
        elif re.match("(^https?://[^\s]+)", word):
            words[i] = "<a href='"+word+ "'>"+word+"</a>"
            words[i]=mark_safe(words[i])
        else:
            words[i]=escape(words[i])
        
    return ' '.join(words)