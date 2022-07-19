# vim: set fileencoding=utf-8 :

import mwparserfromhell
import re

def simplify_wikisyntax(text):
	"""
	>>> simplify_wikisyntax('Mid-sentence [[:nl:Link|links]] work')
	'Mid-sentence [[Link|links]] work'

	>>> simplify_wikisyntax('[[:nl:Self-contained link|Self-contained link]]')
	'[[Self-contained link]]'

	>>> simplify_wikisyntax('[[Category:Picture of the day]]')
	'[[Category:Picture of the day]]'

	The {{w}} template that is an interwiki shortcut on commons has a totally
	different application on wikinl, so it gets translated to normal wikilink:

	>>> simplify_wikisyntax('{{w|1=Quito|3=nl}}, de hoofdstad van {{w|1=Ecuador|3=nl}}')
	'[[Quito]], de hoofdstad van [[Ecuador]]'

	Just so you'll see the next test is correct:

	>>> '–'
	'–'

	Unicode characters get replaced properly:

	>>> simplify_wikisyntax('Article about [[:nl:–|–]] (em-dash)')
	'Article about [[–]] (em-dash)'

	>>> simplify_wikisyntax('Panorama van de oude stad en het fort in {{W|Salzburg||nl}} (Oostenrijk), gezien vanop de {{W|M\\xf6nchsberg||nl}}.')
	'Panorama van de oude stad en het fort in [[Salzburg]] (Oostenrijk), gezien vanop de [[M\\xf6nchsberg]].'

	>>> simplify_wikisyntax('')
	''

	Categories are assumed to be on commons:

	>>> simplify_wikisyntax('[[:Category:Shockwave (Jet Truck)|Shockwave Truck]]')
	'[[:c:Category:Shockwave (Jet Truck)|Shockwave Truck]]'
	"""
	text = replace_commons_interwiki(text)
	text = re.sub(r'\[\[:Category:(.*?)\]\]', "[[:c:Category:\\1]]", text)
	text = re.sub(r'\[\[:nl:(.*?)\]\]', "[[\\1]]", text)
	text = re.sub(r'\[\[(.*?)\|\1\]\]', "[[\\1]]", text)

	return text

def replace_commons_interwiki(wikitext):
	"""
	We don't do interwiki's to non-wikipedia's, at least have not explicitly tested that.
	We also don't do the {{Wn}} (etc) shortcuts.

	Full production example:

	>>> replace_commons_interwiki('{{w|1=Quito|3=nl}}, de hoofdstad van {{w|1=Ecuador|3=nl}}, gezien vanaf {{w|1=El Panecillo|3=nl}}')
	'[[:nl:Quito|Quito]], de hoofdstad van [[:nl:Ecuador|Ecuador]], gezien vanaf [[:nl:El Panecillo|El Panecillo]]'

	The default language in {{W}} is 'en', so we copy that behaviour:

	>>> replace_commons_interwiki('{{W|Page name|Display name}}')
	'[[:en:Page name|Display name]]'

	>>> replace_commons_interwiki('{{W|Page name|Display name|nl}}')
	'[[:nl:Page name|Display name]]'

	In-line language prefix supersedes language argument:

	>>> replace_commons_interwiki('{{W|nl:Page name|Display name|it}}')
	'[[:nl:Page name|Display name]]'
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

		replacement = '[[:%s:%s|%s]]' % (lang, art, display)

		wikicode.replace(w, replacement)

	return str(wikicode) # Doing str() because it can end up being None, which we don't want it to return
