
import logging
import re
import yaml
import os
import inspect
import ipaddress
import requests

from collections import defaultdict

from resource_manager.pools.ipaddr_subnet import IpAddressPool

logger = logging.getLogger( 'resource-manager' )

class NetboxIpPool(object):

    def __init__(self, netbox, site, role, family, description=None, log='debug', secure=True):
        """
        Inputs:
            netbox: Netbox Server Address http:1.2.3.4:4851
            site:
            role: 
            family:
            description:

        """

        if log.lower() == 'debug':
            logger.setLevel(logging.DEBUG)
        elif log.lower() == 'warn':
            logger.setLevel(logging.WARN)
        elif log.lower() == 'error':
            logger.setLevel(logging.ERROR)
        else:
            logger.setLevel(logging.INFO)

        if not secure:
            from requests.packages.urllib3.exceptions import InsecureRequestWarning
            requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

        self.nb = netbox
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
            self.identifier  = "%s/%s/%s/%s" %( self.site_name, self.role, self.description, self.ip_family)
        elif not self.site_name and self.description:
            self.identifier  = "%s/%s/%s" %( self.role, self.description, self.ip_family)
        elif self.site_name and not self.description:
            self.identifier  = "%s/%s/%s" %( self.site_name, self.role, self.ip_family)
        else:
            self.identifier  = "%s/%s" %( self.role, self.ip_family)
            
        
        ## Add support to define prefixe by IP address
        ## Get prefix from netbox based on Site and Role
        self._get_prefix()
    

        ### Save 
        self.subnet = IpAddressPool(self.data['prefix'])

        ### Get the list of existing IPs in Netbox
        resp = self._get_all_ips_per_prefix(prefix=self.data['prefix'])

        logger.debug("Found %s ips in Netbox" % len(resp['results']) ) 

        for ip in resp['results']:
            
            if ip['status']['label'] not in [ 'Active', 'Reserved' ]: 
                continue

            identifier = None

            ## make sure we have a device and an interface assigned to this IP
            if isinstance(ip['interface'], dict):
                if 'device' in ip['interface'].keys():
                    identifier = "%s::%s" % (ip['interface']['device']['name'], ip['interface']['name'])

            self.subnet.reserve(ip['address'], identifier=identifier)
         

    def get(self, identifier=None, return_mask=True):
        """
        Find the next available IP in the pool
        """
        logger.debug("Will try to get an IP for %s" % identifier ) 

        ip = self.subnet.get(identifier=identifier)

        if return_mask == True:
            return "%s/%s" % (ip, self.subnet.subnet.prefixlen)
        else: 
            return ip

    def _get_prefix(self):

        logger.debug("_get_prefix(), will query netbox for prefix %s %s" % (self.site_name, self.role) )

        resp = self._get_list_prefix_from_netbox(site=self.site_name,
                                                 role=self.role, 
                                                 family=self.ip_family,
                                                 status=1 )

        if resp['count'] == 0: 
            raise Exception("Unable to find the prefixe %s in netbox" % (self.identifier))
        elif resp['count'] > 1 and not self.description: 
            raise Exception("More than 1 prefixe returned for %s in netbox, only 1 is supported" % (self.identifier))

        elif self.description:  

            for result in resp['results']:
                if result['description'] != self.description:
                    continue

                if result['description'] == self.description and self.data:
                    raise Exception("More than 1 prefixe returned for %s in netbox, only 1 is supported" % (self.identifier))

                self.data = result
            
            if self.data == None:
                raise Exception("Unable to find the prefixe %s in netbox" % (self.identifier))

        else:
            self.data = resp['results'][0]
        
        return True

    def _get_all_ips_per_prefix(self, prefix):

        offset = 0
        keep_querying = True
        netbox_batch_size = 500

        url = self.nb_addr + '/api/ipam/ip-addresses/'
        
        results = {
            'count': 0,
            'results': []
        }

        while keep_querying:

            api_url_params = "offset=%s&limit=%s&parent=%s" % (offset, netbox_batch_size, prefix.replace('/', "%2f"))

            resp = self.nb.get(url, 
                                    params=api_url_params, 
                                    verify=self.verify_certs )

            resp.raise_for_status()

            resp_dict = resp.json()

            # TODO check for response code
            results['count'] = resp_dict['count']
            results['results'].extend(resp_dict['results'])

            offset += netbox_batch_size
            if int(resp_dict['count']) < offset:
                keep_querying = False

        return results
    
    def get_prefix(self):

        logger.debug("_get_prefix(), will query netbox for prefix %s %s" % (self.site_name, self.role) )

        resp = self._get_list_prefix_from_netbox(site=self.site_name,
                                                 role=self.role, 
                                                 family=self.ip_family,
                                                 status=1 )

        if resp['count'] == 0: 
            raise Exception("Unable to find the prefixe %s in netbox" % (self.identifier))
        elif resp['count'] > 1 and not self.description: 
            raise Exception("More than 1 prefixe returned for %s in netbox, only 1 is supported" % (self.identifier))

        elif self.description:  

            for result in resp['results']:
                if result['description'] != self.description:
                    continue

                if result['description'] == self.description and self.data:
                    raise Exception("More than 1 prefixe returned for %s in netbox, only 1 is supported" % (self.identifier))

                self.data = result
            
            if self.data == None:
                raise Exception("Unable to find the prefixe %s in netbox" % (self.identifier))

        else:
            self.data = resp['results'][0]
        
        return True

    def _get_list_prefix_from_netbox(self, role, site=None, family=4, status=1):

        offset = 0
        keep_querying = True
        netbox_batch_size = 500

        url = self.nb_addr + '/api/ipam/prefixes/'
        
        logger.debug("_get_list_prefix_from_netbox(), url %s" % (url) )
        
        results = {
            'count': 0,
            'results': []
        }

        params = None
        if site:
            params = "site=%s&role=%s&family=%s&status=%s" % (site, role, family, status)
        else:
            params = "role=%s&family=%s&status=%s" % (role, family, status)

        while keep_querying:

            paging_params = "offset=%s&limit=%s" % (offset, netbox_batch_size)

            api_url_params = paging_params + '&' + params

            logger.debug("_get_list_prefix_from_netbox(), querying > %s %s" % (url, api_url_params) )    

            resp = self.nb.get(url, 
                            params=api_url_params, 
                            verify=self.verify_certs )

            resp.raise_for_status()

            resp_dict = resp.json()

            # TODO check for response code
            results['count'] = resp_dict['count']
            results['results'].extend(resp_dict['results'])

            offset += netbox_batch_size
            if int(resp_dict['count']) < offset:
                keep_querying = False

        return results
