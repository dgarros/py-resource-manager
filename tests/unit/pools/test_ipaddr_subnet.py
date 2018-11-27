import unittest
import yaml
import sys
import logging
from os import path

from resource_manager.pools.ipaddr_subnet import IpAddressPool


class Test_Validate_Get(unittest.TestCase):
    def test_nbr_address(self):

        sub1 = IpAddressPool("10.0.0.0/24")
        sub2 = IpAddressPool("10.0.0.0/30")
        sub3 = IpAddressPool("10.0.0.0/31")

        sub4 = IpAddressPool("2620:0000:0000::0/31")
        sub5 = IpAddressPool("2620:135:6000::0/126")
        sub6 = IpAddressPool("2620:135:6000::0/127")

        self.assertEqual(sub1.num_addresses, 254)
        self.assertEqual(sub2.num_addresses, 2)
        self.assertEqual(sub3.num_addresses, 2)

        self.assertEqual(sub4.num_addresses, 158456325028528675187087900670)
        self.assertEqual(sub5.num_addresses, 2)
        self.assertEqual(sub6.num_addresses, 2)

    def test_v4_no_owner(self):
        sub = IpAddressPool("10.0.0.0/30")

        self.assertEqual(str(sub.get()), "10.0.0.1")
        self.assertEqual(str(sub.get()), "10.0.0.2")

    def test_v4_with_label(self):
        sub = IpAddressPool("10.0.0.0/30")
        self.assertEqual(str(sub.get(identifier="first")), "10.0.0.1")
        self.assertEqual(str(sub.get(identifier="second")), "10.0.0.2")
        self.assertEqual(str(sub.get(identifier="first")), "10.0.0.1")

    def test_v4_with_id(self):
        sub = IpAddressPool("10.0.0.0/24")

        self.assertEqual(str(sub.get()), "10.0.0.1")
        self.assertEqual(str(sub.get(id=1)), "10.0.0.1")
        self.assertEqual(str(sub.get(id=4)), "10.0.0.4")

        self.assertEqual(str(sub.get(id=1, identifier="gateway")), "10.0.0.1")
        self.assertFalse(sub.get(id=1))

    def test_v6_no_owner(self):
        sub = IpAddressPool("2620:135:6000::0/126")

        self.assertEqual(str(sub.get()), "2620:135:6000::1")
        self.assertEqual(str(sub.get()), "2620:135:6000::2")

    def test_v6_with_label(self):
        sub = IpAddressPool("2620:135:6000::0/126")
        self.assertEqual(str(sub.get(identifier="first")), "2620:135:6000::1")
        self.assertEqual(str(sub.get(identifier="second")), "2620:135:6000::2")
        self.assertEqual(str(sub.get(identifier="first")), "2620:135:6000::1")

    def test_big_IpAddressPool(self):
        sub = IpAddressPool("2620:135:6000::0/64")
        self.assertEqual(str(sub.get(identifier="first")), "2620:135:6000::1")
        self.assertEqual(str(sub.get(identifier="second")), "2620:135:6000::2")
        self.assertEqual(str(sub.get(identifier="first")), "2620:135:6000::1")

    def test_only_if_exist(self):
        sub = IpAddressPool("10.0.0.0/24")
        self.assertEqual(str(sub.get(identifier="first")), "10.0.0.1")
        self.assertEqual(
            str(sub.get(identifier="first", only_if_exist=True)), "10.0.0.1"
        )
        self.assertEqual(sub.get(identifier="second", only_if_exist=True), False)


class Test_Validate_Reserve(unittest.TestCase):
    def test_no_owner(self):
        sub = IpAddressPool("10.0.0.0/30")

        self.assertEqual(sub.reserve("10.0.0.1"), True)
        self.assertEqual(str(sub.get()), "10.0.0.2")

    def test_with_owner(self):
        sub = IpAddressPool("10.0.0.0/30")

        self.assertEqual(sub.reserve("10.0.0.1", identifier="first"), True)
        self.assertEqual(str(sub.get(identifier="first")), "10.0.0.1")


class Test_Validate_Outofrange(unittest.TestCase):
    def test_no_more_ip(self):
        sub = IpAddressPool("10.0.0.0/30")

        self.assertEqual(str(sub.get()), "10.0.0.1")
        self.assertEqual(str(sub.get()), "10.0.0.2")
        self.assertIsNone(sub.get())
        self.assertIsNone(sub.get())


def main():
    unittest.main()


if __name__ == "__main__":
    main()
