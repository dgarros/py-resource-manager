import ipaddress
import logging
from collections import defaultdict, OrderedDict

logger = logging.getLogger("prefixes")


class PrefixesPool(object):
    """
    Class to automatically manage Prefixes and help to carve out sub-prefixes
    """

    def __init__(self, network, sub_size, carve_only_from=None, log="warn"):

        if log.lower() == "debug":
            logger.setLevel(logging.DEBUG)
        elif log.lower() == "warn":
            logger.setLevel(logging.WARN)
        elif log.lower() == "error":
            loggersetLevel(logging.ERROR)
        else:
            logger.setLevel(logging.INFO)

        self.network = ipaddress.ip_network(network)
        self.sub_size = int(sub_size)

        ## check if sub_size is smaller than network size
        if self.sub_size <= self.network.prefixlen:
            raise Exception(
                "The size of the subnets need to be bigger than the size of the network provided"
            )

        self.size_delta = self.sub_size - self.network.prefixlen
        self.nbr_subnets = 2 ** self.size_delta
        self.nbr_subnets_available = self.nbr_subnets

        self.sub_by_key = OrderedDict()
        self.sub_by_id = OrderedDict()
        self.shard_size = 16

        if self.size_delta <= self.shard_size:
            self.nbr_shard = 1
            self.sub_by_key[str(self.network)] = None

        else:
            self.nbr_shard = 2 ** (self.size_delta - self.shard_size)
            shard_mask = self.network.prefixlen + self.size_delta - self.shard_size

            ## if the number of shard is too big, we'll only allocate the first 16384
            ## this is mainly for IPv6 and the probability to use all subnet is extremely small
            if self.nbr_shard < 16384:
                for shard in list(self.network.subnets(new_prefix=shard_mask)):
                    self.sub_by_key[str(shard)] = None

            else:
                tmp_network_mask = shard_mask - 14
                tmp_network_addr = "%s/%s" % (
                    str(self.network.network_address),
                    tmp_network_mask,
                )
                tmp_network = ipaddress.ip_network(tmp_network_addr)
                for shard in list(tmp_network.subnets(new_prefix=shard_mask)):
                    self.sub_by_key[str(shard)] = None

        logger.debug("Have created %s shard(s)" % self.nbr_shard)
        logger.debug("Got %s subnets available" % self.nbr_subnets_available)

    def _initialize_shard(self, shard_addr):
        """
        Initialize a shard 
        """

        ## Check if the shard is valid and if it has already been initialized
        if not shard_addr in self.sub_by_key.keys():
            return False

        if self.sub_by_key[shard_addr] != None:
            return False

        logger.debug("Will initialize shard %s" % shard_addr)

        shard = ipaddress.ip_network(shard_addr)
        subnet_list = list(shard.subnets(new_prefix=int(self.sub_size)))

        self.sub_by_key[shard_addr] = {
            "nbr_subnet_available": len(subnet_list),
            "subnets": OrderedDict(),
        }

        # Populate
        for sub in subnet_list:
            self.sub_by_key[shard_addr]["subnets"][str(sub)] = False

        return True

    def reserve(self, subnet, identifier=None):
        """
        Indicate that a specific subnet is already reserved/used
        """

        logger.debug("Will try to reserve > %s (id=%s)" % (subnet, identifier))

        ### TODO Add check to make sure the subnet provided has the right size
        sub = ipaddress.ip_network(subnet)

        if sub.prefixlen != self.sub_size:
            logger.debug("%s do not have the right size, SKIPPING" % (subnet))
            return False

        if not self.network.overlaps(sub):
            logger.debug("%s is not part of this network, SKIPPING" % (subnet))
            return False

        # TODO check earlier if identifier already has reserved something

        logger.debug("Shard list > %s" % (self.sub_by_key.keys()))

        ## Find the shard for this subnet
        for shard in self.sub_by_key.keys():
            shardnet = ipaddress.ip_network(shard)
            if not shardnet.overlaps(sub):
                logger.debug("%s is not part of this shard" % (subnet))
                continue

            if self.sub_by_key[shard] == None:
                self._initialize_shard(shard)

            if str(sub) not in self.sub_by_key[shard]["subnets"].keys():
                raise Exception(
                    "improbable situation, shard has not been initialized properly"
                )

            if self.sub_by_key[shard]["subnets"][str(sub)] != False:
                if (
                    identifier
                    and identifier == self.sub_by_key[shard]["subnets"][str(sub)]
                ):
                    logger.debug(
                        "%s already reserved with id > %s" % (subnet, identifier)
                    )
                    return True
                elif (
                    identifier
                    and identifier != self.sub_by_key[shard]["subnets"][str(sub)]
                ):
                    current_id = self.sub_by_key[shard]["subnets"][str(sub)]
                    logger.debug(
                        "%s already reserved with a different id > %s"
                        % (subnet, current_id)
                    )
                    return False

            elif identifier:
                self.sub_by_key[shard]["subnets"][str(sub)] = identifier
                self.sub_by_id[identifier] = str(sub)

                self.sub_by_key[shard]["nbr_subnet_available"] -= 1
                logger.debug("%s reserved with identifier > %s" % (subnet, identifier))

            else:
                self.sub_by_key[shard]["subnets"][str(sub)] = True
                self.sub_by_key[shard]["nbr_subnet_available"] -= 1
                logger.debug("%s reserved without identifier" % (subnet))

            return True

        # Couldn't find the subnet
        return False

    def get_subnet(self, identifier=None):
        """
        Return the next available Subnet

        Return a IpNetwork Object
        """

        if identifier and identifier in self.sub_by_id.keys():
            return ipaddress.ip_network(self.sub_by_id[identifier])

        for i, (key, shard) in enumerate(self.sub_by_key.items()):

            if shard == None:
                self._initialize_shard(key)

            if self.sub_by_key[key]["nbr_subnet_available"] == 0:
                continue

            for sub in self.sub_by_key[key]["subnets"].keys():
                if self.sub_by_key[key]["subnets"][sub] != False:
                    continue

                if identifier:
                    self.sub_by_key[key]["subnets"][sub] = identifier
                    self.sub_by_id[identifier] = sub
                    self.sub_by_key[key]["nbr_subnet_available"] -= 1

                else:
                    self.sub_by_key[key]["subnets"][sub] = True
                    self.sub_by_key[key]["nbr_subnet_available"] -= 1

                return ipaddress.ip_network(sub)

        # No more subnet available
        return False

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
