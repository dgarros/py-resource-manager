import unittest
import requests_mock
import yaml
import pytest
from os import path

from resource_manager.backend.netbox_net_manager import NetboxNetManager

here = path.abspath(path.dirname(__file__))

FIXTURE_DIR = "fixtures/"

VALID_CONFIG_1 = {
    'netbox': {
        'address': 'http://mock'
    }
}

class Test_NetboxNetManager(unittest.TestCase):

    def test_init_not_valid(self):

        with pytest.raises(Exception) as e_info:
            NetboxNetManager(
                config={}, 
            )

    def test_init_valid(self):
        net_manager = NetboxNetManager(config=VALID_CONFIG_1)
        self.assertTrue(1)

    @requests_mock.mock()
    def test_basic(self, m):

        test03_1 = load_fixture("test03_1_ipam_prefixes")
        test03_2 = load_fixture("test03_2_ipam_prefixes")
        m.get(
            "http://mock/api/ipam/prefixes/?%s" % test03_1["params"],
            json=test03_1["response"],
        )
        m.get(
            "http://mock/api/ipam/prefixes/?%s" % test03_2["params"],
            json=test03_2["response"],
        )

        nnm = NetboxNetManager(config=VALID_CONFIG_1)

        self.assertEqual(str(nnm.resolve(var_type="NET4", var_params="loopback/26")), "10.10.0.64/26")
        self.assertEqual(str(nnm.resolve(var_type="NET4", var_params="loopback/26", identifier="first")), "10.10.0.0/26")
        self.assertEqual(str(nnm.resolve(var_type="NET4", var_params="loopback/26", identifier="first")), "10.10.0.0/26")
        self.assertEqual(str(nnm.resolve(var_type="NET4", var_params="loopback/26", identifier="fourth")), "10.10.0.192/26")
        self.assertEqual(str(nnm.resolve(var_type="NET4", var_params="loopback/24", identifier="fifth")), "10.10.1.0/24")
    
def load_fixture(name):
    return yaml.load(open(here + "/" + FIXTURE_DIR + name + ".json"))
