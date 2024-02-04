# vim: set fileencoding=utf-8 :

import pywikibot, mwparserfromhell
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from itertools import groupby
from operator import itemgetter
import re
import cleandate
from cleanwikitext import simplify_wikisyntax
import importlib

settings = importlib.import_module("potd-config")
config = settings.config[settings.lang]

def dagen(today):
	"""
	The first POTD that will be copied over is today's picture.

	>>> next(dagen(date(2016, 10, 20)))
	datetime.date(2016, 10, 20)

	The POTD furthest in the future that is to be copied over is as follows:

	>>> [i for i in dagen(date(2016, 10, 20))][-1]
	datetime.date(2016, 11, 18)

	The number of days in January exceeds the number of days in February by a few,
	this is a test to make sure that doesn't cause a conflict:

	>>> [i for i in dagen(date(2016, 1, 31))][-1]
	datetime.date(2016, 2, 27)
	"""
	d1 = today
	d2 = today + relativedelta(days=-2, months=+1)

	delta = d2 - d1

	for i in range(delta.days + 1):
	    yield d1 + timedelta(days=i)

def potdArtikel(site, day):
	name = potdArtikelnaam(day, settings.lang)
	page = pywikibot.Page(site, name)
	
	return potdDescription(page.text)

def potdDescription(text):
	"""
	>>> potdDescription('')
	>>> potdDescription('{{Potd description|1=Een beschrijving.|2=nl|3=2016|4=10|5=07}}')
	'Een beschrijving.'
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

def filename_from_potd_template(text):
	"""
	Newline in the comment:
	>>> filename_from_potd_template("{{Potd filename|1= Hohenloher Freilandmuseum - Baugruppe Mühlental - Mahlmühle aus Weipertshofen - Flur - blaue Wand mit Feuerlöscher (2).jpg"+chr(10)+"<!--DON'T EDIT BELOW THIS LINE. IT FILLS OUT THE REST FOR YOU. "+chr(10)+"-->|2=2022|3=08|4=31}}")
	'Hohenloher Freilandmuseum - Baugruppe Mühlental - Mahlmühle aus Weipertshofen - Flur - blaue Wand mit Feuerlöscher (2).jpg'

	>>> filename_from_potd_template("{{Potd filename|1= Verschiedenfarbige Schwertlilie (Iris versicolor)-20200603-RM-100257.jpg"+chr(10)+"<!--DON'T EDIT BELOW THIS LINE. IT FILLS OUT THE REST FOR YOU.  -->"+chr(10)+"|2=2022|3=08|4=28}}")
	'Verschiedenfarbige Schwertlilie (Iris versicolor)-20200603-RM-100257.jpg'

	If the template only contains a file name, don't attempt to decode parameters, but
	only strip superfluous whitespace: (case taken from Template:Potd/2021-06-28)

	>>> filename_from_potd_template("Zürich view Quaibrücke 20200702.jpg" + chr(10))
	'Zürich view Quaibrücke 20200702.jpg'

	Cyrillic character test:

	>>> filename_from_potd_template("{{Potd filename|Тавче Гравче.jpg|2021|07|28}}")
	'Тавче Гравче.jpg'

	"""

	# It's a mwparser object, make it pure text so it's accepted by re, among other reasons
	value = str(text)

	if '{{' in value:
		value = str(argumentFromTemplate(text, 'Potd filename', '1'))

	return re.compile('<!--.*?-->', re.DOTALL).sub('', value).strip()

def potdBestandsnaam(site, day):
	name = potdBestandsnaamartikelnaam(day)
	page = pywikibot.Page(site, name)

	return filename_from_potd_template(page.text)

def potdArtikelnaam(day, lang):
	"""
	>>> potdArtikelnaam(date(2016, 4, 1), 'nl')
	'Template:Potd/2016-04-01 (nl)'
	"""
	return "Template:Potd/%04d-%02d-%02d (%s)" % (day.year, day.month, day.day, lang)

def potdBestandsnaamartikelnaam(day):
	"""
	>>> potdBestandsnaamartikelnaam(date(2016, 4, 1))
	'Template:Potd/2016-04-01'
	"""
	return "Template:Potd/%04d-%02d-%02d" % (day.year, day.month, day.day)

def main(*args):
	local_args = pywikibot.handle_args(args)

	commons = pywikibot.Site(code="commons", fam="commons")
	site = pywikibot.Site(code=settings.lang, fam="wikipedia")


	today = date.today()

	metbeschrijvingen = map(lambda x: (x, x.day, potdArtikel(commons, x)), dagen(today))
	bron = [a + (None,) if a[2] == None else a + (potdBestandsnaam(commons, a[0]),) for a in metbeschrijvingen if a[2]]

	descriptionPage = pywikibot.Page(site, config['description_page'])
	descriptionText, updatedDays = getD(bron, descriptionPage)

	descriptionChanged = descriptionPage.text != descriptionText

	filePage = pywikibot.Page(site, config['file_page'])
	fileText = getFiletext(bron, filePage)

	fileChanged = filePage.text != fileText

	if fileChanged or descriptionChanged:
		# Only save both at the same time. If we save one, we also save the other.

		edit_summary = config['edit_summary'] % cleandate.readable_dates(updatedDays, settings.lang)

		descriptionPage.text = descriptionText
		descriptionPage.save(edit_summary, minor=False)

		filePage.text = fileText
		filePage.save(edit_summary, minor=False)

	if today in updatedDays:
		refreshHomepage(site)

def refreshHomepage(site):
	page = pywikibot.Page(site, config['main_page'])
	site.purgepages([page])

def D(datum, beschrijving):
	return u"{{Potd description|1=%s|2=%s|3=%04d|4=%02d|5=%02d}}\n  " % (simplify_wikisyntax(beschrijving, settings.lang), settings.lang, datum.year, datum.month, datum.day)

def getD(bron, page):
	wikicode = mwparserfromhell.parse(page.text)
	switch = wikicode.filter_templates()[0]

	updatedDays = []

	for datum, dag, beschrijving, bestandsnaam in bron:
		existing = switch.get('<!--%02d-->%d' % (dag, dag))
		newValue = D(datum, beschrijving)

		if existing.value == newValue:
			continue

		existing.value = newValue
		updatedDays.append(datum)

	newText = wikicode

	return (newText, updatedDays)

def getFiletext(bron, filePage):
	wikicode = mwparserfromhell.parse(filePage.text)
	templates = wikicode.filter_templates()
	multiview = [x for x in templates if x.name.matches('Multiview')][0]

	for datum, dag, beschrijving, bestandsnaam in bron:
		multiview.get(dag).value = multiviewRegel(dag, bestandsnaam)

	newText = wikicode

	return newText

def multiviewRegel(dag, bestandsnaam):
	return u"<!--%02d-->[[Image:%s|%s|{{%s}}]]\n  " % (dag, bestandsnaam, config['image_dimensions'], config['description_template'])

if __name__ == "__main__":
	try:
		main()
	except Exception:
		pywikibot.error("Fatal error:", exc_info=True)
