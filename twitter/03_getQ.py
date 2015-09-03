# -*- coding: utf-8 -*-
#!/usr/bin/python
import MySQLdb
import pywikibot
import sys
import re
import mwparserfromhell
from pywikibot import pagegenerators

config = ConfigParser.ConfigParser()
config.read("../mysql.conf")

db = MySQLdb.connect(host=config.get("mysql", "host"), # your host, usually localhost
                     user=config.get("mysql", "user"), # your username
                      passwd=config.get("mysql", "password"), # your password
                      db=config.get("mysql", "database"),
                      charset='utf8') # name of the data base

site = pywikibot.Site("en", "wikipedia")

def dataLoad(wikiId):
	page=pywikibot.Page(site, wikiId)
	try:
		data = pywikibot.ItemPage.fromPage(page)
		return data
	except:
		print "Impossible de charger #%s# " % (wikiId)
		return False

cur = db.cursor() 
cur.execute("SELECT id, title, ta FROM twitter where Q='' and status=1")

for row in cur.fetchall() :
	idPage, title, twitterAccountProposed = (row[0], row[1], row[2])
	item = dataLoad(title.decode("utf-8"))
	if item == False:
		print "Pas de Q"
	else:
		print "~~ %s [%s] ~~" % (title, item.getID().encode("utf-8"))
		
		if "P2002" in item.claims:
			if len(item.claims["P2002"]) == 1:
				twitterAccountExist = item.claims["P2002"][0].getTarget()
			else:
				print "PLUSIEURS 2002"

			if twitterAccountExist == twitterAccountProposed:


				sql = "UPDATE twitter set `Q` = '%s', `ta_current`='%s' where id=%s" % (db.escape(item.getID()), db.escape(twitterAccountExist), idPage)
				db.cursor().execute(sql)
				db.commit()
				print "Nothing new"
			else:
				print twitterAccountExist, " => ", twitterAccountProposed

		elif "P553" in item.claims:
			sql = "UPDATE twitter set `Q` = '%s', `ta_current`='P553' where id=%s" % (db.escape(item.getID()), idPage)
			db.cursor().execute(sql)
			db.commit()	
		sql = "UPDATE twitter set `Q` = '%s' where id=%s" % (db.escape(item.getID()), idPage)
		db.cursor().execute(sql)
		db.commit()
