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
        logger.debug("Checking adding a note.")
        self.nota.add(title="foo", keywords=["test","foo"], content="")
        logger.debug("Checking searching notes by hash.")
        self.assertEqual(1, len(self.nota.find_by_hash(hash=None, book=-1)))
        self.nota.add(title="bar", keywords=["test","bar"], content="")
        logger.debug(" find-by-hash test 1 ok.")
        self.assertEqual(2, len(self.nota.find_by_hash(hash=None, book=-1)))
        logger.debug(" find-by-hash test 2 ok.")
        logger.debug("Checking searching for notes by keywords.")
        self.assertEqual(1, len(self.nota.find_by_keyword(keywords=["foo"], strict_match=True)))
        logger.debug(" search-by-keyword test 1 ok.")
        self.assertEqual(1, len(self.nota.find_by_keyword(keywords=["bar"], strict_match=True)))
        logger.debug(" search-by-keyword test 2 ok.")
        self.assertEqual(0, len(self.nota.find_by_keyword(keywords=["foobar"], strict_match=True)))
        logger.debug(" search-by-keyword test 3 ok.")
        if self.debug:
            logger.debug("\n hashes %s" % self.nota.find_by_hash(hash=None))
        logger.debug("Checking note deletion.")
        hash0 = self.nota.find_by_hash(hash=None)[0]["hash"]
        if self.debug:
            logger.debug("\n hash0 %s" % hash0)
        self.nota.delete(hash=hash0)
        if self.debug:
            logger.debug("\n hashes %s" % self.nota.find_by_hash(hash=None, book=1))
        self.assertEqual(1, len(self.nota.find_by_hash(hash=None)))
        logger.debug(" note-deletion-check test 1 ok.")
        self.assertEqual(1, len(self.nota.find_by_hash(hash=None, book=1)))
        logger.debug(" note-deletion-check test 2 ok.")


    def test_books(self):
        logger.debug("Checking book names.")
        books = self.nota.book_list()
        self.assertEqual(2, len(books))
        logger.debug(" book-name test 1 ok.")
        self.assertEqual(books[0], "Trash")
        logger.debug(" book-name test 2 ok.")
        self.assertEqual(books[1], "Default")
        logger.debug(" book-name test 3 ok.")
        self.nota.book_rename("Default", "Test")
        logger.debug(" book-name test 3 ok.")
        books = self.nota.book_list()
        self.assertEqual(2, len(books))
        logger.debug(" book-name test 4 ok.")
        self.assertEqual(books[0], "Trash")
        logger.debug(" book-name test 5 ok.")
        self.assertEqual(books[1], "Test")
        logger.debug(" book-name test 5 ok.")

    def test_keywords(self):
        self.nota.add(title="foo", keywords=["test","foo"], content="")
        logger.debug("Checking searching notes by hash.")
        self.assertEqual(1, len(self.nota.find_by_hash(hash=None, book=-1)))
        self.nota.add(title="bar", keywords=["test","bar"], content="")
        keywords = self.nota.keyword_list()
        self.assertEqual(3, len(keywords))
        logger.debug(" keywords test 1 ok.")
        # the keywords are returned in alphabetical order
        self.assertEqual(keywords[0], "bar")
        logger.debug(" keywords test 2 ok.")
        self.assertEqual(keywords[1], "foo")
        logger.debug(" keywords test 3 ok.")
        self.assertEqual(keywords[2], "test")
        logger.debug(" keywords test 4 ok.")


    def tearDown(self):
        logger.debug("Removing temporary database file.")
        os.remove(self.database.name)

if __name__ == '__main__':
    unittest.main()

