import unittest
import requests_mock
import yaml
import pytest
from os import path

from resource_manager.backend.netbox_asn_manager import NetboxAsnManager

here = path.abspath(path.dirname(__file__))

FIXTURE_DIR = "fixtures/"

VALID_CONFIG_1 = {
    'netbox': {
        'address': 'http://mock'
    }
}

VALID_CONFIG_2 = {
    'netbox': {
        'address': 'http://mock'
    },
    'netbox_asn': {
        'custom_field_name': 'newname'
    }
}

class Test_NetboxAsnManager(unittest.TestCase):

    def test_init_not_valid(self):

        with pytest.raises(Exception) as e_info:
            asnManager = NetboxAsnManager(
                config={}, 
            )

    def test_init_valid(self):
        asn_manager = NetboxAsnManager(config=VALID_CONFIG_1)
        self.assertTrue(1)

    def test_init_custom_field(self):

        asn_manager = NetboxAsnManager(config=VALID_CONFIG_2)
        self.assertEqual(asn_manager.netbox_custom_field_name, 'newname')
  
    @requests_mock.mock()
    def test_basic(self, m):

        test02_1 = load_fixture("test02_1_dcim_devices")
        m.get(
            "http://mock/api/dcim/devices/?%s" % test02_1["params"],
            json=test02_1["response"],
        )

        asn_manager = NetboxAsnManager(config=VALID_CONFIG_1)
        asn_manager.add_pool_specification(name='test_range', spec={
            'scope': [{"site": "test"}],
            'range': [65001, 65100]
        })

        self.assertEqual(asn_manager.resolve(var_type='ASN', var_params="test_range"), 65003)
        self.assertEqual(asn_manager.resolve(var_type='ASN', var_params="test_range", identifier="device1"), 65001)
        self.assertEqual(asn_manager.resolve(var_type='ASN', var_params="test_range", identifier="device10"), 65010)


def load_fixture(name):
    return yaml.load(open(here + "/" + FIXTURE_DIR + name + ".json"))
