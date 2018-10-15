import logging
import os
import inspect
from collections import defaultdict

logger = logging.getLogger("resource_manager")


class IntegerPool(object):
    def __init__(self, name, start, end, log="warn"):

        self.name = name

        if int(start) >= int(end):
            raise Exception(
                "the values provided for the range are not valid, start(%s) needs to be smaller than end(%s)"
                % (start, end)
            )

        self.range_start = int(start)
        self.range_end = int(end)
        self.nbr_integer = self.range_end - self.range_start
        self.nbr_available = self.nbr_integer
        self.padding = "{:0%s}" % len(str(self.nbr_integer))

        self.int_by_key = {}
        self.int_by_id = {}

        ## Set logging
        if log.lower() == "debug":
            logger.setLevel(logging.DEBUG)
        elif log.lower() == "warn":
            logger.setLevel(logging.WARN)
        elif log.lower() == "error":
            logger.setLevel(logging.ERROR)
        else:
            logger.setLevel(logging.INFO)

    def _get_key(self, integer):
        """
        Return the internal id of an integer
        Integer are stored in a dict with a padding system

        The padding system allow to manage large pool without pre-allocation all values
        """

        clean_int = int(integer)
        int_diff = clean_int - self.range_start
        return self.padding.format(int_diff)

    def _get_value(self, key):
        """
        Return the value of an integer from its internal key
        Integer are stored in a dict with a padding system
        """
        return int(key) + self.range_start

    def reserve(self, integer, identifier=None):
        """
        Reserve an integer from the Pool
        Optionally, indicate an identifier for this integer to be able to retrieve it later
        """

        if int(integer) < self.range_start and int(integer) > self.range_end:
            # the integer is NOT part of the range
            return False

        int_key = self._get_key(integer)

        if int_key in self.int_by_key.keys():

            # If integer is already reserved, check the owner
            if self.int_by_key[int_key] == identifier:
                return True
            else:
                return False

        if identifier:
            self.int_by_key[int_key] = identifier
            self.int_by_id[identifier] = int_key
            self.nbr_available -= 1

        else:
            self.int_by_key[int_key] = True
            self.nbr_available -= 1

        return True

    def get(self, identifier=None):
        """
        Get an integer from the pool
        Return the next available one by default, 
          except if an identifier is provided and there is already 
        an integer associated with this id
        """

        if identifier:
            if identifier in self.int_by_id.keys():
                return self._get_value(self.int_by_id[identifier])

        for id in range(0, self.nbr_integer):
            id2str = self.padding.format(id)

            if id2str in self.int_by_key.keys():
                continue

            # if this id is available, reserve it
            if identifier:
                self.int_by_key[id2str] = identifier
                self.int_by_id[identifier] = id2str
                self.nbr_available -= 1
                return self._get_value(id2str)

            else:
                self.int_by_key[id2str] = True
                self.nbr_available -= 1
                return self._get_value(id2str)
