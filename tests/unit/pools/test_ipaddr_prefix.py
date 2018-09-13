import unittest
import sys
import logging
import pytest
from os import path

from resource_manager.pools.ipaddr_prefixes import PrefixesPool

class Test_Validate_Init(unittest.TestCase):
    
    def test_init_no_shard(self):
        sub = PrefixesPool('192.168.0.0/16', 24)

        self.assertEqual(sub.nbr_shard, 1 )
        self.assertEqual(sub.nbr_subnets, 256 )
        self.assertEqual(list(sub.sub_by_key.keys()), ['192.168.0.0/16'] )

    def test_init_2_shards(self):
        sub = PrefixesPool('192.0.0.0/8', 25)

        self.assertEqual(sub.nbr_shard, 2 )
        self.assertEqual(sub.nbr_subnets, 131072 )
        self.assertEqual(list(sub.sub_by_key.keys()), ['192.0.0.0/9', '192.128.0.0/9'] )

    def test_init_4_shards(self):
        sub = PrefixesPool('192.0.0.0/8', 26)

        self.assertEqual(sub.nbr_shard, 4 )
        self.assertEqual(sub.nbr_subnets, 262144 )

    def test_init_128_shards(self):
        sub = PrefixesPool('192.0.0.0/8', 31)

        self.assertEqual(sub.nbr_shard, 128 )
        self.assertEqual(sub.nbr_subnets, 8388608 )

class Test_Validate_Get_Subnet(unittest.TestCase):
    
    def test_v4_no_owner(self):
        sub = PrefixesPool('192.168.0.0/16', 24)

        self.assertEqual(str(sub.get_subnet()), '192.168.0.0/24' )
        self.assertEqual(str(sub.get_subnet()), '192.168.1.0/24' )
    
    def test_no_more_subnet(self):
        sub = PrefixesPool('192.0.0.0/22', 24)

        self.assertEqual(str(sub.get_subnet()), '192.0.0.0/24' )
        self.assertEqual(str(sub.get_subnet()), '192.0.1.0/24' )
        self.assertEqual(str(sub.get_subnet()), '192.0.2.0/24' )
        self.assertEqual(str(sub.get_subnet()), '192.0.3.0/24' )
        self.assertEqual(sub.get_subnet(), False )

    @pytest.mark.long
    def test_v6_no_owner(self):
        sub = PrefixesPool('2620:135:6000:fffe::/64', 127)

        self.assertEqual(str(sub.get_subnet()), '2620:135:6000:fffe::/127' )

class Test_Validate_Check_if_Already_Reserved(unittest.TestCase):
    
    def test_v4_no_owner(self):
        sub = PrefixesPool('192.168.0.0/16', 24)

        self.assertEqual(str(sub.get_subnet(identifier='first')), '192.168.0.0/24' )
        self.assertEqual(str(sub.get_subnet(identifier='second')), '192.168.1.0/24' )

        self.assertTrue(sub.check_if_already_allocated(identifier='second'))
        self.assertFalse(sub.check_if_already_allocated(identifier='third'))
           

class Test_Validate_Reserve(unittest.TestCase):
    
    def test_no_owner(self):
        sub = PrefixesPool('192.168.0.0/16', 24)

        self.assertEqual(sub.reserve('192.168.0.0/24'), True )
        self.assertEqual(str(sub.get_subnet()), '192.168.1.0/24' )


    def test_wrong_input(self):
        sub = PrefixesPool('192.168.0.0/16', 24)

        ## Out of sub
        self.assertEqual(sub.reserve('192.192.1.0/24', identifier='first'), False )
        
        
    def test_with_owner(self):
        sub = PrefixesPool('192.192.0.0/16', 24)

        self.assertEqual(sub.reserve('192.192.0.0/24', identifier='first'), True )
        self.assertEqual(sub.reserve('192.192.1.0/24', identifier='second'), True )
        
        self.assertEqual(str(sub.get_subnet()), '192.192.2.0/24' )

    
# # Test negative cases:
#   - IP out of range, 
#   - IP already reserved

def main():
    unittest.main()

if __name__ == '__main__':
    main()