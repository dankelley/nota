#from __future__ import print_function
import unittest
import tempfile
import logging
from nota.notaclass import Nota
import os, sys

logger = logging.getLogger()
logger.addHandler(logging.StreamHandler(sys.stdout))
logger.level = logging.DEBUG

class TestNota(unittest.TestCase):

    def setUp(self):
        self.debug = False
        self.database = tempfile.NamedTemporaryFile(prefix="nota", delete=False)
        logger.debug("\nCreating database file %r.", self.database.name)
        self.nota = Nota(db=self.database.name, debug=self.debug)

    def test(self):
        self.nota.add(title="foo", keywords=["test","foo"], content="")
        self.assertEqual(1, len(self.nota.find_by_hash(hash=None, book=-1)))
        self.nota.add(title="bar", keywords=["test","bar"], content="")
        self.assertEqual(2, len(self.nota.find_by_hash(hash=None, book=-1)))
        self.assertEqual(1, len(self.nota.find_by_keyword(keywords=["foo"], strict_match=True)))
        self.assertEqual(1, len(self.nota.find_by_keyword(keywords=["bar"], strict_match=True)))
        self.assertEqual(0, len(self.nota.find_by_keyword(keywords=["foobar"], strict_match=True)))
        hash0 = self.nota.find_by_hash(hash=None)[0]["hash"]
        self.nota.delete(hash=hash0)
        self.assertEqual(1, len(self.nota.find_by_hash(hash=None)))
        self.assertEqual(1, len(self.nota.find_by_hash(hash=None, book=1)))


    def test_books(self):
        books = self.nota.book_list()
        self.assertEqual(2, len(books))
        self.assertEqual(books[0], "Trash")
        self.assertEqual(books[1], "Default")
        self.nota.book_rename("Default", "Test")
        books = self.nota.book_list()
        self.assertEqual(2, len(books))
        self.assertEqual(books[0], "Trash")
        self.assertEqual(books[1], "Test")

    def test_keywords(self):
        self.nota.add(title="foo", keywords=["test","foo"], content="")
        self.assertEqual(1, len(self.nota.find_by_hash(hash=None, book=-1)))
        self.nota.add(title="bar", keywords=["test","bar"], content="")
        keywords = self.nota.keyword_list()
        self.assertEqual(3, len(keywords))
        # the keywords are returned in alphabetical order
        self.assertEqual(keywords[0], "bar")
        self.assertEqual(keywords[1], "foo")
        self.assertEqual(keywords[2], "test")


    def tearDown(self):
        logger.debug("Removing temporary database file.")
        os.remove(self.database.name)

if __name__ == '__main__':
    unittest.main()

