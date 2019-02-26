import unittest
import doctest
import potdrotate
import cleandate
import cleanwikitext

def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite(potdrotate))
    tests.addTests(doctest.DocTestSuite(cleandate))
    tests.addTests(doctest.DocTestSuite(cleanwikitext))
    return tests
