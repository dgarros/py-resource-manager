import logging
import re
import yaml
import os
import inspect
import requests
from collections import defaultdict

from resource_manager.pools.integer import IntegerPool
from resource_manager.backend.netbox_utils import query_netbox

logger = logging.getLogger("resource-manager")


class NetboxAsnPool(object):
    """
    Manage ASN Pool in Netbox
    ASN are stored per device, in a custom field > ASN
    """

    def __init__(
        self, netbox, name, scope, asn_range=[], custom_field="ASN", secure=True
    ):

        self.nb = netbox
        self.name = name

        ### Ensure Scope is dict and Range is a list of 2
        if not isinstance(asn_range, list):
            raise Exception("asn_range must be list, not %s" % type(asn_range))
        elif not isinstance(scope, list):
            raise Exception("scope must be a list, not %s" % type(scope))
        elif len(asn_range) != 2:
            raise Exception(
                "asn_range must be list of 2 items, not %s items" % len(asn_range)
            )

        for item in scope:
            if not isinstance(item, dict):
                raise Exception(
                    "scope must be a list of dictionnay, at least 1 item is a %s"
                    % type(item)
                )

        if not secure:
            from requests.packages.urllib3.exceptions import InsecureRequestWarning

            requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

        self.nb = requests.session()
        self.nb_addr = netbox
        self.verify_certs = secure

        ### Create the Integer Pool
        self.pool = IntegerPool(self.name, start=asn_range[0], end=asn_range[1])

        ### Query Netbox to find the devices in scope for this group
        url = self.nb_addr + "/api/dcim/devices/"
        url_params = "is_network_device=True"
        for item in scope:
            for key, value in item.items():
                url_params = url_params + "&%s=%s" % (key, value)

        resp = query_netbox(
            req=self.nb, url=url, params=url_params, secure=self.verify_certs
        )

        logger.debug("Found %s devices in scope" % resp["count"])

        ### Go over the list of devices and reserve the existing ASN
        for dev in resp["results"]:

            ## Check if the device has an ASN number define
            if not isinstance(dev["custom_fields"], dict):
                continue
            elif custom_field not in dev["custom_fields"].keys():
                continue
            elif dev["custom_fields"][custom_field] == None:
                continue

            self.pool.reserve(
                integer=dev["custom_fields"][custom_field], identifier=dev["name"]
            )

    def get(self, identifier=None):
        """
        Find the next available ASN in the pool
        """
        logger.debug("Will try to get an ASN for %s" % identifier)

        asn = self.pool.get(identifier=identifier)

        return asn
