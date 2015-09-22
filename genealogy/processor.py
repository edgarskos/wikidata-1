# -*- coding: utf-8 -*-
#!/usr/bin/python
import MySQLdb
import pywikibot
import ConfigParser
import mwparserfromhell
import pywikibot as wikipedia
from pywikibot import pagegenerators

from pywikibot import config
import re

pywikibot.config.put_throttle = 1


config.usernames['wikidata']['wikidata'] = 'Symac bot'

config = ConfigParser.ConfigParser()
config.read("../../wikidata/mysql.conf")

db = MySQLdb.connect(host=config.get("mysql", "host"), # your host, usually localhost
                     user=config.get("mysql", "user"), # your username
                      passwd=config.get("mysql", "password"), # your password
                      db=config.get("mysql", "database"),
                      charset='utf8') # name of the data base

site = wikipedia.Site("en", 'wikipedia')
repo = site.data_repository()


importedEnWikipedia = pywikibot.Claim(repo, u'P143')
enWikipedia = pywikibot.ItemPage(repo, "Q328")
importedEnWikipedia.setTarget(enWikipedia)

equivCodes = {
	"spouse": "P26",
	"partner" : "P451",
	"children" : "P40",
	"parents" : "P22|P25",
	"relatives": "P7|P9" # Brother (P7) / Sister (P9)
}

def isHuman(item):
	for tmp in item.claims["P31"]:
		if tmp.getTarget().getID() == "Q5":
			return True
	return False

def getGender(item):
	print "DEAL WITH GENDER"
	exit()
	print item.claims["P21"]

def getPeriod(dates):
	dates = dates.replace("–", "-")
	dates = dates.replace("&ndash;", "-")
	if "-" in dates:
		debut, fin = dates.split("-")
		if (len(debut) == 4) and (len(fin) == 2):
			fin = debut[0:2] + fin

		if fin.upper() == "PRESENT":
			fin = None

		if not re.match(r"^\d{4}$", debut):
			print "Issue with begin date %s" % debut
			debut = None

		if fin:
			fin = re.sub(r"^(\d{4}).*$", r"\1", fin)
			if not re.match(r"^\d{4}$", fin):
				print "Issue with end date %s" % fin
				fin = None
		return (debut, fin)
	else:
		#print "No date : ", dates
		return None

