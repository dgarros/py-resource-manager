import ipaddress
import logging
from collections import defaultdict, OrderedDict

logger = logging.getLogger("prefixes")

class PrefixesPool(object):
    """
    Class to automatically manage Prefixes and help to carve out sub-prefixes
    """

    def __init__(self, network, carve_only_from=None):

        self.network = ipaddress.ip_network(network)

        ## Define biggest and smallest possible masks
        self.mask_biggest = self.network.prefixlen + 1
        if self.network.version == 4:
            self.mask_smallest = 32
        else:
            self.mask_smallest = 128

        self.available_subnets = defaultdict(list)
        self.sub_by_key = OrderedDict()
        self.sub_by_id = OrderedDict()

        ## Save the top level available subnet
        for subnet in list(self.network.subnets(new_prefix=self.mask_biggest)):
            self.available_subnets[self.mask_biggest].append(str(subnet))
        
    def reserve(self, subnet, identifier=None):
        """
        Indicate that a specific subnet is already reserved/used
        """

        logger.debug("Will try to reserve > %s (id=%s)" % (subnet, identifier))

        ### TODO Add check to make sure the subnet provided has the right size
        sub = ipaddress.ip_network(subnet)

        if int(sub.prefixlen) <= int(self.network.prefixlen):
            logger.debug("%s do not have the right size (%s,%s), SKIPPING" % (
                subnet, sub.prefixlen, self.network.prefixlen
            ))
            return False

        if sub.supernet(new_prefix=self.network.prefixlen) != self.network:
            logger.debug("%s is not part of this network, SKIPPING" % (subnet))
            return False

        ## Check first if this ID as already done a reservation
        if identifier and identifier in self.sub_by_id.keys():
            if self.sub_by_id[identifier] == str(sub):
                logger.debug("This identifier (%s) already has an active reservation for %s" %
                    (identifier, subnet)
                )
                return True
            else:
                logger.warn("this identifier (%s) is already used but for a different resource (%s)" % 
                    (identifier,  self.sub_by_id[identifier])
                )
                return False

        elif identifier and str(sub) in self.sub_by_key.keys():
            logger.warn("this subnet is already reserved but not with this identifier (%s)" % 
                    (identifier)
                )
            return False 

        elif str(sub) in self.sub_by_key.keys():
            self.remove_subnet_from_available_list(sub)
            return True

        logger.debug("No previous reservation found for (%s)" % subnet) 

        ## Check if the subnet itself is available
        ## if available reserve and return
        if subnet in self.available_subnets[sub.prefixlen]:
            if identifier:
                self.sub_by_id[identifier] = subnet
                self.sub_by_key[subnet] = identifier
            else:
                self.sub_by_key[subnet] = None

            self.remove_subnet_from_available_list(sub)
            return True

        logger.debug("the subnet (%s) is not already available, will need to split a bigger one " % str(subnet)) 

        ## If not reserved already, check if the subnet is available
        ## start at sublen and check all available subnet
        ### increase 1 by 1 until we find the closer supernet available
        ### break it down and keep track of the other available subnets 

        for sublen in range(sub.prefixlen-1, self.network.prefixlen, -1):
            supernet = sub.supernet(new_prefix=sublen)
            if str(supernet) in self.available_subnets[sublen]:
                self.split_supernet(supernet, sub)
                return self.reserve(subnet, identifier=identifier)
            

    def get_subnet(self, size, identifier=None):
        """
        Return the next available Subnet
        Return a IpNetwork Object
        """

        if identifier and identifier in self.sub_by_id.keys():
            net = ipaddress.ip_network(self.sub_by_id[identifier])
            if net.prefixlen == size:
                return net 
            else: 
                return False

        logger.debug("Nothing found, will allocate a new /%s Subnet" % size)
        if len(self.available_subnets[size]) != 0:
            sub = self.available_subnets[size][0]
            self.reserve(subnet=sub, identifier=identifier)
            return ipaddress.ip_network(sub)

        logger.debug("No /%s available, will create one" % size)
        ## if a subnet of this size is not available
        ## we need to find the closest subnet available and split it
        for i in range(size-1, self.mask_biggest-1, -1):
            
            if len(self.available_subnets[i]) != 0:
                supernet = ipaddress.ip_network(self.available_subnets[i][0])
                logger.debug("%s available, will split it" % str(supernet))
                subs = supernet.subnets(new_prefix=size)
                sub = next(subs)
                self.split_supernet(supernet, sub)
                self.reserve(subnet=str(sub), identifier=identifier)
                return sub
            else:
                logger.debug("No /%s available, will continue searching" % i)
                
        # No more subnet available
        return False

    def get_nbr_available_subnets(self):

        tmp = {}
        for i in range(self.mask_biggest, self.mask_smallest+1):
            tmp[i] = len(self.available_subnets[i])

        return tmp


    def check_if_already_allocated(self, identifier=None):
        """
        Check if a subnet has already been allocated based on an identifier

        Need to add the same capability based on Network address

        If both identifier and subnet are provided, identifier take precedence

        return True/False
        """
        if identifier and identifier in self.sub_by_id.keys():
            return True
        elif identifier and identifier not in self.sub_by_id.keys():
            return False


    def split_supernet(self, supernet, subnet):
        """
        Split a supernet into smaller networks

        args
            supernet (ipnetwork)
            subnet (ipnetwork)
        """

        ### TODO ensure subnet is small than supernet
        ### TODO ensure that subnet is part of supernet
        logger.debug("will create %s out of %s " % (str(subnet), str(supernet)))

        parent_net = supernet
        for i in range(supernet.prefixlen+1, subnet.prefixlen+1):

            tmp_net = list(parent_net.subnets(new_prefix=i))

            if i == subnet.prefixlen:
                for net in tmp_net:
                    logger.debug("Add %s into list of available subnet" % str(net))
                    self.available_subnets[i].append(str(net))
            else:
                if subnet.subnet_of(tmp_net[0]):
                    parent = 0
                    other = 1
                else:
                    parent = 1
                    other = 0
                
                parent_net = tmp_net[parent]
                logger.debug("Add %s into list of available subnet" % str(tmp_net[other]))
                self.available_subnets[i].append(str(tmp_net[other]))

        self.remove_subnet_from_available_list(supernet)
        return True

    def remove_subnet_from_available_list(self, subnet):
        """
        Remove a subnet from the list of available Subnet
        
        args:
            subnet (ipnetwork)
        """

        ## todo check if subnet is an IP network object

        try:
            idx = self.available_subnets[subnet.prefixlen].index(str(subnet))
            
            # if idx:
            logger.debug("Subnet %s is not available anymore" % str(subnet))
            del self.available_subnets[subnet.prefixlen][idx]
            return True
        except:
            logger.warn("Unable to remove %s from list of available subnets" % str(subnet))
            return False



