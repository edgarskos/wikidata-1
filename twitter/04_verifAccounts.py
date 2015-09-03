# -*- coding: utf-8 -*-
#!/usr/bin/python
import MySQLdb
import pywikibot
import sys
import re
import twitter

from pywikibot import pagegenerators

config = ConfigParser.ConfigParser()
config.read("../mysql.conf")

config_api = ConfigParser.ConfigParser()
config_api.read("../api_keys.conf")


db = MySQLdb.connect(host=config.get("mysql", "host"), # your host, usually localhost
                     user=config.get("mysql", "user"), # your username
                      passwd=config.get("mysql", "password"), # your password
                      db=config.get("mysql", "database"),
                      charset='utf8') # name of the data base


api = twitter.Api(consumer_key=config.get("twitter", "consumer_key"),
                      consumer_secret=config.get("twitter", "consumer_secret"),
                      access_token_key=config.get("twitter", "access_token_key"),
                      access_token_secret=config.get("twitter", "access_token_secret"))

cur = db.cursor() 
cur.execute("SELECT id, ta FROM twitter where Q!='' and ta_current='' and exist=-1 and status != 0 and ta != '@' and ta != '' limit 0,90")

pageIdList = {}
userList = []
for row in cur.fetchall() :
	idPage, twitterAccountProposed = (row[0], row[1].strip())
	userList.append(twitterAccountProposed)
	pageIdList[twitterAccountProposed.upper()] = str(idPage)


res =api.UsersLookup(None, userList)
for user in res:
	id = pageIdList[user.screen_name.upper()]
	if user.verified == True:
		sql = "UPDATE twitter set `ta_cass`= '%s', `exist` = '2' where id=%s" % (db.escape(user.screen_name), id)
	else:
		sql = "UPDATE twitter set `ta_cass`= '%s', `exist` = '1' where id=%s" % (db.escape(user.screen_name), id)

	db.cursor().execute(sql)
	db.commit()
	del(pageIdList[user.screen_name.upper()])


print "** After cleaning **"
for screenName in pageIdList:
	print "Remove %s [%s]" % (screenName, pageIdList[screenName])
	sql = "UPDATE twitter set `exist` = '0' where id=%s" % (pageIdList[screenName])	
	db.cursor().execute(sql)
	db.commit()