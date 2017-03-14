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

        despawn = data.get('dts')
        if despawn:
            despawn = datetime.utcfromtimestamp(despawn)
        else:
            despawn = 'unkn'

        pkmn = {
            'type': 'pokemon',
            'id': data['eid'],
            'pkmn_id': int(data['pid']),
            'disappear_time': despawn,
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
            pkmn['height'] = '?'
            pkmn['weight'] = '?'
            pkmn['gender'] = '?'
            atk, def_, sta = ivs.get('atk'), ivs.get('def'), ivs.get('sta')
            if atk is None or def_ is None or sta is None:
                pkmn['iv'] = 'unkn'
            else:
                pkmn['iv'] = float(((atk + def_ + sta) * 100) / float(45))
        pkmn['gmaps'] = get_gmaps_link(pkmn['lat'], pkmn['lng'])

        return pkmn

########################################################################################################################