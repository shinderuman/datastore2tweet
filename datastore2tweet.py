#!/usr/bin/python
#encoding:utf-8
__author__ = 'lunch@spookies.in'


import gdata.spreadsheet.text_db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.ext import db

G_DOC_MIN_RECORD   = 1
G_DOC_MAX_RECORD   = 200000

TWITTER_MAX_LENGTH = 140

class BotDataModel(db.Model):
  mid = db.IntegerProperty()
  seq = db.IntegerProperty()
  status = db.StringProperty()

class MasterBotDataModel(db.Model):
  id = db.IntegerProperty()
  name = db.StringProperty()
  type = db.StringProperty()
  cron = db.StringProperty()
  cKey = db.StringProperty()
  cSecret = db.StringProperty()
  aToken = db.StringProperty()
  aTokenSecret = db.StringProperty()
  gUser = db.StringProperty()
  gPass = db.StringProperty()
  gDocFile = db.StringProperty()
  gDocTbl = db.StringProperty()
  statusFormat = db.StringProperty()
  statusColumns = db.StringListProperty()
  enabled = db.BooleanProperty()

class SeqDataModel(db.Model):
  mid = db.IntegerProperty()
  cnt = db.IntegerProperty()

class Sheet2DatastoreHandler(webapp.RequestHandler):

  def get(self):
    # TODO get from MasterBotDataModel
    mid = 1
    name = 'ドロヘドロbot'
    gUser = ''
    gPass = ''
    gDocFile = 'ドロヘドロ'
    gDocTbl = 'Sheet1'
    statusFormat = '「%s」魔の%s'
    statusColumns = ['comments', 'chapter']

    q = db.GqlQuery("SELECT * FROM BotDataModel WHERE mid = :1", mid)
    for result in q:
      result.delete()

    client = gdata.spreadsheet.text_db.DatabaseClient(gUser, gPass)
    textDb = client.GetDatabases(name=gDocFile)[0]
    table = textDb.GetTables(name=gDocTbl)[0]
    seq = 0
    for record in table.GetRecords(G_DOC_MIN_RECORD, G_DOC_MAX_RECORD):
      content = record.content

      length = 10 + 10
      for column in statusColumns:
        length = length + len(content[column])

      if length <= TWITTER_MAX_LENGTH:
        seq = seq + 1
        data  = BotDataModel()
        data.mid = mid
        data.seq = seq
        data.status = unicode(statusFormat, 'utf8') % tuple([content[x] for x in statusColumns])
        data.put()

    self.response.out.write(u'%sに%dレコード入れました' % (unicode(name, 'utf8'), seq))

class Datastore2TweetHandler(webapp.RequestHandler):
  
  def get(self):
    data = BotDataModel.all().get()
    self.response.out.write(unicode(data.status))
      
class RootRequestHandler(webapp.RequestHandler):

  def get(self):
    self.response.out.write('Hack you!!!')
          
def main():
  application = webapp.WSGIApplication([
  ('/', RootRequestHandler),
  ('/datastore2tweet', Datastore2TweetHandler),
  ('/sheet2datastore', Sheet2DatastoreHandler),
  ], debug=False)
  util.run_wsgi_app(application)

if __name__ == '__main__':
  main()
