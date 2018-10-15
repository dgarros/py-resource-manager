import re
import logging
import os
import inspect
from collections import defaultdict, OrderedDict

### -------------------------------------------------------
### Support Function
### -------------------------------------------------------
def expand_list(int_list):
    """
    Take a list of string as input and return a list with all individual item

    int_list = [ 'et-[0-1]/0/0' ]  > [ 'et-0/0/0', 'et-1/0/0']
    """

    ints = []

    for item in int_list:

        range_list = []
        sub_int = None

        try:
            # Try if there is a range in the interface name
            # if there is one, expand the range to a list of integer
            range_str = re.search(r"\[([0-9\-\,]+)\]", item).group(1)
            range_list = expand_range(range_str)

            # extract the substring before and after the range
            sub_int = re.split(r"\[[0-9\-\,]+\]", item, 1)

        except AttributeError:
            pass

        if sub_int is None:
            # if nothing just add interface to list
            ints.append(item)
        else:
            for i in range_list:
                new_int = "%s%s%s" % (sub_int[0], i, sub_int[1])
                new_int_list = expand_list([new_int])
                ints.extend(new_int_list)

    return ints


def expand_range(str_range):
    """ 
    Take a range defined as a string in input and return a list of integer

    input: 
        string

    return:
        List of Integer

    0-1,3   > [0,1,3]
    0-1,3-6 > [0,1,3,4,5,6]
    0-1,6,7,10 > [0,1,6,7,10]
    """
    out = sum(
        (
            (
                list(range(*[int(j) + k for k, j in enumerate(i.split("-"))]))
                if "-" in i
                else [int(i)]
            )
            for i in str_range.split(",")
        ),
        [],
    )

    return out


### -------------------------------------------------------
### Main Class
### -------------------------------------------------------
# class DeviceInterfacePool(object):

#     def __init__(self, netbox, name, log='debug'):

#         # Get
#         self.nb = netbox
#         self.name = name
#         self.data = None
#         self.int_spec = {}

#         self.int_by_name = defaultdict(dict)
#         self.int_by_owner = {}

#         self.int_type = 'interface'

#         ## Get device from netbox
#         resp, ok = self.nb.request.dcim.dcim_devices_list(name=self.name)
#         if not ok:
#             raise Exception("An issue happened while trying to get device %s in netbox" % self.name)
#         elif resp['count'] == 0:
#             raise Exception("Unable to find %s in netbox" % self.name)

#         self.data = resp['results'][0]

#         ## Set logging
#         self.log = logging.getLogger( 'int-pool-%s' % self.name )

#         if log.lower() == 'debug':
#             self.log.setLevel(logging.DEBUG)
#         elif log.lower() == 'warn':
#             self.log.setLevel(logging.WARN)
#         elif log.lower() == 'error':
#             self.log.setLevel(logging.ERROR)
#         else:
#             self.log.setLevel(logging.INFO)

#         ## Load the spec file
#         int_spec = yaml.load(open(SPECS_DIR + "interface_pool.yaml"))
#         self.log.debug('Opening Spec file {}'.format(SPEC_FILE))

#         ## Check device role
#         self.role =  self.data['device_role']['slug']
#         self.log.debug('device role is %s' % self.role)

#         ## Check device design Revision
#         self.design_rev = None
#         role_dr = None
#         if isinstance(self.data['custom_fields'], dict):
#             if 'design_rev' in self.data['custom_fields']:
#                 self.design_rev = self.data['custom_fields']['design_rev']
#                 self.log.debug('device design rev is %s' % self.design_rev)
#                 role_dr = "%s_%s" % (self.role, self.design_rev)

#         if role_dr in int_spec.keys():
#             self.int_spec = int_spec[role_dr]
#             self.log.debug('Found interface profile %s' % role_dr)

#         elif self.role in int_spec.keys():
#             self.int_spec = int_spec[self.role]
#             self.log.debug('Found interface profile %s' % self.role)

#         else:
#             raise Exception("Unable to find an interface pool profile for %s" % self.name)


#         ### Expand Spec list
#         for group in self.int_spec.keys():

#             if group == 'type':
#                 continue

#             expanded_list = expand_int_list(self.int_spec[group])
#             self.int_spec[group] = expanded_list
#             self.log.debug('Found %s interfaces for %s' % (len(expanded_list), group))

#         ### Get the list of existing interface in Netbox
#         ###  Create a dict with name as the key and indicate if the interface is available or not
#         if 'type' in self.int_spec.keys():
#             self.int_type = self.int_spec['type']

#         if self.int_type == 'interface':
#             resp, ok = self.nb.request.dcim.dcim_interfaces_list(device=self.name, limit=1000)

#             for int in resp['results']:
#                 self.int_by_name[int['name']]['exist'] = True
#                 self.int_by_name[int['name']]['used'] = False

#                 if isinstance(int['interface_connection'], dict):
#                     if 'status' in int['interface_connection'].keys():
#                         con = int['interface_connection']
#                         peer = "%s::%s" % (con['interface']['device']['name'], con['interface']['name'])

#                         self.int_by_name[int['name']]['used'] = peer
#                         self.int_by_owner[peer] = int['name']

#         elif self.int_type == 'console':
#             resp, ok = self.nb.request.dcim.dcim_console_server_ports_list(device=self.name, limit=250)

#             for int in resp['results']:
#                 self.int_by_name[int['name']]['exist'] = True
#                 self.int_by_name[int['name']]['used'] = False

