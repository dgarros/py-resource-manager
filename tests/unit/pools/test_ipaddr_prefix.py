import unittest
import sys
import logging
import pytest
import ipaddress
from os import path

from resource_manager.pools.ipaddr_prefixes import PrefixesPool

logging.basicConfig(level=logging.DEBUG)


class Test_Validate_Init(unittest.TestCase):
    def test_init_v4(self):
        sub = PrefixesPool("192.168.0.0/28")
        avail_subs = sub.get_nbr_available_subnets()

        self.assertEqual(avail_subs, {29: 2, 30: 0, 31: 0, 32: 0})
        self.assertEqual(
            sub.available_subnets[29], ["192.168.0.0/29", "192.168.0.8/29"]
        )

    def test_init_v6(self):
        sub = PrefixesPool("2001:db8::0/48")
        avail_subs = sub.get_nbr_available_subnets()

        self.assertEqual(avail_subs[49], 2)
        self.assertEqual(avail_subs[50], 0)


class Test_Validate_split_supernet(unittest.TestCase):
    def test_split_first(self):
        sub = PrefixesPool("192.168.0.0/24")

        sub.split_supernet(
            supernet=ipaddress.ip_network("192.168.0.128/25"),
            subnet=ipaddress.ip_network("192.168.0.128/27"),
        )
        avail_subs = sub.get_nbr_available_subnets()

        self.assertEqual(avail_subs[25], 1)
        self.assertEqual(avail_subs[26], 1)
        self.assertEqual(avail_subs[27], 2)
        self.assertEqual(avail_subs[28], 0)

        self.assertEqual(sub.available_subnets[25], ["192.168.0.0/25"])
        self.assertEqual(sub.available_subnets[26], ["192.168.0.192/26"])
        self.assertEqual(
            sub.available_subnets[27], ["192.168.0.128/27", "192.168.0.160/27"]
        )

    def test_split_middle(self):
        sub = PrefixesPool("192.168.0.0/24")

        sub.split_supernet(
            supernet=ipaddress.ip_network("192.168.0.128/25"),
            subnet=ipaddress.ip_network("192.168.0.192/27"),
        )
        avail_subs = sub.get_nbr_available_subnets()

        self.assertEqual(avail_subs[25], 1)
        self.assertEqual(avail_subs[26], 1)
        self.assertEqual(avail_subs[27], 2)
        self.assertEqual(avail_subs[28], 0)

        self.assertEqual(sub.available_subnets[25], ["192.168.0.0/25"])
        self.assertEqual(sub.available_subnets[26], ["192.168.0.128/26"])
        self.assertEqual(
            sub.available_subnets[27], ["192.168.0.192/27", "192.168.0.224/27"]
        )

    def test_split_end(self):
        sub = PrefixesPool("192.168.0.0/16")

        sub.split_supernet(
            supernet=ipaddress.ip_network("192.168.128.0/17"),
            subnet=ipaddress.ip_network("192.168.255.192/27"),
        )
        avail_subs = sub.get_nbr_available_subnets()

        self.assertEqual(avail_subs[17], 1)
        self.assertEqual(avail_subs[25], 1)
        self.assertEqual(avail_subs[26], 1)
        self.assertEqual(avail_subs[27], 2)
        self.assertEqual(avail_subs[28], 0)

        self.assertEqual(sub.available_subnets[17], ["192.168.0.0/17"])
        self.assertEqual(sub.available_subnets[26], ["192.168.255.128/26"])
        self.assertEqual(
            sub.available_subnets[27], ["192.168.255.192/27", "192.168.255.224/27"]
        )


class Test_Validate_Get_Subnet(unittest.TestCase):
    def test_v4_no_owner(self):
        sub = PrefixesPool("192.168.0.0/16")

        self.assertEqual(str(sub.get(size=24)), "192.168.0.0/24")
        self.assertEqual(str(sub.get(size=25)), "192.168.1.0/25")
        self.assertEqual(str(sub.get(size=17)), "192.168.128.0/17")
        self.assertEqual(str(sub.get(size=24)), "192.168.2.0/24")
        self.assertEqual(str(sub.get(size=25)), "192.168.1.128/25")

    def test_v4_with_owner(self):
        sub = PrefixesPool("192.168.0.0/16")

        self.assertEqual(
            str(sub.get(size=24, identifier="first")), "192.168.0.0/24"
        )
        self.assertEqual(
            str(sub.get(size=25, identifier="second")), "192.168.1.0/25"
        )
        self.assertEqual(
            str(sub.get(size=17, identifier="third")), "192.168.128.0/17"
        )
        self.assertEqual(
            str(sub.get(size=25, identifier="second")), "192.168.1.0/25"
        )
        self.assertEqual(
            str(sub.get(size=17, identifier="third")), "192.168.128.0/17"
        )

    def test_no_more_subnet(self):
        sub = PrefixesPool("192.0.0.0/22")

        self.assertEqual(str(sub.get(size=24)), "192.0.0.0/24")
        self.assertEqual(str(sub.get(size=24)), "192.0.1.0/24")
        self.assertEqual(str(sub.get(size=24)), "192.0.2.0/24")
        self.assertEqual(str(sub.get(size=24)), "192.0.3.0/24")
        self.assertEqual(sub.get(size=24), False)

    @pytest.mark.long
    def test_v6_no_owner(self):
        sub = PrefixesPool("2620:135:6000:fffe::/64")
        self.assertEqual(str(sub.get(size=127)), "2620:135:6000:fffe::/127")


class Test_Validate_Check_if_Already_Reserved(unittest.TestCase):
    def test_v4_no_owner(self):
        sub = PrefixesPool("192.168.0.0/16")

        self.assertEqual(
            str(sub.get(size=24, identifier="first")), "192.168.0.0/24"
        )
        self.assertEqual(
            str(sub.get(size=24, identifier="second")), "192.168.1.0/24"
        )

        self.assertTrue(sub.check_if_already_allocated(identifier="second"))
        self.assertFalse(sub.check_if_already_allocated(identifier="third"))


class Test_Validate_Reserve(unittest.TestCase):
    def test_no_owner(self):
        sub = PrefixesPool("192.168.0.0/16")

        self.assertEqual(sub.reserve("192.168.0.0/24"), True)
        self.assertEqual(str(sub.get(size=24)), "192.168.1.0/24")

    def test_wrong_input(self):
        sub = PrefixesPool("192.168.0.0/16")

        ## Out of sub
        self.assertEqual(sub.reserve("192.192.1.0/24", identifier="first"), False)

    def test_with_owner(self):
        sub = PrefixesPool("192.192.0.0/16")

        self.assertEqual(sub.reserve("192.192.0.0/24", identifier="first"), True)
        self.assertEqual(sub.reserve("192.192.1.0/24", identifier="second"), True)

        self.assertEqual(str(sub.get(size=24)), "192.192.2.0/24")


# # Test negative cases:
#   - IP out of range,
#   - IP already reserved


def main():
    unittest.main()


if __name__ == "__main__":
    main()
