# -*- coding: utf-8 -*-
#!/usr/bin/python
import pywikibot
site = pywikibot.Site("fr", "wikipedia")

tpl_name = "Template:Lions rugby"
tpl_page=pywikibot.Page(site, tpl_name)
text = tpl_page.get(get_redirect=True)
print text