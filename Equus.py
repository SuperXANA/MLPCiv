## Sid Meier's Civilization 4
## Copyright Firaxis Games 2005

from CvPythonExtensions import *
import CvUtil
import CvMapGeneratorUtil
from CvMapGeneratorUtil import HintedWorld, TerrainGenerator, FeatureGenerator, BonusBalancer
from array import array
from random import random, randint, seed, shuffle
import math
import sys

# Configuration: Map Internal Names to Engine IDs and Data Values
CvMapOptions = {
	# XANA (note): We need to create new Map Game Options based on My Little Pony FiM
    # 'LAND_SHAPE': {
        # 'id': 0,
        # 'name_key': "TXT_KEY_MAP_SCRIPT_LAND_SHAPE",
        # 'default': 1, # Make the PW2 landmass generator the default
        # 'values': {
            # 0: "Perlin Noise",
            # 1: "Plate Tectonics"
        # }
    # },
    # 'START_LOC': {
        # 'id': 1,
        # 'name_key': "Start",
        # 'default': 0,
        # 'values': {
            # 0: "TXT_KEY_MAP_SCRIPT_START_ANYWHERE",
            # 1: "Old World (unless Pangaea); -30% players recommended"
        # }
    #
	# },
    'WORLD_WRAP': {
        'id': 2,
        'name_key': "TXT_KEY_MAP_WORLD_WRAP",
        'default': 1,
        'values': {
            0: "TXT_KEY_MAP_WRAP_FLAT",
            1: "TXT_KEY_MAP_WRAP_CYLINDER",
            2: "TXT_KEY_MAP_WRAP_TOROID"
        }
    }
}

# Helper to find the config block by the ID passed from the engine
def getMapOptionByID(keyNumber):
	if not isinstance(keyNumber, int): return None
    for key in CvMapOptions:
        if CvMapOptions[key]['id'] == keyNumber:
            return CvMapOptions[key]
    return None

gc = CyGlobalContext()
localText = CyTranslator()
balancer = BonusBalancer()

class MapConstants:
	def setup(self):
		
		# Defines how the realm is shaped into a torodial form internally, to aid in simulating the mechanics of a circular world.
		# If both values are zero, according to player-set game options, the map is considered as a flat plane with no wrapping.
		# Wrapping upon one axis generates a cylindrical form, whereas wrapping both axis creates a torus-shaped planet. 
		self.WrapX = False
		self.WrapY = False
		
		# Degrees latitude for the top and bottom of the map. This allows
		# for more specific climate zones
		# advc: Was 90, -90. That results in one whole row for 90 and -90 each, which, with an equal-area projection, should take up at most one plot each.
		self.topLatitude    = 85
		self.bottomLatitude = -85
		
		# Decides whether to use the Python random generator or the one that is
		# intended for use with civ maps. The Python random has much higher precision
		# than the civ one. 53 bits for Python result versus 16 for getMapRand. The
		# rand they use is actually 32 bits, but they shorten the result to 16 bits.
		# However, the problem with using the Python random is that it may create
		# syncing issues for multi-player now or in the future, therefore it must be optional.
		# advc (note): For debugging with fixed seeds, it might be best to toggle this off.
		self.UsePythonRandom = True
	
	def initInGameOptions(self):
		return 0

mc = MapConstants()

class PythonRandom:
	def seed(self):
		if mc.UsePythonRandom:
			if CyGame().isNetworkMultiPlayer():
				self.mapRand = gc.getGame().getMapRand()
				seedValue = self.mapRand.get(65535, "Seeding mapRand - Equus.py")
				seed(seedValue)
				self.seedString = "Random seed (Using getMapRand) for this map is %(s)20d" % {"s" :seedValue}
			else:
				# Python 'long' has unlimited precision, while the random generator
				# has 53 bits of precision, so I'm using a 53 bit integer to seed the map!
				seed() # Start with system time
				seedValue = randint(0, 9007199254740991)
				seed(seedValue)
				self.seedString = "Random seed (Using Python rands) for this map is %(s)20d" % {"s" :seedValue}
		else:
			self.mapRand = gc.getGame().getMapRand()
			seedValue = self.mapRand.get(65535, "Seeding mapRand - Equus.py")
			self.mapRand.init(seedValue)
			self.seedString = "Random seed (Using getMapRand) for this map is %(s)20d" % {"s" :seedValue}

	def random(self):
		if mc.UsePythonRandom: 
			return random()
		else:
			# This formula is identical to the getFloat function in CvRandom. It is not exposed to Python so I have to recreate it.
			fResult = float(self.mapRand.get(65535, "Getting float - Equus.py")) / float(65535)
			return fResult

	def randint(self, rMin, rMax):
		# if rMin and rMax are the same, then return the only option
		if rMin == rMax: return rMin
		# returns a number between rMin and rMax inclusive
		if mc.UsePythonRandom:
			return randint(rMin, rMax)
		else:
			# mapRand.get() is not inclusive, so we must make it so
			return rMin + self.mapRand.get(rMax + 1 - rMin, "Getting a randint - Equus.py")
			
PRand = PythonRandom()

def beforeInit():
	PRand.seed() # advc: Moved from generatePlotTypes
	mc.initInGameOptions()

def getDescription():
	return "Random map that simulates a fantasy world largely populated by ponies and other magical creatures. Ready for the AdvCiv mod."

def getWrapX():
	return mc.WrapX

def getWrapY():
	return mc.WrapY

def getNumCustomMapOptions():
	mc.setup()
	return len(CvMapOptions)

def getCustomMapOptionName(argsList):
	# <advc> Use existing translations
    config = getMapOptionByID(argsList[0])
	if config is None: return ""
	return getTranslatedText(config['name_key']) # </advc>

def getNumCustomMapOptionValues(argsList):
	# <advc>
    config = getMapOptionByID(argsList[0])
	if config is None: return 0
    return len(config['values'])

def getCustomMapOptionDescAt(argsList):
	# <advc>
	[iSelectedOption, iActivatedOptionChoice] = argsList
    config = getMapOptionByID(iSelectedOption)
	if config is None: return ""
	return getTranslatedText(config['values'][iActivatedOptionChoice])

# <advc> Make cylindrical the middle choice b/c that's what the standard map scripts do
def getCustomMapOptionDefault(argsList):
    config = getMapOptionByID(argsList[0])
	if config is None: return 0
    return config['default'] # </advc>

def isRandomCustomMapOption(argsList):
	iSelectedOption = argsList[0]
	return False

def isAdvancedMap():
	return False

def isClimateMap():
	return True

def getTopLatitude():
	return mc.topLatitude # advc.001: was 90

def getBottomLatitude():
	return mc.bottomLatitude # advc.001: was -90

def getTranslatedText(string):
	if not isinstance(string, str): return ""
	return unicode(localText.getText(string, ()))
	
class EquusHintedWorld(CvMapGeneratorUtil.HintedWorld):
	
class EquusTerrainGenerator(CvMapGeneratorUtil.TerrainGenerator):
	
class EquusFeatureGenerator(CvMapGeneratorUtil.FeatureGenerator):
	
