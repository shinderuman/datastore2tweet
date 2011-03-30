#!/usr/bin/python
#encoding:utf-8
__author__ = 'lunch@spookies.in'


import models.BotDataModel
import gdata.spreadsheet.text_db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.ext import db

G_USERNAME = ''
G_PASSWORD = ''

G_DOC_FILE_NAME    = 'ドロヘドロ'
G_DOC_TABLE_NAME   = 'Sheet1'

MID = 1
URL = '/sheet2datastore/dorohedoro'

G_DOC_MIN_RECORD   = 1
G_DOC_MAX_RECORD   = 200000

TWITTER_MAX_LENGTH = 140

class DorohedoroSheet2DatastoreHandler(webapp.RequestHandler):

  def get(self):
    q = db.GqlQuery("SELECT * FROM BotDataModel WHERE mid = :1", MID)
    for result in q:
      result.delete()

    client = gdata.spreadsheet.text_db.DatabaseClient(G_USERNAME, G_PASSWORD)
    textDb = client.GetDatabases(name=G_DOC_FILE_NAME)[0]
    table = textDb.GetTables(name=G_DOC_TABLE_NAME)[0]
    seq = 0
    for record in table.GetRecords(G_DOC_MIN_RECORD, G_DOC_MAX_RECORD):
      content = record.content
      length = len(content['comments']) + 10 + 10
      if length <= TWITTER_MAX_LENGTH:
        seq = seq + 1
        data  = models.BotDataModel.BotDataModel()
        data.mid = MID
        data.seq = seq
        data.status = u'「%s」魔の%s' % tuple([content[x] for x in ['comments','chapter']])
        data.put()

    self.response.out.write('hoge')
    
def main():
  application = webapp.WSGIApplication([
  (URL, DorohedoroSheet2DatastoreHandler),
  ], debug=False)
  util.run_wsgi_app(application)

if __name__ == '__main__':
  main()
