#!/usr/bin/python
#encoding:utf-8
__author__ = 'lunch@spookies.in'

from google.appengine.ext import db

class BotDataModel(db.Model):
  mid = db.IntegerProperty()
  seq = db.IntegerProperty()
  status = db.StringProperty()
