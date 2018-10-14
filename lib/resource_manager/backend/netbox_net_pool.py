import logging
import re
import yaml
import os
import requests

from collections import defaultdict

from resource_manager.pools.ipaddr_subnet import IpAddressPool
from resource_manager.pools.ipaddr_prefixes import PrefixesPool

from resource_manager.backend.netbox_utils import query_netbox

logger = logging.getLogger("resource-manager")


class NetboxNetPool(object):
    def __init__(self, netbox, site, role, family, size, secure=True):

        if not secure:
            from requests.packages.urllib3.exceptions import InsecureRequestWarning

            requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

        self.nb = requests.session()
        self.nb_addr = netbox
        self.verify_certs = secure

        self.site_name = site
        self.role = role
        self.subnet_size = size
        self.ip_family = family

        self.data = None

        self.prefixes = []

        self.is_p2p_pool = False

        if size in [4, 6]:
            self.is_p2p_pool = True

        ## Get prefix from netbox based on Site and Role
        url = self.nb_addr + "/api/ipam/prefixes/"
        params = "site={site}&role={role}&family={family}&status={status}".format(
            site=self.site_name,
            role=self.role,
            family=str(self.ip_family),
            status=str(0),
        )

        resp = query_netbox(
            req=self.nb, url=url, params=params, secure=self.verify_certs
        )

        if resp["count"] == 0:
            raise Exception(
                "Unable to find the prefixe %s (v%s) for %s in netbox"
                % (self.role, self.ip_family, self.site_name)
            )

        self.data = resp["results"]

        ### Save all prefixes
        for p in self.data:
            prefix = PrefixesPool(p["prefix"], self.subnet_size)

            # Get the list of existing prefix in Netbox
            # And reserve them in the local object
            # TODO need to remove te mask_lenght limitation
            url = self.nb_addr + "/api/ipam/prefixes/"
            params = "site={site}&parent={parent}&family={family}&mask_length={mask_length}".format(
                site=self.site_name,
                parent=p["prefix"],
                family=str(self.ip_family),
                mask_length=int(self.subnet_size),
            )

            resp = query_netbox(
                req=self.nb, url=url, params=params, secure=self.verify_certs
            )

            logger.debug("Found %s prefixes in Netbox" % len(resp["results"]))

            for net in resp["results"]:
                if net["description"]:
                    prefix.reserve(net["prefix"], identifier=net["description"])
                else:
                    prefix.reserve(net["prefix"])

            self.prefixes.append(prefix)

    def get_parent_prefixes(self):
        """
        Return the list parent prefixes as ipaddress.ip_network obj for this net pool
        """
        parent_list = []
        for prefix in self.prefixes:
            parent_list.append(prefix.network)

        return parent_list

    def get_net(self, identifier=None):
        """
        reserve a new subnet
        """

        ### First check if this identifier already has a subnet assigned
        ### in one of the existing pool
        for prefix in self.prefixes:
            if prefix.check_if_already_allocated(identifier=identifier):
                return prefix.get_subnet(identifier=identifier)

        ### If Nothing was found previously, assign a new subnet
        for prefix in self.prefixes:
            new_prefix = prefix.get_subnet(identifier=identifier)
            if new_prefix:
                return new_prefix

        ### if nothing has been assigned and returned before, no more subnet are available
        return False

    ## This function propably should not live here

    # def get_net_ip(self, device=None, interface=None, ipid=1):
    #     """
    #     Reserve a new subnet and return an IP address
    #     """

    #     logger.debug("get_net_ip() device %s interface %s" % ( device, interface))

    #     label = None

    #     if device and interface and not self.is_p2p_pool:
    #         label = "%s::%s" % (device, interface)

    #     elif device and interface and self.is_p2p_pool:

    #         peers = []
    #         peers.append("%s::%s" % (device, interface))
    #         ints, ok = self.nb.request.dcim.dcim_interfaces_list(device=device, name=interface )

    #         if ok:
    #             if ints['count'] == 1:
    #                 int = ints['results'][0]

    #                 if isinstance(int['interface_connection'], dict):
    #                     peer_int = int['interface_connection']['interface']['name']
    #                     peer_dev = int['interface_connection']['interface']['device']['name']

    #                     peers.append("%s::%s" % (peer_dev, peer_int))
    #                     label = "<>".join(sorted(peers))
    #             else:
    #                 logger.debug("%s interface got returned from netbox, not supported" % (ints['count'] ))

    #             logger.debug("Something happened while trying to pull interface from Netbox > %s" % (ints))

    #     elif device:
    #         label = device

    #     subnet = self.get_net(identifier=label)

    #     # for prefix in self.prefixes:
    #     #     ## Check if there are some prefix available
    #     #     subnet = prefix.get_subnet(identifier=label)

    #     logger.debug("Got subnet for label > %s > %s" % ( label, str(subnet)))

    #     ### TODO should we store the subnet somewhere to reuse it later ??
    #     return "%s/%s" % (subnet[ipid], subnet.prefixlen)
