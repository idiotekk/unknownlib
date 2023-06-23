import os
import sys
import unittest
from unknownlib.evm.core import Addr

class TestFastW3Methods(unittest.TestCase):

    def test_addr(self):
        test_addr = Addr("0x0938C63109801Ee4243a487aB84DFfA2Bba4589e")
        self.assertTrue(test_addr == test_addr.value.lower())
        self.assertRaises(ValueError, lambda: Addr(test_addr.value[:-2]))
        self.assertRaises(ValueError, lambda: Addr("000" + test_addr.value))
        self.assertRaises(ValueError, lambda: Addr(test_addr.value.replace("a", "z")))
        self.assertTrue(test_addr == Addr(test_addr.value))
        self.assertTrue(test_addr == Addr(test_addr.value.lower()))
        self.assertTrue(hash(test_addr) == hash(test_addr.value))
        self.assertTrue(len(test_addr.to_topic()) == 66)

if __name__ == '__main__':
    unittest.main()