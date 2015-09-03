# -*- coding: utf-8 -*-
#!/usr/bin/python
import MySQLdb
import pywikibot
import sys
import re
import mwparserfromhell
from pywikibot import pagegenerators
'''
Ce script va récupérer toutes les pages qui utilisent le template "Infobox Rugbyman"
'''
exit()

config = ConfigParser.ConfigParser()
config.read("../mysql.conf")

db = MySQLdb.connect(host=config.get("mysql", "host"), # your host, usually localhost
                     user=config.get("mysql", "user"), # your username
                      passwd=config.get("mysql", "password"), # your password
                      db=config.get("mysql", "database"),
                      charset='utf8') # name of the data base

site = pywikibot.Site("en", "wikipedia")

def parse(title):
	page = pywikibot.Page(site, title)
	text = page.get()
	return mwparserfromhell.parse(text)

cur = db.cursor() 

liste = pagegenerators.ReferringPageGenerator(pywikibot.Page(site, u"Template:Twitter"), onlyTemplateInclusion=True)
for page in liste:
	#print str(page.title().encode("utf-8"))
	sql = "INSERT INTO twitter (`title`, `lng`) values (%s, 'en')" % (db.escape(page.title().encode("utf-8")))
	db.cursor().execute(sql)
	db.commit()
