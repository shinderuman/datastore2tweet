#!/usr/bin/python
#encoding:utf-8
__author__ = 'lunch@spookies.in'

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db

class MasterBotDataModel(db.Model):
  pk = db.IntegerProperty()
  name = db.StringProperty()
  botType = db.StringProperty()
  cKey = db.StringProperty()
  cSecret = db.StringProperty()
  aToken = db.StringProperty()
  aTokenSecret = db.StringProperty()

class Test(webapp.RequestHandler):
  def __init__(self):
    self

  def get(self):
    data = MasterBotDataModel()
    data.pk   = 1
    data.name = u"ドロヘドロbot"
    data.botType = "rnd"
    data.cKey = "1"
    data.cSecret = "2"
    data.aToken  = "3"
    data.aTokenSecret = "4"
    data.put()
    self.response.out.write('hoge')
  
def main():
  application = webapp.WSGIApplication([
  ('/', Test),
  ], debug=False)
  run_wsgi_app(application)

if __name__ == '__main__':
  main()
