#from __future__ import print_function
import unittest
from nota.notaclass import Nota

class TestNota(unittest.TestCase):

    def setUp(self):
        self.data = range(10)

    def test_01(self):
        self.assertEqual(self.data, range(10))

    def tearDown(self):
        pass
        #print("in tearDown")

if __name__ == '__main__':
    unittest.main()

