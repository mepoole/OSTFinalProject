from google.appengine.ext.webapp import template
# ...
register = template.create_template_register()
@register.filter(name='imagerender')
def imagerender(value):
    return value