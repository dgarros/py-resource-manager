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

        # TODO check
        self.site_name = site
        self.role = role
        self.ip_family = family
        self.description = description

        self.identifier = None

        self.data = None

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

        ## Add support to define prefixe by IP address
        ## Get prefix from netbox based on Site and Role
        self._get_prefix()

        ### Save
        self.subnet = IpAddressPool(self.data["prefix"])

        ### Get the list of existing IPs in Netbox
        resp = self._get_all_ips_per_prefix(prefix=self.data["prefix"])

        logger.debug("Found %s ips in Netbox" % len(resp["results"]))

        for ip in resp["results"]:

            if ip["status"]["label"] not in ["Active", "Reserved"]:
                continue

            identifier = None

            ## make sure we have a device and an interface assigned to this IP
            if isinstance(ip["interface"], dict):
                if "device" in ip["interface"].keys():
                    identifier = "%s::%s" % (
                        ip["interface"]["device"]["name"],
                        ip["interface"]["name"],
                    )

            self.subnet.reserve(ip["address"], identifier=identifier)

    def get(self, identifier=None, return_mask=True):
        """
        Find the next available IP in the pool
        """
        logger.debug("Will try to get an IP for %s" % identifier)

        ip = self.subnet.get(identifier=identifier)

        if return_mask == True:
            return "%s/%s" % (ip, self.subnet.subnet.prefixlen)
        else:
            return ip

    def _get_prefix(self):

        logger.debug(
            "_get_prefix(), will query netbox for prefix %s %s"
            % (self.site_name, self.role)
        )

        resp = self._get_list_prefix_from_netbox(
            site=self.site_name, role=self.role, family=self.ip_family, status=1
        )

        if resp["count"] == 0:
            raise Exception(
                "Unable to find the prefixe %s in netbox" % (self.identifier)
            )
        elif resp["count"] > 1 and not self.description:
            raise Exception(
                "More than 1 prefixe returned for %s in netbox, only 1 is supported"
                % (self.identifier)
            )

        elif self.description:

            for result in resp["results"]:
                if result["description"] != self.description:
                    continue

                if result["description"] == self.description and self.data:
                    raise Exception(
                        "More than 1 prefixe returned for %s in netbox, only 1 is supported"
                        % (self.identifier)
                    )

                self.data = result

            if self.data == None:
                raise Exception(
                    "Unable to find the prefixe %s in netbox" % (self.identifier)
                )

        else:
            self.data = resp["results"][0]

        return True

    def _get_all_ips_per_prefix(self, prefix):

        url = self.nb_addr + "/api/ipam/ip-addresses/"
        url_params = "parent=%s" % prefix.replace("/", "%2f")

        return query_netbox(
            req=self.nb, url=url, params=url_params, secure=self.verify_certs
        )

    def get_prefix(self):

        logger.debug(
            "_get_prefix(), will query netbox for prefix %s %s"
            % (self.site_name, self.role)
        )

        resp = self._get_list_prefix_from_netbox(
            site=self.site_name, role=self.role, family=self.ip_family, status=1
        )

        if resp["count"] == 0:
            raise Exception(
                "Unable to find the prefixe %s in netbox" % (self.identifier)
            )
        elif resp["count"] > 1 and not self.description:
            raise Exception(
                "More than 1 prefixe returned for %s in netbox, only 1 is supported"
                % (self.identifier)
            )

        elif self.description:

            for result in resp["results"]:
                if result["description"] != self.description:
                    continue

                if result["description"] == self.description and self.data:
                    raise Exception(
                        "More than 1 prefixe returned for %s in netbox, only 1 is supported"
                        % (self.identifier)
                    )

                self.data = result

            if self.data == None:
                raise Exception(
                    "Unable to find the prefixe %s in netbox" % (self.identifier)
                )

        else:
            self.data = resp["results"][0]

        return True

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
