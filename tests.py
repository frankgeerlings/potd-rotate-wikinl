import unittest
import doctest
import potdrotate

def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite(potdrotate))
    return tests
