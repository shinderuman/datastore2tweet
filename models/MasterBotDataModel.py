#!/usr/bin/python
#encoding:utf-8
__author__ = 'lunch@spookies.in'

from google.appengine.ext import db

class MasterBotDataModel(db.Model):
  id = db.IntegerProperty()
  name = db.StringProperty()
  type = db.StringProperty()
  cron = db.StringProperty()
  cKey = db.StringProperty()
  cSecret = db.StringProperty()
  aToken = db.StringProperty()
  aTokenSecret = db.StringProperty()
