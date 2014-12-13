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


site = pywikibot.Site("fr", "wikipedia")

def parse(title):
	page = pywikibot.Page(site, title)
	text = page.get()
	return mwparserfromhell.parse(text)

liste = pagegenerators.ReferringPageGenerator(pywikibot.Page(site, u"Modèle:Infobox Rugbyman"), onlyTemplateInclusion=True)
for page in liste:
	print str(page.title().encode("utf-8"))
sys.exit()
parsedText = parse("Mathieu Bourret")
templates = parsedText.filter_templates()

for tpl in templates:
	if tpl.name.upper().strip() == "INFOBOX RUGBYMAN":
		print ">>%s<<" % tpl.name.strip().encode("utf-8")
		saisons = re.split("<br ?\/>", str(tpl.get("saison").value))
		clubs = re.split("<br ?\/>", str(tpl.get("club").value))
		print clubs
		print "%s - %s" % (len(clubs), len(saisons))



# pywikibot.extract_templates_and_params