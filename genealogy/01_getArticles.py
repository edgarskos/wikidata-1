# -*- coding: utf-8 -*-
#!/usr/bin/python
import MySQLdb
import pywikibot
import ConfigParser
import mwparserfromhell
import pywikibot as wikipedia
from pywikibot import pagegenerators
import re

import time
start = time.time()

config = ConfigParser.ConfigParser()
config.read("../../wikidata/mysql.conf")

db = MySQLdb.connect(host=config.get("mysql", "host"), # your host, usually localhost
                     user=config.get("mysql", "user"), # your username
                      passwd=config.get("mysql", "password"), # your password
                      db=config.get("mysql", "database"),
                      charset='utf8') # name of the data base

def list_template_usage(site, article_tpl_name):
	"""Return a generator of main space pages transcluding a given template."""
	rowTemplate = wikipedia.Page(site, u'%s:%s' % (site.namespace(10), article_tpl_name))
	transGen = pagegenerators.ReferringPageGenerator(rowTemplate, onlyTemplateInclusion=True)
	filteredGen = pagegenerators.NamespaceFilterPageGenerator(transGen, [0])
	# generator = pagegenerators.PreloadingGenerator(filteredGen)
	generator =site.preloadpages(filteredGen, pageprops=True)
	return generator



site = wikipedia.Site("en", 'wikipedia')

nb = 0
for page in list_template_usage(site, "Infobox person"):
	Q = ""
	try:
		item = pywikibot.ItemPage.fromPage(page)
		Q = item.getID()
	except pywikibot.NoPage:
		print "No ITEM"
		Q = ""

	parsedExtText = mwparserfromhell.parse(page.text, skip_style_tags=True)

	templates = parsedExtText.filter_templates()
	tplText = ""
	for tpl in templates:
		if tpl.name.upper().startswith("INFOBOX"):
			tplText = tpl

	nb += 1
	db.cursor().execute("INSERT INTO genealogy (`article`, `q`, `tpl`) values (%s, %s, %s)", (page.title().encode("utf-8"), Q, tplText.encode("utf-8")))
	db.commit()