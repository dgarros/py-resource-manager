import logging
from resource_manager.backend.netbox_net_pool import NetboxNetPool

logger = logging.getLogger("resource-manager")


class NetboxNetManager(object):
    def __init__(self, config):

        self.__supported_types = ["NET4", "NET6"]
        self.mandatory_config_sections = ["netbox"]

        self.net_pools = {}

        for section in self.mandatory_config_sections:
            if section not in config.keys():
                raise Exception("Configuration must have a %s section" % section)

        self.netbox_addr = config["netbox"]["address"]

        if "secure" in config["netbox"]:
            self.netbox_secure = config["netbox"]["secure"]
        else:
            self.netbox_secure = True

    def supported_types(self):
        return self.__supported_types

    def resolve(self, var_type, var_params, identifier=None):

        if var_type.upper() not in self.__supported_types:
            logger.warn(
                "type {type} not supported for {my_class}".format(
                    type=var_type, my_class=type(self).__name__
                )
            )
            return False

        if not var_params:
            return False

        (pool_identifier, params) = self.parse_params(var_params)

        if "4" in var_type:
            params["family"] = 4
        elif "6" in var_type:
            params["family"] = 6
        else:
            params["family"] = None

        if pool_identifier not in self.net_pools.keys():
            try:
                self.net_pools[pool_identifier] = NetboxNetPool(
                    netbox=self.netbox_addr,
                    role=params["role"],
                    site=params["site"],
                    family=params["family"],
                    secure=self.netbox_secure,
                )

            except Exception as err:
                logger.warn(
                    "Something went wrong while creating the NetboxNetPool for %s > %s"
                    % (pool_identifier, err)
                )
                return False

        next_net = self.net_pools[pool_identifier].get(
            size=params["size"], identifier=identifier
        )

        return next_net

    def parse_params(self, params):
        """
        args 
            params (str)

        return
            identifier (str)
            parser params (dict)
        """
        ## TODO we need to find a better and more scalable way to parse the params

        params_list = params.split("/")

        tmp = {"site": None, "role": None, "size": None}

        if len(params_list) == 2:
            ## We expect
            ##  - first item to be a role
            ##  - second item to be the size of the subnet
            tmp["role"] = params_list[0]
            tmp["size"] = int(params_list[1])

            return (params, tmp)

        elif len(params_list) == 3:
            ## We expect
            ##  - first item to be a site
            ##  - second item to be a role
            ##  - third item to be the size of the subnet
            tmp["site"] = params_list[0]
            tmp["role"] = params_list[1]
            tmp["size"] = int(params_list[2])

            return (params, tmp)

        else:
            return (False, None)
