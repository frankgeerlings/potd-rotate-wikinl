# vim: set fileencoding=utf-8 :

from datetime import date
from dateutil.relativedelta import relativedelta
from itertools import groupby
from operator import itemgetter
import re

def readable_dates(data):
	"""
	>>> readable_dates([date(2016, 11, 11), date(2016, 11, 12), date(2016, 11, 14)])
	'11-12 nov en 14 nov'
	"""
	return daterangefix(lexical_join(list(combine_ranges(map_formatter_to_range_groups(date_range_groups(data), date_as_text), lambda x, y: "%s-%s" % (x, y)))))

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

def date_as_text(date):
	"""Convert a date to a (Dutch) string consisting of date and month only (no year, Dutch 3-character month abbreviation)"""
	return '%d %s' % (date.day, ['jan', 'feb', 'mrt', 'apr', 'mei', 'jun', 'jul', 'aug', 'sep', 'okt', 'nov', 'dec'][date.month - 1])

def date_range_groups(data):
	"""
	>>> date_range_groups([date(2016, 11, 11), date(2016, 11, 12), date(2016, 11, 14)])
	[(datetime.date(2016, 11, 11), datetime.date(2016, 11, 12)), (datetime.date(2016, 11, 14), datetime.date(2016, 11, 14))]
	"""
	ranges = []
	for k, g in groupby(enumerate(data), lambda i_x: i_x[1]+relativedelta(days=-i_x[0])):
		group = list(map(itemgetter(1), g))
		ranges.append((group[0], group[-1]))

	return ranges

def map_formatter_to_range_groups(data, formatter):
	"""
	>>> map_formatter_to_range_groups([(date(2016, 11, 11), date(2016, 11, 12)), (date(2016, 11, 14), date(2016, 11, 14))], lambda i: i.strftime('%d %b'))
	[('11 Nov', '12 Nov'), ('14 Nov', '14 Nov')]
	"""
	return [(formatter(i), formatter(j)) for (i, j) in data]

def combine_ranges(data, combiner):
	"""
	>>> [i for i in combine_ranges([('11 Nov', '12 Nov'), ('14 Nov', '14 Nov')], lambda x, y: "%s-%s" % (x, y))]
	['11 Nov-12 Nov', '14 Nov']
	"""
	for i, j in data:
		if i == j:
			yield i
		else:
			yield combiner(i, j)

def lexical_join(data):
	"""
	>>> lexical_join(['11 Nov-12 Nov', '14 Nov', '16 Nov'])
	'11 Nov-12 Nov, 14 Nov en 16 Nov'
	"""
	if len(data) == 1:
		return data[0]

	return '%s en %s' % (', '.join(data[0:-1]), data[-1])
