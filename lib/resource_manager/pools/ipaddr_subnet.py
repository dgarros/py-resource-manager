import ipaddress

#TODO add logging

class IpAddressPool(object):
    """
    This class manage the ip address allocation in a subnet
    Each IP allocated can be saved with a label to define its identifier
    If the same ownder request an IP multiple time, the same IP will be returned

    The IPs are store with in a dict with a key that represent the ID of the IP in the subnet
    """

    def __init__(self, subnet):
        self.subnet = ipaddress.ip_network(subnet)
        self.num_addresses = self.subnet.num_addresses
        self.nwk_int = int(self.subnet[0])
        self.padding = '{:0%s}' % len(str(self.num_addresses))
        self.ips_by_id = {}
        self.ips_by_identifier = {}

    def get(self, identifier=None):
        """
        Get an IP from the Subnet
        Return the next one if no Ip are already associated with this label
        Return the IP previously allocated if one already exist
        """

        ### If an identifier is provided, check if an IP was already allocated
        if identifier and identifier in self.ips_by_identifier.keys():
            id = int(self.ips_by_identifier[identifier])
            return self.subnet[id]

        ### If no IP were allocated, pick the next one
        for id in range(1, self.num_addresses):
            id2str = self.padding.format(id)

            if id2str in self.ips_by_id.keys():
                continue
            
            if identifier:
                self.ips_by_id[id2str] = identifier
                self.ips_by_identifier[identifier] = id2str
            else:
                self.ips_by_id[id2str] = True

            return self.subnet[id]

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
        

