import unittest
import sys
import logging
import pytest
from os import path

from resource_manager.pools.integer import IntegerPool

class Test_Validate_Integer_Range(unittest.TestCase):
    
    def test_init_valid(self):

        ipool = IntegerPool('test', start=1, end=10)
        assert(isinstance(ipool, IntegerPool))


    def test_init_invalid(self):

        with pytest.raises(Exception):
            ipool = IntegerPool('test', start=10, end=8)

        with pytest.raises(Exception):
            ipool = IntegerPool('test', start=10, end=10)

    def test_get_integer_without_id(self):

        ipool = IntegerPool('test', start=1, end=10)

        self.assertEqual(ipool.get(), 1 )
        self.assertEqual(ipool.get(), 2 )

    def test_get_integer_with_id(self):

        ipool = IntegerPool('test', start=99, end=110)

        self.assertEqual(ipool.get(identifier='first'), 99 )
        self.assertEqual(ipool.get(), 100 )
        self.assertEqual(ipool.get(identifier='first'), 99 )

    def test_reserve(self):

        ipool = IntegerPool('test', start=99, end=110)

        self.assertEqual(ipool.reserve(integer=102, identifier='first'), True )
        self.assertEqual(ipool.get(identifier='first'), 102 )
        self.assertEqual(ipool.get(), 99 )
        

def main():
    unittest.main()

if __name__ == '__main__':
    main()