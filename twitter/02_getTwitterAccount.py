# -*- coding: utf-8 -*-
#!/usr/bin/python
import MySQLdb
import pywikibot
import sys
import re
import mwparserfromhell
import re
from pywikibot import pagegenerators

config = ConfigParser.ConfigParser()
config.read("../mysql.conf")

db = MySQLdb.connect(host=config.get("mysql", "host"), # your host, usually localhost
                     user=config.get("mysql", "user"), # your username
                      passwd=config.get("mysql", "password"), # your password
                      db=config.get("mysql", "database"),
                      charset='utf8') # name of the data base

site = pywikibot.Site("en", "wikipedia")


cur = db.cursor() 
cur.execute("SELECT id, title FROM twitter where status=0")

for row in cur.fetchall() :
	idPage, title = (row[0], row[1])
	print "~~ %s ~~" % title
	page=pywikibot.Page(site, title.decode("utf-8"))
	text = page.get()
	parsedText = mwparserfromhell.parse(text)
	externalLinks = ""
	headers = [(len(match.group(1)), match.group(2).strip(), match.start(), match.end()) for match in re.compile(r'^(=+) *(.*) *\1 *$', re.M).finditer(page.text)]
	for (id, header) in enumerate(headers):
		if re.match(r'External links', header[1].strip()):
			if len(headers) > (id + 1):
				externalLinks = page.text[header[3]:]
			else:
				externalLinks = page.text[header[3]:]

	if externalLinks != "":
		parsedExtText = mwparserfromhell.parse(externalLinks)
		templates = parsedExtText.filter_templates()
		twitterName = "";

		for tpl in templates:
			if tpl.name.upper().strip() == "TWITTER" or tpl.name.upper().strip() == "TWITTER.COM":
				if tpl.has("id"):
					twitterName = tpl.get("id").value
				else:
					if len(tpl.params) == 1:
						# Only one param, that is the username
						twitterName = tpl.get(1).value
					elif len(tpl.params) == 2:
						twitterName = tpl.get(1).value
		twitterName = str(twitterName)
		twitterName = twitterName.replace("http://twitter.com/#!/", "")
		twitterName = twitterName.replace("http://www.twitter.com/#!/", "")
		twitterName = twitterName.replace("https://twitter.com/", "")
		twitterName = twitterName.replace("https://www.twitter.com/", "")
		twitterName = twitterName.replace("http://twitter.com/", "")
		twitterName = twitterName.replace("http://www.twitter.com/", "")
		twitterName = twitterName.replace("twitter.com/", "")
		twitterName = re.sub(r"^@", "", str(twitterName))


		if "@" in twitterName or "TWITTER" in twitterName.upper():
			print str(twitterName)
			print twitterName
			
			exit()

		if twitterName != "":
			db.cursor().execute("UPDATE twitter set `status` = 1, `ta`=%s where id=%s" % (db.escape(twitterName), idPage))
			db.commit()
		else:
			print "NO TWITTER NAME"
			db.cursor().execute("UPDATE twitter set `status` = -1 where id=%s" % (idPage))
			db.commit()

	else:
		db.cursor().execute("UPDATE twitter set `status` = -1 where id=%s" % (idPage))
		db.commit()
