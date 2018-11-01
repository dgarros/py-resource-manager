import unittest
import yaml
import sys
import logging
from os import path

from resource_manager.pools.ipaddr_subnet import IpAddressPool


class Test_Validate_get(unittest.TestCase):
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


class Test_Validate_Reserve(unittest.TestCase):
    def test_no_owner(self):
        sub = IpAddressPool("10.0.0.0/30")

        self.assertEqual(sub.reserve("10.0.0.1"), True)
        self.assertEqual(str(sub.get()), "10.0.0.2")

    def test_with_owner(self):
        sub = IpAddressPool("10.0.0.0/30")

        self.assertEqual(sub.reserve("10.0.0.1", identifier="first"), True)
        self.assertEqual(str(sub.get(identifier="first")), "10.0.0.1")

    ## Test negative cases:
    #   - IP out of range,
    #   - IP already reserved


def main():
    unittest.main()


if __name__ == "__main__":
    main()