def getVals(code, tpl):
	output = {}
	if tpl.has(code):
		value = tpl.get(code).value.encode("utf-8").strip()
		if value == "":
			return output
		if "{{ublist" in value or "{{UNBULLETED LIST" in value.upper() or "{{bulleted list" in value:
			lines = []
			ublist = mwparserfromhell.parse(value)
			tpl = ublist.filter_templates(recursive=False)
			tpl = tpl[0]
			print tpl.encode("utf-8")
			for i in range(0,10):
				if tpl.has(i):
					if str(tpl.get(i).encode("utf-8")).strip() != "":
						# lines.append(str(tpl.get(i).encode("utf-8").strip()))
						lines.append(str(tpl.get(i).encode("utf-8").strip()))
		elif "{{PLAINLIST" in value.upper() or "{{PLAIN LIST" in value.upper():
			lines = []
			ublist = mwparserfromhell.parse(value)
			tpl = ublist.filter_templates(recursive=False)
			tpl = tpl[0]
			lines = str(tpl.get(1).encode("utf-8")).split("\n")
		# Sometimes we only have a list separated by a ,
		elif "]]," in value:
			lines = reduce(lambda acc, elem: acc[:-1] + [acc[-1] + elem] if elem == "]]," else acc + [elem], re.split("(]],)", value), [])
		else:
			lines = re.split("<br ?\/? ?>", value)

		# We reduce the table in case we have split lines with dates on the second line
		tmpLines = lines
		lines = reduce(lambda acc, elem: acc[:-1] + [acc[-1] + " " + elem ] if re.match(r"^\((m\.)? ?\d", elem) else acc + [elem], lines, [])
		if lines != tmpLines:
			print "Reduction de lines !"
			print lines
			print tmpLines
			exit()
		noPage = False

		tabLines = [x for x in lines if str(x) != '']
		for line in tabLines:

			cleanLine = line.strip()
			cleanLine = re.sub(r"^ ?\* ?", "", cleanLine) # When we have a list
			cleanLine = re.sub(r"<ref[^>]*>.*<\/ref>", "", cleanLine) # Remove the references

			if "{{MARRIAGE" in cleanLine.upper():
				parsedText = mwparserfromhell.parse(cleanLine)
				tpl = parsedText.filter_templates(recursive=False)
				cleanLine = ""
				for subTpl in tpl:
					if subTpl.name.upper() == "MARRIAGE":
						if "[[" in str(subTpl.get("1")):
							person = re.sub(r"^\[\[(.*)\]\]", r"\1", str(subTpl.get("1")))
						else:
							person = None
						if subTpl.has("2"):
							P580 = str(subTpl.get("2").value)
						if subTpl.has("3"):
							P582 = str(subTpl.get("3").value)
					if person != None:
						person = re.sub(r"<br ?\/? ?>$", "", person) # Remove the <br> useless (cf. [[Charlie_Chaplin]] spouses)
			else:
				person = None
				P580 = None
				P582 = None
				if code == "relatives":
					if ("brother" in cleanLine or "sister" in cleanLine) and "half-" not in cleanLine:
						pass
					else:
						# Relative which is not a brother or sister ? Not handled
						noPage = True
						cleanLine = ""


				cleanLine = re.sub(r"^{{nowrap\|(.*)", r"\1", cleanLine)
				cleanLine = re.sub(r"}}$", "", cleanLine)
				cleanLine = re.sub(r"^(Father|Mother) ?:? ?", "", cleanLine)		
				if cleanLine.startswith("["): # We have a link, that might be interesting
					person = re.sub(r".*?\[\[([^\|\]]*).*", r"\1", cleanLine.strip().decode("utf-8"))
					if code in ["spouse", "partner"]:
						# For spouse and partners it might be interesting to get the begin and end date
						dates = re.sub(r'<[^>]+>', "", cleanLine).strip() # We remove html tags
						dates = re.sub(r".*\(m?\.? ?(\d.*)\)$", r"\1", dates) # We isolate the parenthesis, which can start with a m.
						dates = re.sub(r"(.*)\).*$", r"\1", dates)

						processedDates = getPeriod(dates)

						if processedDates != None:
							P580 = processedDates[0]
							P582 = processedDates[1]
			
			if person != None:
				print "Loading %s" % person
				personPage = pywikibot.Page(site, person)
				if not personPage.exists():
					# Red link
					print "No page"
					noPage = True
					pass
				else:
					if personPage.isRedirectPage():
						personPage = personPage.getRedirectTarget()
					personItem = pywikibot.ItemPage.fromPage(personPage)
					personQ = personItem.getID()

					if isHuman(personItem):
						output[personQ] = {}
						output[personQ]["item"] = personItem
						output[personQ]["Q"] = personQ
						output[personQ]["P580"] = P580
						output[personQ]["P582"] = P582
					else:
						print "%s is not a human" % person
						exit()

		if value != "" and len(output) == 0 and "[[" in value and not noPage and "<ref" not in value and not value.upper().startswith("SEE") :
			print "ISSSSSSSSSSSSSSSSSSSSSUE"
			print value
			exit()
	return output

def processVals(code, values):
	pass

def getInfobox(text):
	parsedExtText = mwparserfromhell.parse(text)
	infoboxes = parsedExtText.filter_templates(recursive=False)
	if len(infoboxes) != 1:
		print "%s : Error with infobox number (%s)" % (Q, len(infoboxes))
		exit()
	infobox = infoboxes[0]
	return infobox

