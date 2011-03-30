#!/usr/bin/python
#encoding:utf-8
__author__ = 'lunch@spookies.in'

from google.appengine.ext import db

class SeqDataModel(db.Model):
  mid = db.IntegerProperty()
  cnt = db.IntegerProperty()