#                 if int['connected_console']:

#                     peer_port, ok = self.nb.request.dcim.dcim_console_ports_read(id=int['connected_console'])

#                     if not ok:
#                         self.int_by_name[int['name']]['used'] = True

#                     else:
#                         peer = "%s::%s" % (peer_port['device']['name'], peer_port['name'])

#                         self.int_by_name[int['name']]['used'] = peer
#                         self.int_by_owner[peer] = int['name']


#         elif self.int_type == 'power':
#             resp, ok = self.nb.request.dcim.dcim_power_outlets_list(device=self.name, limit=250)

#             for int in resp['results']:
#                 self.int_by_name[int['name']]['exist'] = True
#                 self.int_by_name[int['name']]['used'] = False

#                 if int['connected_port']:
#                     self.int_by_name[int['name']]['used'] = True

#                     peer_port, ok = self.nb.request.dcim.dcim_power_ports_read(id=int['connected_console'])

#                     if not ok:
#                         self.int_by_name[int['name']]['used'] = True

#                     else:
#                         peer = "%s::%s" % (peer_port['device']['name'], peer_port['name'])

#                         self.int_by_name[int['name']]['used'] = peer
#                         self.int_by_owner[peer] = int['name']

#         else:
#             self.log.warn('%s is not a valid interface type' % self.int_type)

#     def get_int(self, group, device=None, interface=None, int_id=None):
#         """
#         Get interface in a pool
#         If a device and interface are provided, first search if the interface is already allocated
#         If not, pick reserve the next available one

#         If an Id is provided, return the interface matching this Id directly
#         """

#         if group not in self.int_spec.keys():
#             self.log.warn('No group named %s' % group )
#             return False

#         if int_id:

#             if int(int_id) > len(self.int_spec[group]):
#                 self.log.debug('Trying to access an interface by id outside of the pool > %s > %s' % (group, int_id))
#                 return False

#             intf = self.int_spec[group][int(int_id) - 1]

#             ## if the interface is alreayd reserved, just return the interface name
#             ## if it's not reserved yet, reserve it
#             if self.int_by_name[intf]['used'] != False:
#                 return intf

#             if device and interface:
#                 owner = "%s::%s" % (device, interface)
#                 self.int_by_name[intf]['used'] = owner
#                 self.int_by_owner[owner] = intf
#             else:
#                 self.int_by_name[intf]['used'] = True

#             return intf


#         if device and interface:

#             owner = "%s::%s" % (device, interface)
#             self.log.debug('Will check if there is already an interface allocated for this owner > %s' % (owner))

#             if owner in self.int_by_owner.keys():
#                 self.log.debug('There is already an interface for this owner > %s > %s' % (owner, self.int_by_owner[owner]))
#                 if self.int_by_owner[owner] in self.int_spec[group]:
#                     return self.int_by_owner[owner]
#                 else:
#                     self.log.warn('There is already an entry for this device / interface (%s/%s)but it does not belong to the right group' % (device, interface))
#                     return False

#             self.log.debug('will get a new interface for %s ' % owner)

#         for intf in self.int_spec[group]:
#             if intf not in self.int_by_name.keys():
#                 continue

#             if self.int_by_name[intf]['used'] != False:
#                 continue

#             if device and interface:
#                 owner = "%s::%s" % (device, interface)
#                 self.int_by_name[intf]['used'] = owner
#                 self.int_by_owner[owner] = intf

#             else:
#                 self.int_by_name[intf]['used'] = True

#             return intf


class ListPool(object):
    def __init__(self, name, items_list, log="debug"):

        self.name = name
        self.item_by_value = OrderedDict()
        self.item_by_identifier = {}
        self.nbr_item_available = 0
        self.nbr_item = 0

        ## Save all item in a dict by Value
        for item in expand_list(items_list):
            self.item_by_value[item] = False
            self.nbr_item += 1

        self.nbr_item_available = self.nbr_item

    def get_nbr_available(self):
        return self.nbr_item_available

    def get_list_size(self):
        return self.nbr_item

    def reserve(self, item, identifier=None):
        """
        Reserve an item from the Pool
        Optionally, indicate an identifier for this item to be able to retrieve it later
        """

        if item not in self.item_by_value.keys():
            # the integer is NOT part of the list
            return False

        # If item is already reserved, check the identifier
        if self.item_by_value[item] != False:
            if self.item_by_value[item] == identifier:
                return True

            # item already reserved by someone else
            return False

        if identifier:
            self.item_by_value[item] = identifier
            self.item_by_identifier[identifier] = item
            self.nbr_item_available -= 1
            return True

        elif not identifier:
            self.item_by_value[item] = True
            self.nbr_item_available -= 1
            return True

    def get(self, identifier=None):
        """
        Get an item from the pool
        Return the next available one by default, 
          except if an identifier is provided and there is already an item associated with this id
        """

        if identifier:
            if identifier in self.item_by_identifier.keys():
                return self.item_by_identifier[identifier]

        for item in self.item_by_value.keys():

            if self.item_by_value[item] != False:
                continue

            # if this item is available, reserve it
            if identifier:
                self.item_by_value[item] = identifier
                self.item_by_identifier[identifier] = item
                self.nbr_item_available -= 1
                return item

            else:
                self.item_by_value[item] = True
                self.nbr_item_available -= 1
                return item
