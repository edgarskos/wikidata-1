# -*- coding: utf-8 -*-
#!/usr/bin/python
import MySQLdb, ConfigParser
import pywikibot
import sys
import re
import mwparserfromhell
from pywikibot import pagegenerators
'''
Ce script va récupérer les informations de club dans les infobox rugbyman
'''

site = pywikibot.Site("fr", "wikipedia")
repo = site.data_repository()

pywikibot.config.put_throttle = 1


config = ConfigParser.ConfigParser()
config.read("../mysql.conf")

teamEquiv = ConfigParser.ConfigParser()
teamEquiv.read("equipes.txt")

db = MySQLdb.connect(host=config.get("mysql", "host"), # your host, usually localhost
                     user=config.get("mysql", "user"), # your username
                      passwd=config.get("mysql", "password"), # your password
                      db=config.get("mysql", "database"),
                      charset='utf8') # name of the data base

importedFrWikipedia = pywikibot.Claim(repo, u'P143')
frWikipedia = pywikibot.ItemPage(repo, "Q8447")
importedFrWikipedia.setTarget(frWikipedia)

def addClaimCheck(item, P, target, qualifiers = []):
	# On va commencer par regarder si l'élément est déjà là
	myP = ""
	if item.claims.has_key(P):
		for Q in item.claims[P]:
			if Q.getTarget().getID() == target:
				myP = Q

	if myP == "":
		myP = pywikibot.Claim(repo, str(P))
		myP.setTarget(pywikibot.ItemPage(repo, target))
		item.addClaim(myP)
		print "## AJOUT DE LA PROFESSION ##"
		
	for myQ in qualifiers:
		needQ = True
		for key, value in myP.qualifiers.iteritems():
			if key == myQ.getID():
				needQ = False
				
		if needQ == True:
			print "On doit ajouter le qualificateur"
			myP.addQualifier(myQ)
	# On va ajouter la source s'il n'y en a pas
	if len(myP.sources) > 0 and "P143" in [key for key, value in myP.sources[0].iteritems()]:
		pass
	else:
		print "On doit ajouter la source"
		myP.addSource(importedFrWikipedia)


def cleanAnnee(annee):
	annee_depart = annee
	if "?" in annee:
		annee = "";

	annee = annee.strip()
	# On va supprimer les liens pour ne garder que la date
	m = re.match(r"^.*(\d{4})\]?\]?$", annee)
	if m:
		annee = m.group(1)

	m = re.match(r"^\d{4}$", annee)
	if not m:
		print "Attention annee : #%s#" % annee_depart
		annee = ""


	return annee

def getItem(label):
	page=pywikibot.Page(site, label)
	data = pywikibot.ItemPage.fromPage(page)
	data.get()
	return data

def parse(title):
	page = pywikibot.Page(site, title)
	text = page.get()
	return mwparserfromhell.parse(text)

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
		print "Unexpected error pour getQ:", sys.exc_info()[0]
		sys.exit()
    	raise


cur = db.cursor() 
cur.execute("SELECT id, Q, joueur FROM rugby where statut=0")
cur.execute("SELECT id, Q, joueur FROM rugby where id=42")

