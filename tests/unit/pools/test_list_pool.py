import unittest
import sys
import logging
import pytest
from os import path

from resource_manager.pools.list import ListPool, expand_list, expand_range


class Test_Expand_range(unittest.TestCase):
    def test_expand_single(self):

        self.assertEqual(expand_range("0-1,3"), [0, 1, 3])

    def test_expand_multiple(self):

        self.assertEqual(expand_range("0-1,3-6"), [0, 1, 3, 4, 5, 6])


class Test_Expand_list(unittest.TestCase):
    def test_expand_single(self):

        self.assertEqual(expand_list(["test[0-2]"]), ["test0", "test1", "test2"])

    def test_expand_multiple(self):

        test01 = ["t10", "t11", "t12", "t212", "t214"]

        self.assertEqual(expand_list(["t1[0-2]", "t2[12,14]"]), test01)


class Test_Validate_ListPool(unittest.TestCase):
    def test_init_valid(self):

        pool = ListPool("test", items_list=["t1", "t2"])
        self.assertIsInstance(pool, ListPool)

    # def test_init_invalid(self):

    #     with pytest.raises(Exception):
    #         ipool = IntegerPool('test', start=10, end=8)

    #     with pytest.raises(Exception):
    #         ipool = IntegerPool('test', start=10, end=10)

    def test_get_item_without_id(self):

        pool = ListPool("test", items_list=["t[1-9]"])

        self.assertEqual(pool.get_nbr_available(), 9)
        self.assertEqual(pool.get_list_size(), 9)
        self.assertEqual(pool.get(), "t1")
        self.assertEqual(pool.get(), "t2")
        self.assertEqual(pool.get_nbr_available(), 7)
        self.assertEqual(pool.get_list_size(), 9)
        self.assertEqual(pool.get(), "t3")

    def test_list_unordered(self):

        pool = ListPool("test", items_list=["t[5,2,1,6]"])

        self.assertEqual(pool.get(), "t5")
        self.assertEqual(pool.get(), "t2")
        self.assertEqual(pool.get(), "t1")
        self.assertEqual(pool.get(), "t6")

    def test_get_item_with_id(self):

        pool = ListPool("test", items_list=["t[5,2,1,6]"])

        self.assertEqual(pool.get(identifier="first"), "t5")
        self.assertEqual(pool.get(), "t2")
        self.assertEqual(pool.get(identifier="first"), "t5")

    def test_reserve(self):

        pool = ListPool("test", items_list=["t[5,2,1,6]"])

        self.assertEqual(pool.reserve(item="t2", identifier="first"), True)
        self.assertEqual(pool.get(identifier="first"), "t2")
        self.assertEqual(pool.get(), "t5")
        self.assertEqual(pool.get(), "t1")
