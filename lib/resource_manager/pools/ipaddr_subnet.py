import ipaddress
import logging

logger = logging.getLogger("resource-manager")


class IpAddressPool(object):
    """
    This class manage the ip address allocation in a subnet
    Each IP allocated can be saved with a label to define its identifier
    If the same owner request an IP multiple time, the same IP will be returned

    The IPs are store with in a dict with a key that represent the ID of the IP in the subnet
    """

    def __init__(self, subnet):
        self.subnet = ipaddress.ip_network(subnet)

        if (self.subnet.version == 4 and self.subnet.prefixlen == 31) or (
            self.subnet.version == 6 and self.subnet.prefixlen == 127
        ):
            self.num_addresses = self.subnet.num_addresses
        else:
            self.num_addresses = self.subnet.num_addresses - 2

        self.nwk_int = int(self.subnet[0])
        self.padding = "{:0%s}" % (len(str(1000)) + 1)
        self.ips_by_id = {}
        self.ips_by_identifier = {}

    def get(self, identifier=None, id=None, only_if_exist=False):
        """
        Get an IP from the Subnet
        Return the next one if no Ip is already associated with this label
        If Id is provided, reserve and return the appropriate Id
        Return the IP previously allocated if one already exist
        if only_if_exist is defined, 
            a new IP will not be created but it will return an existing IP associated with the identifier
        """

        ### If an identifier is provided, check if an IP was already allocated
        if identifier and identifier in self.ips_by_identifier.keys():
            ip_id = int(self.ips_by_identifier[identifier])

            ##TODO When Id is provided, Add logic to check if previously
            ## reserved IP matches the ID
            if id and id != ip_id:
                logger.warning(
                    "There is already an IP reserved for the identifier %s, can't provided Ip id %s as requested"
                    % (identifier, id)
                )

            return self.subnet[ip_id]

        if only_if_exist:
            return False

        ### If id is provided, pick this IP
        if id:
            id2str = self.padding.format(id)

            ## Check if this IP is already reserved with an Identifier
            if id2str in self.ips_by_id.keys() and isinstance(
                self.ips_by_id[id2str], str
            ):
                if identifier and self.ips_by_id[id2str] == identifier:
                    return self.subnet[id]

                elif identifier and self.ips_by_id[id2str] != identifier:
                    logger.warning(
                        "The Ip with id %s is already reserved under a different Identifier (%s / %s) "
                        % (id, identifier, self.ips_by_id[id2str])
                    )
                    return False
                elif not identifier:
                    logger.warning(
                        "The Ip with id %s is already reserved with the Identifier (%s) "
                        % (id, self.ips_by_id[id2str])
                    )
                    return False

            if identifier:
                self.ips_by_id[id2str] = identifier
                self.ips_by_identifier[identifier] = id2str
            else:
                self.ips_by_id[id2str] = True

            return self.subnet[id]

        ### If no IP were allocated, pick the next one
        for ip_id in range(1, self.num_addresses + 1):
            id2str = self.padding.format(ip_id)

            if id2str in self.ips_by_id.keys():
                continue

            if identifier:
                self.ips_by_id[id2str] = identifier
                self.ips_by_identifier[identifier] = id2str
            else:
                self.ips_by_id[id2str] = True

            return self.subnet[ip_id]

    def reserve(self, ip_address, identifier=None):
        """
        Indicate that an Ip address is already reserved
        Optionnaly indicate the identifier of this address
        """

        # TODO Check if the ip is provided with or without subnet info

        ip = ipaddress.ip_interface(ip_address)
        ip_nbr = int(ip)
        ip_diff = ip_nbr - self.nwk_int
        ip_id = self.padding.format(ip_diff)

        if identifier:
            self.ips_by_id[ip_id] = identifier
            self.ips_by_identifier[identifier] = ip_id
        else:
            self.ips_by_id[ip_id] = True

        return True
