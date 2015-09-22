# -*- coding: utf-8 -*-
#!/usr/bin/python

import unittest
from processor import getPeriod, getVals, getInfobox
import ConfigParser
import MySQLdb

config = ConfigParser.ConfigParser()
config.read("../../wikidata/mysql.conf")

db = MySQLdb.connect(host=config.get("mysql", "host"), # your host, usually localhost
                     user=config.get("mysql", "user"), # your username
                      passwd=config.get("mysql", "password"), # your password
                      db=config.get("mysql", "database"),
                      charset='utf8') # name of the data base

class TestProcessor(unittest.TestCase):
	def test_parse_date_range(self):
		"""Test extract_from_range()."""
		values = [
			("1915–1919", ("1915", "1919")),
			("", None),
			("1900-", ("1900", "")),
			("1912", None),
			("1970–86", ("1970", "1986"))
		]

		for value, expected in values:
			self.assertEqual(getPeriod(value), expected)

	def my_test_parser(self, code, value, expected):
		cur = db.cursor() 
		cur.execute("SELECT tpl FROM genealogy where Q = '%s'" % value)
		tpl = cur.fetchone()[0]
		infobox = getInfobox(tpl)

		result = getVals(code, infobox)
		for Q in result:
			self.assertEqual(result[Q]["Q"], expected[Q]["Q"])
			self.assertEqual(result[Q]["P580"], expected[Q]["P580"])
			self.assertEqual(result[Q]["P582"], expected[Q]["P582"])

	def test_parsing_spouses(self):
		values = [
			("Q853", ({u'Q3217941': {'Q': u'Q3217941', 'P582': '1986', 'P580': '1970'}, u'Q1981049': {'Q': u'Q1981049', 'P582': '1970', 'P580': '1957'}})),
			("Q8006", ({u'Q3032150': {'Q': u'Q3032150', 'P582': '1985', 'P580': '1945'}} ) )
		]
		for value, expected in values:
			self.my_test_parser("spouse", value, expected)

	def test_parsing_children(self):
		values = [
			("Q474235", ({u'Q185696': {'Q': u'Q185696', 'P582': None, 'P580': None}, u'Q3617650': {'Q': u'Q3617650', 'P582': None, 'P580': None}, u'Q2821626': {'Q': u'Q2821626', 'P582': None, 'P580': None}, u'Q5363492': {'Q': u'Q5363492', 'P582': None, 'P580': None}})),
			("Q72984", {u'Q371716': {'Q': u'Q371716', 'P582': None, 'P580': None}, u'Q5976701': {'Q': u'Q5976701', 'P582': None, 'P580': None}, u'Q433368': {'Q': u'Q433368', 'P582': None, 'P580': None}, u'Q6969557': {'Q': u'Q6969557', 'P582': None, 'P580': None}, u'Q7185654': {'Q': u'Q7185654', 'P582': None, 'P580': None}, u'Q5258318': {'Q': u'Q5258318', 'P582': None, 'P580': None}, u'Q13218111': {'Q': u'Q13218111', 'P582': None, 'P580': None}})
		]
		for value, expected in values:
			self.my_test_parser("children", value, expected)


if __name__ == '__main__':
	unittest.main()