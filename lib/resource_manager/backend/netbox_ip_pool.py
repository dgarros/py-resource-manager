import logging
import re
import yaml
import os
import inspect
import ipaddress
import requests

from collections import defaultdict

from resource_manager.pools.ipaddr_subnet import IpAddressPool
from resource_manager.backend.netbox_utils import query_netbox

logger = logging.getLogger("resource-manager")


class NetboxIpPool(object):
    def __init__(self, netbox, site, role, family, description=None, secure=True):
        """
        Inputs:
            netbox: Netbox Server Address http:1.2.3.4:4851
            site:
            role: 
            family:
            description:
        """

        if not secure:
            from requests.packages.urllib3.exceptions import InsecureRequestWarning
            requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

        self.nb = requests.session()
        self.nb_addr = netbox
        self.verify_certs = secure

        self.site_name = site
        self.role = role
        self.ip_family = family
        self.description = description

        self.identifier = None

        self.data = None

        self.subnets = []

        ### Define unique identifier for this pool
        if self.site_name and self.description:
            self.identifier = "%s/%s/%s/%s" % (
                self.site_name,
                self.role,
                self.description,
                self.ip_family,
            )
        elif not self.site_name and self.description:
            self.identifier = "%s/%s/%s" % (self.role, self.description, self.ip_family)
        elif self.site_name and not self.description:
            self.identifier = "%s/%s/%s" % (self.site_name, self.role, self.ip_family)
        else:
            self.identifier = "%s/%s" % (self.role, self.ip_family)

        self._get_info_from_netbox()

    def get(self, identifier=None, return_mask=True, id=None):
        """
        Find the next available IP in the pool
        Or if id is defined, get a specific IP in the pool
        """
        logger.debug("Will try to get an IP for %s" % identifier)

        ### If identifier is defined, 
        ### first check on all subnets if this identifier already has an Ip reserved
        ### if not, pick the next available Ips
        if identifier:
            for subnet in self.subnets:
                ip =  subnet.get(identifier=identifier, id=id, only_if_exist=True)

                if ip and return_mask:
                    return "%s/%s" % (ip, subnet.subnet.prefixlen)
                elif ip:
                    return ip

        for subnet in self.subnets:

            ip = subnet.get(identifier=identifier, id=id)

            if ip and return_mask:
                return "%s/%s" % (ip, subnet.subnet.prefixlen)
            elif ip:
                return ip

        return False

    def _get_info_from_netbox(self):

        logger.debug(
            "_get_info_from_netbox(), will query netbox for prefixes %s"
            % (self.identifier)
        )

        resp = self._get_list_prefix_from_netbox(
                                        site=self.site_name, 
                                        role=self.role, 
                                        family=self.ip_family, 
                                        status=1
                                    )

        if resp["count"] == 0:
            raise Exception(
                "Unable to find a prefix for %s in netbox" % (self.identifier)
            )

        for result in resp["results"]:
            if self.description and result["description"] != self.description:
                continue            
            self._add_prefix(result['prefix'])

        if self.subnets == []:
            raise Exception(
                "Unable to find a prefix for %s in netbox" % (self.identifier)
            )

        return True


    def _add_prefix(self, prefix):

        ### 
        pool = IpAddressPool(prefix)

        ### Get the list of existing IPs in Netbox
        resp = self._get_all_ips_per_prefix(prefix=prefix)

        logger.debug("Found %s ip(s) in Netbox for %s" % (len(resp["results"]), prefix))

        for ip in resp["results"]:
            if ip["status"]["label"] not in ["Active", "Reserved"]:
                continue

            identifier = None

            ## make sure we have a device and an interface assigned to this IP
            if isinstance(ip["interface"], dict):
                if "device" in ip["interface"].keys():
                    identifier = "{device}::{interface}".format(
                        device=ip["interface"]["device"]["name"],
                        interface=ip["interface"]["name"],
                    )

            pool.reserve(ip["address"], identifier=identifier)

        self.subnets.append(pool)

        return True


    def _get_all_ips_per_prefix(self, prefix):

        url = self.nb_addr + "/api/ipam/ip-addresses/"
        url_params = "parent=%s" % prefix.replace("/", "%2f")

        return query_netbox(
            req=self.nb, url=url, params=url_params, secure=self.verify_certs
        )

    def _get_list_prefix_from_netbox(self, role, site=None, family=4, status=1):

        url = self.nb_addr + "/api/ipam/prefixes/"

        url_params = None
        if site:
            url_params = "site=%s&role=%s&family=%s&status=%s" % (
                site,
                role,
                family,
                status,
            )
        else:
            url_params = "role=%s&family=%s&status=%s" % (role, family, status)

        return query_netbox(
            req=self.nb, url=url, params=url_params, secure=self.verify_certs
        )
