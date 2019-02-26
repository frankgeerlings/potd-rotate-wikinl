# vim: set fileencoding=utf-8 :

import mwparserfromhell
import re

def simplify_wikisyntax(text):
	"""
	>>> simplify_wikisyntax(u'Mid-sentence [[:nl:Link|links]] work')
	u'Mid-sentence [[Link|links]] work'

	>>> simplify_wikisyntax(u'[[:nl:Self-contained link|Self-contained link]]')
	u'[[Self-contained link]]'

	>>> simplify_wikisyntax(u'[[Category:Picture of the day]]')
	u'[[Category:Picture of the day]]'

	The {{w}} template that is an interwiki shortcut on commons has a totally
	different application on wikinl, so it gets translated to normal wikilink:

	>>> simplify_wikisyntax(u'{{w|1=Quito|3=nl}}, de hoofdstad van {{w|1=Ecuador|3=nl}}')
	u'[[Quito]], de hoofdstad van [[Ecuador]]'

	Just so you'll see the next test is correct:

	>>> u'–'
	u'\\xe2\\x80\\x93'

	Unicode characters get replaced properly:

	>>> simplify_wikisyntax(u'Article about [[:nl:–|–]] (em-dash)')
	u'Article about [[\\xe2\\x80\\x93]] (em-dash)'

	>>> simplify_wikisyntax(u'Panorama van de oude stad en het fort in {{W|Salzburg||nl}} (Oostenrijk), gezien vanop de {{W|M\\xf6nchsberg||nl}}.')
	u'Panorama van de oude stad en het fort in [[Salzburg]] (Oostenrijk), gezien vanop de [[M\\xf6nchsberg]].'

	>>> simplify_wikisyntax(u'')
	u''
	"""

	nocommonsinterwiki = replaceCommonsInterwiki(unicode(text))
	nointerwiki = re.sub(ur'\[\[:nl:(.*?)\]\]', u"[[\\1]]", nocommonsinterwiki)
	nodoubles = re.sub(ur'\[\[(.*?)\|\1\]\]', u"[[\\1]]", nointerwiki)

	return unicode(nodoubles)

def replaceCommonsInterwiki(wikitext):
	"""
	We don't do interwiki's to non-wikipedia's, at least have not explicitly tested that.
	We also don't do the {{Wn}} (etc) shortcuts.

	Full production example:

	>>> replaceCommonsInterwiki(u'{{w|1=Quito|3=nl}}, de hoofdstad van {{w|1=Ecuador|3=nl}}, gezien vanaf {{w|1=El Panecillo|3=nl}}')
	u'[[:nl:Quito|Quito]], de hoofdstad van [[:nl:Ecuador|Ecuador]], gezien vanaf [[:nl:El Panecillo|El Panecillo]]'

	The default language in {{W}} is 'en', so we copy that behaviour:

	>>> replaceCommonsInterwiki(u'{{W|Page name|Display name}}')
	u'[[:en:Page name|Display name]]'

	>>> replaceCommonsInterwiki(u'{{W|Page name|Display name|nl}}')
	u'[[:nl:Page name|Display name]]'

	In-line language prefix supersedes language argument:

	>>> replaceCommonsInterwiki(u'{{W|nl:Page name|Display name|it}}')
	u'[[:nl:Page name|Display name]]'
	"""

	wikicode = mwparserfromhell.parse(wikitext)
	templates = wikicode.filter_templates()
	ws = [x for x in templates if x.name.matches('w')]

	for w in ws:
		lang = 'en'
		if w.has_param('3'):
			lang = w.get('3').value

		art = ''
		if w.has_param('1'):
			art = w.get('1').value

		if ':' in art:
			lang, art = art.split(':', 1)

		display = art
		if w.has_param('2') and len(w.get('2').value) > 0:
			display = w.get('2').value

		replacement = u'[[:%s:%s|%s]]' % (lang, art, display)

		wikicode.replace(w, replacement)

	return unicode(wikicode)
