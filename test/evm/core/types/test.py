import os
import sys
import unittest
from unknownlib.evm.core.types import check_type

class TestTypesMethods(unittest.TestCase):

    def test_check_types(self):
        self.assertTrue(check_type(type, type) is None)
        self.assertTrue(check_type(1, (int, str)) is None)
        self.assertRaises(TypeError, lambda: check_type(True, str))
        self.assertRaises(TypeError, lambda: check_type(True, (str, unittest.TestCase)))

if __name__ == '__main__':
    unittest.main()