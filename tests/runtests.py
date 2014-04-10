#!/usr/bin/env python
import doctest
import unittest

from taxi.parser.parsers import plaintext

suite = unittest.TestSuite()
suite.addTest(unittest.TestLoader().discover('.'))
suite.addTest(doctest.DocTestSuite(plaintext))
