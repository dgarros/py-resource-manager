import unittest
import requests_mock
import yaml
from os import path

from resource_manager.backend.netbox_net_pool import NetboxNetPool

here = path.abspath(path.dirname(__file__))

FIXTURE_DIR = "fixtures/"


class Test_NetboxNetPool(unittest.TestCase):
    @requests_mock.mock()
    def test_01(self, m):

        test01_1 = load_fixture("test01_1_ipam_prefixes")
        test01_2 = load_fixture("test01_2_ipam_prefixes")
        m.get(
            "http://mock/api/ipam/prefixes/?%s" % test01_1["params"],
            json=test01_1["response"],
        )
        m.get(
            "http://mock/api/ipam/prefixes/?%s" % test01_2["params"],
            json=test01_2["response"],
        )

        pool = NetboxNetPool(
            netbox="http://mock", site="test", role="loopback", family=4
        )

        self.assertEqual(str(pool.get(size=26)), "10.10.0.64/26")
        self.assertEqual(str(pool.get(size=26, identifier="first")), "10.10.0.0/26")
        self.assertEqual(str(pool.get(size=26, identifier="first")), "10.10.0.0/26")
        self.assertEqual(str(pool.get(size=26, identifier="fourth")), "10.10.0.192/26")

    @requests_mock.mock()
    def test_03_no_site(self, m):

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

        pool = NetboxNetPool(
            netbox="http://mock", role="loopback", family=4
        )

        self.assertEqual(str(pool.get(size=26)), "10.10.0.64/26")
        self.assertEqual(str(pool.get(size=26, identifier="first")), "10.10.0.0/26")
        self.assertEqual(str(pool.get(size=26, identifier="first")), "10.10.0.0/26")
        self.assertEqual(str(pool.get(size=26, identifier="fourth")), "10.10.0.192/26")
        self.assertEqual(str(pool.get(size=24, identifier="fifth")), "10.10.1.0/24")

def load_fixture(name):

    return yaml.load(open(here + "/" + FIXTURE_DIR + name + ".json"))
