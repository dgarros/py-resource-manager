import unittest
import requests_mock
import yaml
import pytest
from os import path

from resource_manager.backend.netbox_asn_pool import NetboxAsnPool

here = path.abspath(path.dirname(__file__))

FIXTURE_DIR = 'fixtures/'

class Test_NetboxAsnPool(unittest.TestCase):

    @requests_mock.mock() 
    def test_init(self, m):

        test02_1 = load_fixture('test02_1_dcim_devices')
        m.get('http://mock/api/dcim/devices/?%s' % test02_1['params'], json=test02_1['response'])

        with pytest.raises(Exception) as e_info:
            pool = NetboxAsnPool(
                        netbox='http://mock',
                        name='test_range',
                        asn_range = [65001, 65100]
                    )
            
        with pytest.raises(Exception) as e_info:
            pool = NetboxAsnPool(
                        netbox='http://mock',
                        name='test_range',
                        scope=[ {'site': 'test'} ],
                    )

        with pytest.raises(Exception) as e_info:
            pool = NetboxAsnPool(
                        netbox='http://mock',
                        name='test_range',
                        scope=[ {'site': 'test'} ],
                        asn_range = [65001, 65100, 1234]
                    )

        with pytest.raises(Exception) as e_info:
            pool = NetboxAsnPool(
                        netbox='http://mock',
                        name='test_range',
                        scope=[ {'site': 'test'} ],
                        asn_range = [1234]
                    )

        with pytest.raises(Exception) as e_info:
            pool = NetboxAsnPool(
                        netbox='http://mock',
                        scope=[ {'site': 'test'} ],
                        asn_range = [65001, 65100]
                    )

        pool = NetboxAsnPool(
                        netbox='http://mock',
                        name='test_range',
                        scope=[ {'site': 'test'} ],
                        asn_range = [65001, 65100]
                    )
        

    @requests_mock.mock()    
    def test_basic(self, m):

        test02_1 = load_fixture('test02_1_dcim_devices')
        m.get('http://mock/api/dcim/devices/?%s' % test02_1['params'], json=test02_1['response'])
       
        pool = NetboxAsnPool(
                    netbox='http://mock',
                    name='test_range',
                    scope=[ {'site': 'test'} ],
                    asn_range = [65001, 65100]
                )
        
        self.assertEqual(pool.get(), 65003)
        self.assertEqual(pool.get(identifier='device1'), 65001)
        self.assertEqual(pool.get(identifier='device10'),65010)


    @requests_mock.mock()    
    def test_user_defined_custom_field(self, m):

        test03_1 = load_fixture('test03_1_dcim_devices')
        m.get('http://mock/api/dcim/devices/?%s' % test03_1['params'], json=test03_1['response'])
       
        pool = NetboxAsnPool(
                    netbox='http://mock',
                    name='test_range',
                    scope=[ {'site': 'test'} ],
                    asn_range = [65001, 65100],
                    custom_field='random_name'
                )
        
        self.assertEqual(pool.get(), 65003)
        self.assertEqual(pool.get(identifier='device1'), 65001)
        self.assertEqual(pool.get(identifier='device10'),65010)
        

def load_fixture(name):
    
    return yaml.load(open(here + '/' + FIXTURE_DIR + name + '.json'))