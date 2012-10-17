#!/usr/bin/python
#encoding:utf-8
__author__ = 'lunch@spookies.in'


import gdata.spreadsheet.text_db
from gdata.alt.appengine import run_on_appengine
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.ext import db
from google.appengine.api import users
from datetime import datetime
import random
import logging

G_DOC_MIN_RECORD   = 1
G_DOC_MAX_RECORD   = 200000

TWITTER_MAX_LENGTH = 140

class BotDataModel(db.Model):
  mid = db.IntegerProperty()
  seq = db.IntegerProperty()
  status = db.StringProperty()

class MasterBotDataModel(db.Model):
  mid = db.IntegerProperty()
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
    data = db.GqlQuery('SELECT * FROM MasterBotDataModel WHERE mid = :1', int(self.request.get('mid'))).get()
    mid = data.mid
    name = data.name
    gUser = data.gUser
    gPass = data.gPass
    gDocFile = data.gDocFile.encode('utf_8')
    gDocTbl = data.gDocTbl.encode('utf_8')
    statusFormat = data.statusFormat
    statusColumns = data.statusColumns

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
        data.status = statusFormat % tuple([content[x] for x in statusColumns])
        data.put()

    self.response.out.write(u'%sに%dレコード入れました' % (name, seq))
    self.response.out.write(u'&nbsp;<a href="masterlist">戻る</a>')


class Datastore2TweetHandler(webapp.RequestHandler):

  def get(self):
    base = datetime.now()
    minute = base.hour * 60 + base.minute
    for masterData in db.GqlQuery('SELECT * FROM MasterBotDataModel WHERE enabled = True'):
      if masterData.cron != '':
        if (minute % int(masterData.cron) == 0):
#        if True:
          if masterData.type == 'seq':
            self._seqTweet(masterData)
          elif masterData.type == 'rnd':
            self._rndTweet(masterData)


  def _seqTweet(self, masterData):
    seqData = db.GqlQuery("SELECT * FROM SeqDataModel WHERE mid = :1", masterData.mid).get()
    if seqData == None:
      seqData = SeqDataModel()
      seqData.mid = masterData.mid
      seqData.cnt = 1

    botData = db.GqlQuery("SELECT * FROM BotDataModel WHERE mid = :1 AND seq = :2", masterData.mid, seqData.cnt).get()
    if botData == None:
      seqData.cnt = 1
      botData = db.GqlQuery("SELECT * FROM BotDataModel WHERE mid = :1 AND seq = :2", masterData.mid, seqData.cnt).get()

    seqData.cnt = seqData.cnt + 1
    seqData.put()

    self._doTweet(masterData, botData)

  def _rndTweet(self, masterData):
    q = db.GqlQuery("SELECT * FROM BotDataModel WHERE mid = :1", masterData.mid)
    botData = q.fetch(1, random.randint(1, q.count()) - 1)[0]

    self._doTweet(masterData, botData)

  def _doTweet(self, masterData, botData):
    import oauth
    client = oauth.TwitterClient(masterData.cKey,
                                 masterData.cSecret, None)
    run_on_appengine(client, store_tokens=False, single_user_mode=True)
    param = {'status': botData.status}
    client.make_request('https://api.twitter.com/1.1/statuses/update.json',
                        token=masterData.aToken,
                        secret=masterData.aTokenSecret,
                        additional_params=param,
                        protected=True,
                        method='POST')
    logging.info(botData.status)

class AdminMasterListRequestHandler(webapp.RequestHandler):
  def get(self):
    self.response.out.write('<html><body><table>')

    for data in MasterBotDataModel.all():
      self.response.out.write('  <tr><td>')
      self.response.out.write(data.name.encode('utf_8'))
      self.response.out.write('  </td><td>')
      self.response.out.write('    <a href="masterinput?mid=' + str(data.mid) + '">マスター更新</a>')
      self.response.out.write('  </td><td>')
      self.response.out.write('    <a href="sheet2datastore?mid=' + str(data.mid) + '">データインポート</a>')
      self.response.out.write('  </td></tr>')

    self.response.out.write("""
  <tr><td colspan="3">
    <a href="masterinput">新規登録</a>
  </td></tr>

</table></body></html>""")

