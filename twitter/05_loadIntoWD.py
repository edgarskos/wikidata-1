# -*- coding: utf-8 -*-
#!/usr/bin/python
import MySQLdb
import pywikibot
import sys
import re
import twitter

from pywikibot import pagegenerators

site = pywikibot.Site("en", "wikipedia")
repo = site.data_repository()  # this is a DataSite object

config = ConfigParser.ConfigParser()
config.read("../mysql.conf")

db = MySQLdb.connect(host=config.get("mysql", "host"), # your host, usually localhost
                     user=config.get("mysql", "user"), # your username
                      passwd=config.get("mysql", "password"), # your password
                      db=config.get("mysql", "database"),
                      charset='utf8') # name of the data base

importedEnWikipedia = pywikibot.Claim(repo, u'P143')
enWikipedia = pywikibot.ItemPage(repo, "Q328")
importedEnWikipedia.setTarget(enWikipedia)

cur_update = db.cursor()
cur = db.cursor() 

cur.execute("SELECT id, Q, ta_cass as twitterAccount, exist as accountStatus FROM `twitter` where exist in (1, 2) and ta_current = '' and `update`=0 order by id limit 0,10")

for row in cur.fetchall() :
	ID, Q, account = (row[0], row[1], row[2].strip())
	item = pywikibot.ItemPage(repo, Q)
	item.get()  # you need to call it to access any data.

	if "P2002" in item.claims:
		print "P2002 has been loaded for %s" % Q
		exit()

	claim = pywikibot.Claim(repo, str("P2002"))
	claim.setTarget(account)
	item.addClaim(claim)
	claim.addSources([importedEnWikipedia])

	cur_update.execute("UPDATE twitter set `update`=1 where id=%s" % (ID))
	db.commit()
	print "%s maj" % Q
