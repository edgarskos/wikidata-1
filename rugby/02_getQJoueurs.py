# -*- coding: utf-8 -*-
#!/usr/bin/python
import MySQLdb, ConfigParser
import pywikibot
import sys
import re
import mwparserfromhell
from pywikibot import pagegenerators
'''
Ce script va récupérer toutes les pages qui utilisent le template "Infobox Rugbyman"
'''

site = pywikibot.Site("fr", "wikipedia")
config = ConfigParser.ConfigParser()
config.read("../mysql.conf")

def getQ(acteur):
	try:
		page=pywikibot.Page(site, acteur)
		if page.isRedirectPage():
			return getQ(page.getRedirectTarget().title())		
		else:
			data = pywikibot.ItemPage.fromPage(page)
			return data.getID()
	except pywikibot.NoPage:
		return 0
	except:
		print "Unexpected error:", sys.exc_info()[0]
		sys.exit()
    	raise

db = MySQLdb.connect(host=config.get("mysql", "host"), # your host, usually localhost
                     user=config.get("mysql", "user"), # your username
                      passwd=config.get("mysql", "password"), # your password
                      db=config.get("mysql", "database"),
                      charset='utf8') # name of the data base


cur = db.cursor() 
cur.execute("SELECT id, joueur FROM rugby where Q='0'")
for row in cur.fetchall() :
	ID, joueur = (row[0], row[1])
	Q = getQ(joueur)
	print "%s => %s" % (joueur, Q)
	db.cursor().execute("UPDATE rugby set Q = '%s' where id = %s" % (Q, ID))
	db.commit()
    


sys.exit()

def parse(title):
	page = pywikibot.Page(site, title.decode("utf-8"))
	text = page.get()
	return mwparserfromhell.parse(text)


f = open("joueurs.txt")
for line in f:
	joueur = line.strip()
	print "Chargement de %s" % joueur
	parsedText = parse(joueur)
	templates = parsedText.filter_templates()
	for tpl in templates:
		if tpl.name.upper().strip() == "INFOBOX RUGBYMAN":
			print ">>%s<<" % tpl.name.strip().encode("utf-8")

			saisons = re.split("<br ?\/>", str(tpl.get("saison").value).encode("utf-8"))
			clubs = re.split("<br ?\/>", str(tpl.get("club").value.encode("utf-8")))
			print "%s - %s" % (len(clubs), len(saisons))
sys.exit()




# pywikibot.extract_templates_and_params