class AdminMasterInputRequestHandler(webapp.RequestHandler):
  def get(self):
    self.response.out.write('<html><body><form action="mastersubmit" method="post"><table>')

    html = """
  <tr><td colspan="2">基本情報</td></tr>
  <tr><td>ID</td><td><input type="text" name="mid" value="%d"/></td></tr>
  <tr><td>bot名</td><td><input type="text" name="name" value="%s"/></td></tr>
  <tr><td>botタイプ</td><td><select name="type">
    <option value="rnd" %s>ランダム</option>
    <option value="seq" %s>順番</option>
  </select></td></tr>
  <tr><td>起動間隔(分)</td><td><input type="text" name="cron" value="%s"/></td></tr>
  <tr><td colspan="2">Twitter認証</td></tr>
  <tr><td>TWITTER_CONSUMER_KEY</td><td><input type="text" name="cKey" value="%s"/></td></tr>
  <tr><td>TWITTER_CONSUMER_SECRET</td><td><input type="text" name="cSecret" value="%s"/></td></tr>
  <tr><td>TWITTER_ACCESS_TOKEN</td><td><input type="text" name="aToken" value="%s"/></td></tr>
  <tr><td>TWITTER_ACCESS_TOKEN_SECRET</td><td><input type="text" name="aTokenSecret" value="%s"/></td></tr>
  <tr><td colspan="2">GoogleDocs認証</td></tr>
  <tr><td>GoogleMailAddress</td><td><input type="text" name="gUser" value="%s"/></td></tr>
  <tr><td>GooglePassword</td><td><input type="text" name="gPass" value=""/></td></tr>
  <tr><td>GoogleDocファイル名</td><td><input type="text" name="gDocFile" value="%s"/></td></tr>
  <tr><td>GoogleDocシート名</td><td><input type="text" name="gDocTbl" value="%s"/></td></tr>
  <tr><td colspan="2">その他</td></tr>
  <tr><td>ステータスのフォーマット</td><td><input type="text" name="statusFormat" value="%s"/></td></tr>
  <tr><td>ステータスの置換カラム(,)</td><td><input type="text" name="statusColumns" value="%s"/></td></tr>
  <tr><td>有効</td><td><input type="checkbox" name="enabled" %s /></td></tr>
"""
    if self.request.get('mid') != '':
      data = db.GqlQuery('SELECT * FROM MasterBotDataModel WHERE mid = :1', int(self.request.get('mid'))).get()

      mid = data.mid
      name = data.name.encode('utf_8')
      if data.type == u'rnd':
        rnd = 'selected="selected"'
        seq = ''
      else:
        rnd = ''
        seq = 'selected="selected"'

      cron = data.cron.encode('utf_8')
      cKey = data.cKey.encode('utf_8')
      cSecret = data.cSecret.encode('utf_8')
      aToken = data.aToken.encode('utf_8')
      aTokenSecret = data.aTokenSecret.encode('utf_8')
      gUser = data.gUser.encode('utf_8')
      gDocFile = data.gDocFile.encode('utf_8')
      gDocTbl = data.gDocTbl.encode('utf_8')
      statusFormat = data.statusFormat.encode('utf_8')
      statusColumns = ",".join(data.statusColumns).encode('utf_8')
      enabled = 'checked="checked"' if data.enabled else ''

      self.response.out.write(html % (mid, name, rnd, seq, cron, cKey, cSecret,aToken, aTokenSecret,
                                      gUser, gDocFile, gDocTbl,
                                      statusFormat, statusColumns, enabled))

    else:
      self.response.out.write(html % (MasterBotDataModel.all().count() + 1, '', '',  '', '', '', '', '', '', '', '', '', '', '', 'checked="checked"'))

    self.response.out.write("""
  <tr><td colspan="2">
    <input type="submit" value="登録" />
  </td></tr>

</table></form></body></html>""")

class AdminMasterSubmitRequestHandler(webapp.RequestHandler):
  def post(self):
    data = db.GqlQuery('SELECT * FROM MasterBotDataModel WHERE mid = :1', int(self.request.get('mid'))).get()
    if data == None:
      data = MasterBotDataModel()

    data.mid = int(self.request.get('mid'))
    data.name = self.request.get('name')
    data.type = self.request.get('type')
    data.cron = self.request.get('cron')
    data.cKey = self.request.get('cKey')
    data.cSecret = self.request.get('cSecret')
    data.aToken = self.request.get('aToken')
    data.aTokenSecret = self.request.get('aTokenSecret')
    data.gUser = self.request.get('gUser')
    data.gPass = self.request.get('gPass') if self.request.get('gPass') != '' else data.gPass
    data.gDocFile = self.request.get('gDocFile')
    data.gDocTbl = self.request.get('gDocTbl')
    data.statusFormat = self.request.get('statusFormat')
    data.statusColumns = self.request.get('statusColumns').split(',')
    data.enabled = True if self.request.get('enabled') == 'on' else False
    data.put()

    self.redirect('/admin/masterlist')

class RootRequestHandler(webapp.RequestHandler):

  def get(self):
    if users.is_current_user_admin():
      self.redirect('/admin/masterlist')
    else:
      self.response.out.write('Hack you!!!')

def main():
  application = webapp.WSGIApplication([
  ('/', RootRequestHandler),
  ('/admin/masterlist', AdminMasterListRequestHandler),
  ('/admin/masterinput', AdminMasterInputRequestHandler),
  ('/admin/mastersubmit', AdminMasterSubmitRequestHandler),
  ('/admin/sheet2datastore', Sheet2DatastoreHandler),
  ('/datastore2tweet', Datastore2TweetHandler),
  ], debug=False)
  util.run_wsgi_app(application)

if __name__ == '__main__':
  main()
