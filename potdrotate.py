# vim: set fileencoding=utf-8 :

import pywikibot, mwparserfromhell
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from pprint import pprint
import re

def dagen(today):
	"""
	>>> next(dagen(date(2016, 10, 20)))
	datetime.date(2016, 10, 22)
	"""
	# last_day = today.replace(day = calendar.monthrange(today.year, today.month)[1])

	# Volgende maand tot 'gisteren'
	d1 = today + relativedelta(days=+2)
	d2 = today + relativedelta(days=-2, months=+1)

	delta = d2 - d1

	for i in range(delta.days + 1):
	    yield d1 + timedelta(days=i)

def potdArtikel(site, day):
	name = potdArtikelnaam(day)
	page = pywikibot.Page(site, name)
	
	return potdDescription(page.text)

def potdDescription(text):
	"""
	>>> potdDescription('')
	>>> potdDescription('{{Potd description|1=Een beschrijving.|2=nl|3=2016|4=10|5=07}}')
	u'Een beschrijving.'
	"""
	if text == '':
		return None

	return argumentFromTemplate(text, 'Potd description', '1')

def argumentFromTemplate(text, template, argument):
	wikicode = mwparserfromhell.parse(text)
	templates = wikicode.filter_templates()
	description = [x for x in templates if x.name.matches(template)]

	if description == None or description == []:
		return None

	sjabloon = description[0]
	if not sjabloon.has_param(argument):
		return None

	return sjabloon.get(argument).value

def potdBestandsnaam(site, day):
	name = potdBestandsnaamartikelnaam(day)
	page = pywikibot.Page(site, name)

	return argumentFromTemplate(page.text, 'Potd filename', '1')

def potdArtikelnaam(day):
	"""
	>>> potdArtikelnaam(date(2016, 4, 1))
	'Template:Potd/2016-04-01 (nl)'
	"""
	return "Template:Potd/%04d-%02d-%02d (nl)" % (day.year, day.month, day.day)

def potdBestandsnaamartikelnaam(day):
	"""
	>>> potdBestandsnaamartikelnaam(date(2016, 4, 1))
	'Template:Potd/2016-04-01'
	"""
	return "Template:Potd/%04d-%02d-%02d" % (day.year, day.month, day.day)

def main(*args):
	local_args = pywikibot.handle_args(args)

	commons = pywikibot.Site(code="commons", fam="commons")
	site = pywikibot.Site(code="nl", fam="wikipedia")

	editSummary = 'Robot: Bijwerken afbeelding van de dag (zie [[Gebruiker:Frank Geerlings/Toelichting/Bijwerken afbeelding van de dag|toelichting]])'

	# Deze maand vanaf morgen
	today = date.today()

	metbeschrijvingen = map(lambda x: (x, x.day, potdArtikel(commons, x)), dagen(today))
	bron = [a + (None,) if a[2] == None else a + (potdBestandsnaam(commons, a[0]),) for a in metbeschrijvingen if a[2]]

	descriptionPage = pywikibot.Page(site, 'Sjabloon:Hoofdpagina - afbeelding van de dag - onderschrift')
	descriptionText = getD(bron, descriptionPage)
	# pywikibot.showDiff(descriptionPage.text, descriptionText)

	descriptionChanged = descriptionPage.text != descriptionText

	filePage = pywikibot.Page(site, 'Sjabloon:Hoofdpagina - afbeelding van de dag')
	fileText = getFiletext(bron, filePage)
	# pywikibot.showDiff(filePage.text, fileText)

	fileChanged = filePage.text != fileText

	if fileChanged or descriptionChanged:
		# Alleen allebei tegelijk opslaan, als de een dan ook de ander
		descriptionPage.text = descriptionText
		descriptionPage.save(editSummary, minor=False)

		filePage.text = fileText
		filePage.save(editSummary, minor=False)

def simplifyWikisyntax(text):
	"""
	>>> simplifyWikisyntax(u'Mid-sentence [[:nl:Link|links]] work')
	u'Mid-sentence [[Link|links]] work'

	>>> simplifyWikisyntax(u'[[:nl:Self-contained link|Self-contained link]]')
	u'[[Self-contained link]]'

	>>> simplifyWikisyntax(u'[[Category:Picture of the day]]')
	u'[[Category:Picture of the day]]'

	Just so you'll see the next test is correct:

	>>> u'–'
	u'\\xe2\\x80\\x93'

	Unicode characters get replaced properly:

	>>> simplifyWikisyntax(u'Article about [[:nl:–|–]] (em-dash)')
	u'Article about [[\\xe2\\x80\\x93]] (em-dash)'

	>>> simplifyWikisyntax(u'')
	u''
	"""

	nointerwiki = re.sub(ur'\[\[:nl:(.*?)\]\]', u"[[\\1]]", unicode(text))
	nodoubles = re.sub(ur'\[\[(.*?)\|\1\]\]', u"[[\\1]]", nointerwiki)

	return unicode(nodoubles)

def D(datum, beschrijving):
	return u"{{Potd description|1=%s|2=nl|3=%04d|4=%02d|5=%02d}}\n  " % (simplifyWikisyntax(beschrijving), datum.year, datum.month, datum.day)

def getD(bron, page):
	wikicode = mwparserfromhell.parse(page.text)
	switch = wikicode.filter_templates()[0]

	for datum, dag, beschrijving, bestandsnaam in bron:
		switch.get('<!--%02d-->%d' % (dag, dag)).value = D(datum, beschrijving)

	newText = unicode(wikicode)

	return newText

def getFiletext(bron, filePage):
	wikicode = mwparserfromhell.parse(filePage.text)
	templates = wikicode.filter_templates()
	multiview = [x for x in templates if x.name.matches('Multiview')][0]

	for datum, dag, beschrijving, bestandsnaam in bron:
		multiview.get(dag).value = multiviewRegel(dag, bestandsnaam)

	newText = unicode(wikicode)

	return newText

def multiviewRegel(dag, bestandsnaam):
	return u"<!--%02d-->[[Image:%s|245x180px|{{Hoofdpagina - afbeelding van de dag - onderschrift}}]]\n  " % (dag, bestandsnaam)

if __name__ == "__main__":
	try:
		main()
	except Exception:
		pywikibot.error("Fatal error:", exc_info=True)
