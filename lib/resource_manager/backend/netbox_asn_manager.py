
import logging
from resource_manager.backend.netbox_asn_pool import NetboxAsnPool

logger = logging.getLogger("resource-manager")

class NetboxAsnManager(object):

    def __init__(self, config):
        
        self.__supported_types = ['ASN']
        self.mandatory_config_sections = ['netbox']
        self.asn_pools = {}
        self.asn_pools_spec = {}

        for section in self.mandatory_config_sections:
            if section not in config.keys():
                raise Exception('Configuration must have a %s section' % section)

        self.netbox_addr = config['netbox']['address']
        self.netbox_custom_field_name = "ASN"

        ## Extract optional config parameters from the configuration if present
        if 'netbox_asn' in config:
            if 'custom_field_name' in config['netbox_asn']:
                self.netbox_custom_field_name =  config['netbox_asn']['custom_field_name']


    def import_pools_spec_from_file(self, spec_file):

        ## Open input file
        logger.debug('Opening input file %s' % (spec_file))
        asn_pools_spec = yaml.load(open(spec_file))

        for pool in asn_pools_spec:
            self.add_pool_specification(name=pool, spec=asn_pools_spec[pool])
        
        return True


    def add_pool_specification(self, name, spec):

        if name in self.asn_pools_spec.keys():
            ## Pool already presen
            ## TODO check if the spec are the same
            return True

        ## Ensure the information provided are valid
        ##  Scope is a list of dict and Range is a list of 2
        if 'range' not in spec.keys():
            logger.debug("range is mandatory in pool definition file for %s" % name)
            return False
        elif not isinstance(spec['range'], list):
            logger.debug("range must be a list in pool definition file for %s" % name)
            return False
        elif len(spec['range']) != 2:
            logger.debug("range must be a list of 2 members in pool definition file for %s" % name)
            return False  

        if 'scope' not in spec.keys():
            logger.debug("scope is mandatory in pool definition file for %s" % name)
            return False
        elif not isinstance(spec['scope'], list):
            logger.debug("scope must be a list in pool definition file for %s" % name)
            return False
        
        for item in spec['scope']:
            if not isinstance(item, dict):
                logger.debug("scope must be a list of dictionnay, at least 1 item of %s is a %s"
                    % (name, type(item)))
                return False

        self.asn_pools_spec[name] = spec

        return True


    def supported_types(self):
        return self.__supported_types


    def resolve(self, var_type, var_params, identifier=None):

        if var_type.upper() not in self.__supported_types:
            logger.warn("type %s not supported for NetboxAsnManager" % var_type)
            return False

        if var_params not in self.asn_pools_spec.keys():
            logger.warn("No specification defined for ASN pool %s" % var_params)
            return False

        if not var_params:
            return False

        if var_params not in self.asn_pools.keys():
            try:

                self.asn_pools[var_params] = NetboxAsnPool(
                    netbox=self.netbox_addr, 
                    name=var_params,
                    scope=self.asn_pools_spec[var_params]['scope'],
                    asn_range=self.asn_pools_spec[var_params]['range'],
                    custom_field=self.netbox_custom_field_name
                )

            except Exception as err:
                logger.warn(
                    "Something went wrong while creating the NetboxAsnPool for %s > %s"
                    % (var_params, err)
                )
                return False

        next_asn = self.asn_pools[var_params].get(identifier=identifier)
        return next_asn

    