def run():
	cur = db.cursor() 
	cur.execute("SELECT id, article, Q, tpl FROM genealogy where status = 0 and tpl!= '' limit 0,1")
	#cur.execute("SELECT id, article, Q, tpl FROM genealogy where Q='Q1288128'")
	
	for row in cur.fetchall() :
		id, article, Q, tpl = (row[0], row[1], row[2], row[3])
		stats = {
			"P26": 0,
			"P451": 0,
			"P40": 0,
			"P22": 0,
			"P25": 0,
			"P580": 0,
			"P582": 0,
			"P7": 0,
			"P9": 0
		}
		print "Running %s - %s" % (Q, article)
		print "http://en.wikipedia.org/wiki/%s" % (article.replace(" ", "_"))
		print "http://www.wikidata.org/wiki/%s" % Q
		print ""
		infobox = getInfobox(tpl)

		item = None

		for code in equivCodes.keys():
			values = getVals(code, infobox)
			if len(values) > 0:
				print "## %s ##" % code
				#print values
				if item == None:
					item = pywikibot.ItemPage(repo, Q)
					item.get()
				for Q in values.keys():
					print "\t values for %s : %s" % (code, Q)
					currentP = equivCodes[code]
					if code == "parents" or code == "relatives":
						if "P21" in values[Q]["item"].claims:
							gender = values[Q]["item"].claims["P21"][0].getTarget()
							if gender.getID() == "Q6581097":
								# Masculin
								codeGender = "M"
							elif gender.getID() == "Q6581072":
								codeGender = "F"
							else:
								print "GENDER A DEFINIR", gender.getID()
								exit()
							
							if codeGender == "M":
								if code == "parents":
									currentP = "P22"
								elif code == "relatives":
									currentP = "P7"
							elif codeGender == "F":
								if code == "parents":
									currentP = "P25"
								elif code == "relatives":
									currentP = "P9"

					existingClaim = None
					newParam = False
					P58 = {}
					P58["P580"] = 0
					P58["P582"] = 0

					if currentP in item.claims:
						for claim in item.claims[currentP]:
							if  Q == claim.getTarget().getID():
								existingClaim = claim

					if existingClaim != None:
						print "\t\tClaim already there, checking attributes"
						# Claim already exists, we are going to update it?

						for key, value in existingClaim.qualifiers.iteritems():
							year = value[0].getTarget().year
							if key == "P580":
								P58["P580"] = year
							if key == "P582":
								P58["P582"] = year
					else:
						print "We need to create the item"
						existingClaim = pywikibot.Claim(repo, str(currentP))
						existingClaim.setTarget(pywikibot.ItemPage(repo, str(Q)))
						item.addClaim(existingClaim)
						stats[currentP] += 1
						newParam = True

					for P in ["P580", "P582"]:
						if P in values[Q] and values[Q][P] != None:
							# We have got a year on wikipedia
							if P58[P] == 0:
								# Nothing yet, we can add if safely
								newYear = values[Q][P]
								claimDate = pywikibot.Claim(repo, str(P))
								date = pywikibot.WbTime(year=newYear)
								claimDate.setTarget(date)
								existingClaim.addQualifier(claimDate)
								newParam = True
								stats[P] += 1
							elif str(P58[P]) == str(values[Q][P]):
								pass
							else:
								print "Issue with the year"
								print P58[P]
								print values[Q][P]
								exit()
								# Already a value, we need to check if it is the same


					if newParam == True:
						print "\t\t\tAjout d'un claim ou claim existant sans source"
						try:
							existingClaim.addSource(importedEnWikipedia)
						except:
							# Source already there
							pass


		if item == None:
			print "No information on wp"
			# We have not changed anything, we can update
			cur.execute("UPDATE genealogy set status=1 where id=%s" % id)
			db.commit()
		else:
			# We have processed the record and might have updated at least one field
			sql = "UPDATE genealogy set status=2 "
			for code in stats.keys():
				sql += ", `%s`= (%s + %s)" % (code, code, stats[code])
			sql += " where id=%s" % id
			cur.execute(sql)
			db.commit()
			pass

if __name__ == "__main__":
	run()