# Standard Library Imports
from datetime import datetime
import logging
import multiprocessing
import traceback
# 3rd Party Imports
# Local Imports
from Utils import get_gmaps_link

log = logging.getLogger('Structures')

################################################## Webhook Standards  ##################################################


# GlobalPokeCache Standards
class GlobalPokeCache:
    def __init__(self):
        raise NotImplementedError("This is a static class not meant to be initiated")

    @staticmethod
    def make_object(data):
        try:
            return GlobalPokeCache.pokemon(data)
        except Exception as e:
            log.error("Encountered error while processing webhook ({}: {})".format(type(e).__name__, e))
            log.debug("Stack trace: \n {}".format(traceback.format_exc()))
        return None

    @staticmethod
    def pokemon(data):
        log.debug("Converting to pokemon: \n {}".format(data))

        pkmn = {
            'type': 'pokemon',
            'id': data['eid'],
            'pkmn_id': int(data['pid']),
            'disappear_time': datetime.utcfromtimestamp(data['dts']),
            'lat': float(data['lat']),
            'lng': float(data['lon']),
        }

        # Check optional data
        ivs = data.get('ivs')
        if ivs:
            pkmn['move_1_id'] = ivs.get('m1', 'unkn')
            pkmn['move_2_id'] = ivs.get('m2', 'unkn')
            pkmn['atk'] = ivs.get('atk', 'unkn')
            pkmn['def'] = ivs.get('def', 'unkn')
            pkmn['sta'] = ivs.get('sta', 'unkn')
            atk, def_, sta = data.get('atk'), data.get('def'), data.get('sta')
            if atk is None or def_ is None or sta is None:
                pkmn['iv'] = 'unkn'
            else:
                pkmn['iv'] = float(((atk + def_ + sta) * 100) / float(45))
        pkmn['gmaps'] = get_gmaps_link(pkmn['lat'], pkmn['lng'])

        log.info(pkmn)

        return pkmn

########################################################################################################################


class Geofence(object):

    # Expects points to be
    def __init__(self, name, points):
        self.__name = name
        self.__points = points

        self.__min_x = points[0][0]
        self.__max_x = points[0][0]
        self.__min_y = points[0][1]
        self.__max_y = points[0][1]

        for p in points:
            self.__min_x = min(p[0], self.__min_x)
            self.__max_x = max(p[0], self.__max_x)
            self.__min_y = min(p[1], self.__min_y)
            self.__max_y = max(p[1], self.__max_y)

    def contains(self, x, y):
        # Quick check the boundary box of the entire polygon
        if self.__max_x < x or x < self.__min_x or self.__max_y < y or y < self.__min_y:
            return False

        inside = False
        p1x, p1y = self.__points[0]
        n = len(self.__points)
        for i in range(1, n+1):
            p2x, p2y = self.__points[i % n]
            if min(p1y, p2y) < y <= max(p1y, p2y) and x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y
        return inside

    def get_name(self):
        return self.__name


# Class to allow optimization of waiting requests (not process safe)
class QueueSet(object):
    def __init__(self):
        self.__queue = multiprocessing.Queue()
        self.__lock = multiprocessing.Lock()
        self.__data_set = {}

    # Add or update an object to the QueueSet
    def add(self, id_, obj):
        self.__lock.acquire()
        try:
            if id_ not in self.__data_set:
                self.__queue.put(id_)
            self.__data_set[id_] = obj  # Update info incase it had changed
        except Exception as e:
            log.error("QueueSet error encountered in add: \n {}".format(e))
        finally:
            self.__lock.release()

    # Remove the next item in line
    def remove_next(self):
        self.__lock.acquire()
        data = None
        try:
            id_ = self.__queue.get(block=True)  # get the next id
            data = self.__data_set[id_]  # extract the relevant data
            del self.__data_set[id_]  # remove the id from the set
        except Exception as e:
            log.error("QueueSet error encountered in remove: \n {}".format(e))
        finally:
            self.__lock.release()
        return data
