# -*- coding: utf-8 -*-
#!/usr/bin/python
import re, sys, urllib2
from xml.dom import minidom
from lxml import etree
import pywikibot as wikipedia
from pywikibot import config

site = wikipedia.Site("en", 'wikipedia')
repo = site.data_repository()

lines = [line.rstrip('\n') for line in open('liste_uniq.txt')]

for l in lines:
	tab = re.match(r"\* \[\[(Q.*)\]\]: (.*)$", l)
	if tab:
		Q = tab.group(1)
		lineId = {}
		idref = tab.group(2)
		for link in re.split(",", idref):
			href_idref = re.sub(r"\[([^ ]*) .*$", r"\1", link.strip())			
			id_idref = re.sub("http://www.idref.fr/", "", href_idref)
			lineId[id_idref] = {}


		# A partir d'ici on a tous les ID attachés à la notice
		nb_ok = 0
		print Q
		for id_idref in lineId:
			lineId[id_idref]['status'] = None
			lineId[id_idref]['type'] = None
			lineId[id_idref]['redirect'] = None
			lineId[id_idref]['exists'] = None

			try:
				tree = etree.parse("http://www.idref.fr/%s.xml" % id_idref)
				leader = tree.xpath("//record/leader")[0].text

				status = leader[5:6]
				authorityType = leader[9:10]


				lineId[id_idref]['status'] = status
				lineId[id_idref]['type'] = authorityType

				if status == "d":
					lineId[id_idref]['exists'] = False
					# We need to check if it has been replaced
					try:
						result = urllib2.urlopen("http://www.idref.fr/%s.html" % id_idref)
						txt = result.read(4096)
						if "Notice remplac" in txt:
							new_id = re.sub(r"^.*<a href=\"http\:\/\/www.idref.fr\/(.*)\">.*$", r"\1", txt, flags=re.MULTILINE|re.DOTALL)
							new_id = new_id.strip()

							if re.match(r"^[\dX]*$", new_id):
								lineId[id_idref]['redirect'] = new_id
							else:
								print "Erreur format newid : #%s#" % new_id
								sys.exit()
						else:
							print href_idref + " ok"
					except urllib2.HTTPError, e:
						if e.code == 500:
							# Just deleted on idref
							pass
						else:
							print "#" + str(e.code) + "#"
							print e.msg
							exit()
				elif status == "c" or status == "n":
					lineId[id_idref]['exists'] = True
				else:
					print "Statut non traité : %s" % status
				nb_ok += 1
			except:
				print "Impossible to load %s" % id_idref
		# A partir d'ici on doit regarder combien il y a de notices qui sont en c ou n
		nb_ok = sum(1 for x in lineId if lineId[x]["exists"] == True)
		itemPage = None
		for x in lineId:
			if lineId[x]["exists"] == False:
				print "We need to delete %s" % x
				if itemPage == None:
					itemPage = wikipedia.ItemPage(repo, Q)
				itemPage.get()
				for cl in itemPage.claims["P269"]:
					if cl.getTarget() == x:
						itemPage.removeClaims([cl])
			print "%s => %s, %s" % (x, lineId[x]["status"], lineId[x]["type"])