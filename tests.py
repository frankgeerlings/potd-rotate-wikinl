import unittest
import doctest
import potdrotate
import cleandate

def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite(potdrotate))
    tests.addTests(doctest.DocTestSuite(cleandate))
    return tests
