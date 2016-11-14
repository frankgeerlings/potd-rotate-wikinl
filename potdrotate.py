# vim: set fileencoding=utf-8 :

import pywikibot, mwparserfromhell
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from pprint import pprint
from itertools import groupby
from operator import itemgetter
import re

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

	editSummary = 'Robot: Bijwerken afbeelding van de dag (%s, zie [[Gebruiker:Frank Geerlings/Toelichting/Bijwerken afbeelding van de dag|toelichting]])'

	today = date.today()

	metbeschrijvingen = map(lambda x: (x, x.day, potdArtikel(commons, x)), dagen(today))
	bron = [a + (None,) if a[2] == None else a + (potdBestandsnaam(commons, a[0]),) for a in metbeschrijvingen if a[2]]

	descriptionPage = pywikibot.Page(site, 'Sjabloon:Hoofdpagina - afbeelding van de dag - onderschrift/data')
	descriptionText, updatedDays = getD(bron, descriptionPage)
	# pywikibot.showDiff(descriptionPage.text, descriptionText)

	descriptionChanged = descriptionPage.text != descriptionText

	filePage = pywikibot.Page(site, 'Sjabloon:Hoofdpagina - afbeelding van de dag/data')
	fileText = getFiletext(bron, filePage)
	# pywikibot.showDiff(filePage.text, fileText)

	fileChanged = filePage.text != fileText

	if fileChanged or descriptionChanged:
		# Alleen allebei tegelijk opslaan, als de een dan ook de ander
		descriptionPage.text = descriptionText
		descriptionPage.save(editSummary % readableDates(updatedDays), minor=False)

		filePage.text = fileText
		filePage.save(editSummary % readableDates(updatedDays), minor=False)

	if today in updatedDays:
		refreshHomepage(site)

def refreshHomepage(site):
	page = pywikibot.Page(site, 'Hoofdpagina')
	site.purgepages([page])

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

	updatedDays = []

	for datum, dag, beschrijving, bestandsnaam in bron:
		existing = switch.get('<!--%02d-->%d' % (dag, dag))
		newValue = D(datum, beschrijving)

		if existing.value == newValue:
			continue

		existing.value = newValue
		updatedDays.append(datum)

	newText = unicode(wikicode)

	return (newText, updatedDays)

def readableDates(data):
	"""
	>>> readableDates([date(2016, 11, 11), date(2016, 11, 12), date(2016, 11, 14)])
	'11-12 nov en 14 nov'
	"""
	return daterangefix(lexicalJoin(list(combineRanges(mapFormatterToRangeGroups(dateRangeGroups(data), dateAsText), lambda x, y: "%s-%s" % (x, y)))))

def daterangefix(range):
	"""Group dates by month for non-month-crossing ranges. Works for multiple occurrences in the same string.

	>>> daterangefix('11 nov-12 nov')
	'11-12 nov'

	>>> daterangefix('30 nov-1 dec')
	'30 nov-1 dec'

	>>> daterangefix('1 nov-10 nov en 15 nov-16 nov')
	'1-10 nov en 15-16 nov'
	"""
	return re.sub(r'(\d+) (\w+)-(\d+) (\2)', r'\1-\3 \2', range)

def dateAsText(date):
	"""Convert a date to a (Dutch) string consisting of date and month only (no year, Dutch 3-character month abbreviation)"""
	return '%d %s' % (date.day, ['jan', 'feb', 'maa', 'apr', 'mei', 'jun', 'jul', 'aug', 'sep', 'okt', 'nov', 'dec'][date.month - 1])

def dateRangeGroups(data):
	"""
	>>> dateRangeGroups([date(2016, 11, 11), date(2016, 11, 12), date(2016, 11, 14)])
	[(datetime.date(2016, 11, 11), datetime.date(2016, 11, 12)), (datetime.date(2016, 11, 14), datetime.date(2016, 11, 14))]
	"""
	ranges = []
	for k, g in groupby(enumerate(data), lambda (i,x):x+relativedelta(days=-i)):
		group = map(itemgetter(1), g)
		ranges.append((group[0], group[-1]))

	return ranges

def mapFormatterToRangeGroups(data, formatter):
	"""
	>>> mapFormatterToRangeGroups([(date(2016, 11, 11), date(2016, 11, 12)), (date(2016, 11, 14), date(2016, 11, 14))], lambda i: i.strftime('%d %b'))
	[('11 Nov', '12 Nov'), ('14 Nov', '14 Nov')]
	"""
	return [(formatter(i), formatter(j)) for (i, j) in data]

def combineRanges(data, combiner):
	"""
	>>> [i for i in combineRanges([('11 Nov', '12 Nov'), ('14 Nov', '14 Nov')], lambda x, y: "%s-%s" % (x, y))]
	['11 Nov-12 Nov', '14 Nov']
	"""
	for i, j in data:
		if i == j:
			yield i
		else:
			yield combiner(i, j)

def lexicalJoin(data):
	"""
	>>> lexicalJoin(['11 Nov-12 Nov', '14 Nov', '16 Nov'])
	'11 Nov-12 Nov, 14 Nov en 16 Nov'
	"""
	if len(data) == 1:
		return data[0]

	return '%s en %s' % (', '.join(data[0:-1]), data[-1])

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
