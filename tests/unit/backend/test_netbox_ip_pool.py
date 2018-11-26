import unittest
import requests_mock
import yaml
from os import path

from resource_manager.backend.netbox_ip_pool import NetboxIpPool

here = path.abspath(path.dirname(__file__))

FIXTURE_DIR = "fixtures/"

class Test_NetboxIpPool(unittest.TestCase):
    @requests_mock.mock()
    def test_get_next(self, m):

        test_1 = load_fixture("test04_1_ipam_prefixes")
        test_2 = load_fixture("test04_2_ipam_ipaddresses")
        
        m.get(

            "http://mock/api/ipam/prefixes/?%s" % test_1["params"],
            json=test_1["response"],
        )
        m.get(
            "http://mock/api/ipam/ip-addresses/?%s" % test_2["params"],
            json=test_2["response"],
        )

        pool = NetboxIpPool(
            netbox="http://mock", site="test", role="loopback", family=4
        )

        self.assertEqual(str(pool.get()), "10.10.0.1/26")
        self.assertEqual(str(pool.get()), "10.10.0.3/26")


    @requests_mock.mock()
    def test_return_mask(self, m):

        test_1 = load_fixture("test04_1_ipam_prefixes")
        test_2 = load_fixture("test04_2_ipam_ipaddresses")
        
        m.get(
            "http://mock/api/ipam/prefixes/?%s" % test_1["params"],
            json=test_1["response"],
        )
        m.get(
            "http://mock/api/ipam/ip-addresses/?%s" % test_2["params"],
            json=test_2["response"],
        )

        pool = NetboxIpPool(
            netbox="http://mock", site="test", role="loopback", family=4
        )

        self.assertEqual(str(pool.get(return_mask=False)), "10.10.0.1")
        self.assertEqual(str(pool.get()), "10.10.0.3/26")


    @requests_mock.mock()
    def test_get_id(self, m):

        test_1 = load_fixture("test04_1_ipam_prefixes")
        test_2 = load_fixture("test04_2_ipam_ipaddresses")
        
        m.get(
            "http://mock/api/ipam/prefixes/?%s" % test_1["params"],
            json=test_1["response"],
        )
        m.get(
            "http://mock/api/ipam/ip-addresses/?%s" % test_2["params"],
            json=test_2["response"],
        )

        pool = NetboxIpPool(
            netbox="http://mock", site="test", role="loopback", family=4
        )

        self.assertEqual(str(pool.get(id=1)), "10.10.0.1/26")
        self.assertEqual(str(pool.get(id=1)), "10.10.0.1/26")
        self.assertEqual(pool.get(id=2), False) ## Already Reserved


def load_fixture(name):

    return yaml.load(open(here + "/" + FIXTURE_DIR + name + ".json"))