for row in cur.fetchall() :
	ID, Q, joueur = (row[0], row[1], row[2])
	itemJoueur = pywikibot.ItemPage(repo, str(Q))
	itemJoueur.get()
	print "#%s#" % joueur

	# On n'ajoute le P106 que si on n'a pas de 106
	if not itemJoueur.claims.has_key("P106"):
		addClaimCheck(itemJoueur, "P106", "Q13415036", [])


	parsedText = parse(joueur)
	templates = parsedText.filter_templates()
	up_club = 0
	up_saison = 0
	statut = 1
	for tpl in templates:
		if tpl.name.upper().strip() == "INFOBOX RUGBYMAN":
			clubExistsTpl = {}
			try:
				str_clubs = str(tpl.get("club").value.encode("utf-8").strip())
				if str_clubs == "":
					saisons = []
					clubs = []
				else:
					clubs = re.split("<br ?\/>", str_clubs)
					saisons = tpl.get("saison").value
					if saisons.strip() == "":
						saisons = [""] * len(clubs)
						# On va créer un tableau vide
					else:
						saisons = re.split("<br ?\/?>", str(saisons.encode("utf-8")))
			except ValueError:
				print "Paramètres du modèles non disponible, on va mettre -1"
				saisons = []
				clubs = []
				print "ERREUR : ",sys.exc_info()[0]

			try:
				equipe_nationale = re.split("<br ?\/>", str(tpl.get(u'\xe9quipe nationale').value.encode("utf-8").strip()))
				saison_nationale = tpl.get(u'ann\xe9e nationale').value.encode("utf-8").strip()
				if saison_nationale == "":
					saison_nationale = [""] * len(clubs)
					# On va créer un tableau vide
				else:
					saison_nationale = re.split("<br ?\/?>", str(saison_nationale))

				if len(saison_nationale) != len(equipe_nationale):
					print "Probleme saison vs equipe nationale"
				else:
					for i in range(0, len(saison_nationale)):
						N_equipe = equipe_nationale[i].strip()
						N_annee = saison_nationale[i].strip()
						
						if re.search("{{", N_equipe):
							# On est face à un template, on doit aller chercher quel est l'équipe derrière

							tpl_name = N_equipe.replace("{{", "").replace("}}", "")
							tpl_name = re.sub(r"^''(.*)''$", r"\1", tpl_name)
							tpl_name = "Template:%s" % tpl_name.decode("utf-8")

							try:
								tpl_equipe=pywikibot.Page(site, tpl_name)							
								text = tpl_equipe.get()
							except pywikibot.IsRedirectPage:
								text = tpl_equipe.getRedirectTarget().get()

							# On enlève les fichiers et les catégories:
							text = re.sub(r"\[\[(Fichier|Catégorie|File):[^\]]*\]\]", "", text)
							N_equipe = "[[" + re.sub(r".*?\[\[([^\|\]]*).*", r"\1", text.split("\n")[0]).encode("utf-8") + "]]"
						else:
							N_equipe = "[[" + re.sub(r"^\[\[([^\]\|]*).*$", r"\1", N_equipe) + "]]"
						
						saisons.append(N_annee)
						clubs.append(N_equipe)
							
			except ValueError:
				print "Paramètres du modèles non disponible pour équipe nationale, pas grave"			
				print "ERREUR : ",sys.exc_info()[0]

			if (len(clubs) == len(saisons)) and len(clubs) > 0 and len(saisons) > 0 :
				for i in range(0, len(clubs)):

					if "[[" in clubs[i]:
						thisClub = clubs[i].replace("[[", "").replace("]]", "").strip()
						match = re.search(r"^([^\|]*)\|?(.*)$", thisClub)

						link = match.group(1)
						label = match.group(2)

						if label != "":
							clubExistsTpl[label] = link
						else:
							clubExistsTpl[link] = link

						club = link
					else:
						# On est sur une info mais pas un lien, on va quand même vérifier que l'on n'est pas déjà passer dessus (cf Frédéric Michalak)
						if clubExistsTpl.has_key(clubs[i].strip()):
							club = clubExistsTpl[clubs[i].strip()]
						else:
							statut = -2
							print "Pas un lien, on passe (%s)" % clubs[i]
							club = ""
					
					if club != "":
						# club = re.sub(r"^([^\|]*)\|.*$", r"\1", clubs[i].replace("[[", "").replace("]]", "").strip())
						# On cherche le Q du club
						try:
							Qclub = teamEquiv.get("equipes", club)
						except:
							Qclub = getQ(club.decode("utf-8"))
							teamEquiv.set("equipes", club, Qclub)
							cfgfile = open("equipes.txt",'w')
							teamEquiv.write(cfgfile)
							cfgfile.close()

						if Qclub != "0":
							# On va gérer les périodes de début et de fin
							saison = saisons[i].strip()
							m = re.search("^(.*)\-(.*)$", saison)
							annee_debut = ""
							annee_fin = ""
							if m:
								# print "\t#%s# [%s] - de #%s# à #%s#" % (club, Qclub, m.group(1), m.group(2))
								annee_debut = m.group(1)
								annee_fin = m.group(2)
							else:
								# Si une seule année, on a début et fin identiques
								m = re.search("^(\d{4})$", saison)
								if m:
									annee_debut = m.group(1)
									annee_fin = m.group(1)

							annee_debut = cleanAnnee(annee_debut)
							annee_fin = cleanAnnee(annee_fin)

							if len(annee_debut) != 4 and annee_debut != "":
								print "Pb taille année début : #%s# [%s]" % (annee_debut, saison)
								sys.exit()

							if len(annee_fin) != 4 and annee_fin != "":
								print "Pb taille année fin : %s" % annee_fin
								sys.exit()

							# On ne veut pas d'année incoonue, partielle
							print "[%s] %s => %s # %s" % (Qclub, saison, annee_debut, annee_fin)
							# On va regarder si le club est déjà dans les claims
							itemClub = pywikibot.ItemPage(repo, str(Qclub))
							claimClub = False
							if itemJoueur.claims.has_key("P54"):
								for C in itemJoueur.claims["P54"]:
									if C.getTarget().getID() == Qclub:
										# Si aucun qualifiers pour le moment, on va reprendre cet item pour y ajouter ce qu'on veut
										if len(C.qualifiers.keys()) == 0:
											print "On n'a aucun qualifier, on va prendre ce claim"
											claimClub = C
										else:
											for key, value in C.qualifiers.iteritems():
												if key == "P580" or key == "P582":
													annee_test = value[0].getTarget().year
													# On vérifie si l'année fin est déjà une année fin pour le même club ou la même chose pour l'année début
													if (key == "P580" and str(annee_debut) == str(annee_test)) or (key == "P582" and str(annee_fin) == str(annee_test)):
														claimClub = C
							if not claimClub:
								print "\tCréation [%s]" % club
								claimClub = pywikibot.Claim(repo, str("P54"))
								claimClub.setTarget(itemClub)
								itemJoueur.addClaim(claimClub)
								up_club += 1
							else:
								# Si le club existe, on va devoir vérifier que la date de début est la même
								print "\tClub existant [%s]" % club
							P580 = "" # début
							P582 = "" # fin
							for key, value in claimClub.qualifiers.iteritems():
								if key == "P580":
									P580 = value
								if key == "P582":
									P582 = value

							if P580 == "" and annee_debut != "":
								claimDebut = pywikibot.Claim(repo, str("P580"))
								date = pywikibot.WbTime(year=annee_debut)
								claimDebut.setTarget(date)
								claimClub.addQualifier(claimDebut)
								up_saison += 1
								print "\tAjout date debut"

							if P582 == "" and annee_fin != "":
								claimFin = pywikibot.Claim(repo, str("P582"))
								date = pywikibot.WbTime(year=annee_fin)
								claimFin.setTarget(date)
								claimClub.addQualifier(claimFin)
								up_saison += 1
								print "\tAjout date fin"


							if up_club > 0 or up_saison > 0:
								claimClub.addSource(importedFrWikipedia)
			else:
				statut = -1
				print u"Erreur saisons vs clubs ou paramètres indéfinis [%s # %s]" % (Q, id)
				print clubs
				print saisons
	sql = "UPDATE rugby set Q = '%s', statut=%s, up_clubs=%s, up_saisons=%s where id = %s" % (Q, statut, up_club, up_saison, ID)
	db.cursor().execute(sql)
	db.commit()
	sys.exit()



	
sys.exit()




# pywikibot.extract_templates_and_params