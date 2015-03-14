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
        self.data = range(10)
        self.database = tempfile.NamedTemporaryFile(prefix="nota", delete=False)
        logger.debug("\nCreating database file %r.", self.database.name)
        self.nota = Nota(db=self.database.name, debug=self.debug)

    def test_add(self):
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

    def tearDown(self):
        logger.debug("Removing temporary database file.")
        os.remove(self.database.name)

if __name__ == '__main__':
    unittest.main()

