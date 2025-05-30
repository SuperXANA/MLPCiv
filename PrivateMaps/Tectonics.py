# advc.021a: Tectonics 3.16 with minor changes
# replacing v3.15 (included with BtS)

#-----------------------------------------------------------------------------
#	Copyright (c) 2005-2008 Laurent Di Cesare
#	Copyright (c) 2008 Firaxis Games, Inc. All rights reserved.
#-----------------------------------------------------------------------------
#
# FILE: Tectonics.py
# AUTHOR: Laurent Di Cesare (LDiCesare)
# PURPOSE: Provide a map with mountain ranges, preferably near the coasts.
# DESCRIPTION:
# Provide a map with several continents, possibly some big islands,
# and simulates some very rough plate tectonics to generate mountain ranges.
# The map is tuned to generate about 40% land and 60% water but only the
# number of plates is fixed, not the actual size of the plates, so landmasses
# sizes may vary quite a bit.
# It is an adaptation to CivIV of an algorithm originally developped for
# the Clash of Civilizations (http://clash.apolyton.net)
# VERSION 1.0 Initial version
# VERSION 1.1 Changed the moveplates and blur routines to avoid having 
#                           big lumps of peaks propagating everywhere.
#             Added subduction
#             Hinted continents seeds to avoid the poles
# VERSION 2.0 Added climate management.
# VERSION 2.1 Made desert edges rougher. 
#             Added first try at rivers. 
#             Increased subduction
# VERSION 3.0 Added various landmasses (Pangaeas, Lakes, Islands).
#             Modified rivers
# VERSION 3.1 Lost when reinstalling windows and not backing it up. 
#             It was great, though.
# VERSION 3.2 Provided new option for Earthlike, and grouped land masses
#             so 2/3rds are on the same hemisphere. Less ice.
# VERSION 3.3 Systematic use of climate map because I had bugged it away for
#             the main map type instead of pangaea. Tried to prevent players
#             from starting in the ice. Added hotspots.
# VERSION 3.4 Minor rewritings. 
#             Added fault lines: Some hills and lakes will pop up inside 
#             vast flat areas, forming a ridge line, but with lots of flat
#             lands inside. Not always noticeable but has a definite effect.
#             Corrected climate generation which didn't blow enough moisture.
# VERSION 3.5 Added several climate options. Tuned the starting locations.
# VERSION 3.6 Roughed the edges of the various climate zones to avoid excess
#             of straight limits.
#             Added Mediterranean land type (inner sea).
#             Added No Ice option that replaces ice with tundra and tundra 
#             with grass, otherwise behaves as normal humidity level.
# VERSION 3.7 Mediterranean map rewrite: East is always land, more and bigger 
#             islands, correct latitude used for feature generation.
# VERSION 3.8 Fixed WrapY error.
# VERSION 3.9 Fixed subduction error.
# VERSION 3.10 Shapes of plates are somewhat less square, and rivers in desert
#             are always floodplains even after the default algorithm adds
#             them near players' starting location
# VERSION 3.11 Climate generation rewritten, rivers less likely to start
#             in desert and more often from hills.
# VERSION 3.12 Broke east-west climate lines, smoothed desert-grass 
#             transitions always through plains.
# VERSION 3.13 More mountains (second pass of movePlates). Terra option.
# VERSION 3.14 Fixed starting plot generation errors.
# VERSION 3.15 Added an option not to group civs on Terra option,
#							 Tuned Terra landmasses (mostly Africa, Greenland), removed
#							 Antarctic landmass (too many barbs spawning there).
# VERSION 3.16 Included Firaxis code for translating the options. 
#							Kept my copyrights.
#             Added more rivers. (Also aborted try at heghtmap for rivers.)
#						  Updated the Terra option to have much better looking Arabia.
# TODO The shape of the plates should be less polygonal and more random 
#      (more round than rectangular)
#      The number of plates could be more tunable.
#      I could also rewrite the whole rivers thing...

# advc: Some imports were unused
from CvPythonExtensions import *
#import CvUtil
import CvMapGeneratorUtil
#import Popup as PyPopup
#from CvMapGeneratorUtil import TerrainGenerator
from CvMapGeneratorUtil import FeatureGenerator

# advc.165:
def getNumPlotsPercent(argsList):
	[iWorldSize] = argsList
	if iWorldSize < 0:
		return 100
	sizeModifiers = {
		# NB: The smallest two sizes have highly unpredictable land-sea ratios
		WorldSizeTypes.WORLDSIZE_DUEL:		89,
		WorldSizeTypes.WORLDSIZE_TINY:		87,
		WorldSizeTypes.WORLDSIZE_SMALL:		85,
		WorldSizeTypes.WORLDSIZE_STANDARD:	83,
		WorldSizeTypes.WORLDSIZE_LARGE:		81,
		WorldSizeTypes.WORLDSIZE_HUGE:		77
	}
	if iWorldSize >= len(sizeModifiers):
		return 73
	return sizeModifiers[iWorldSize]

def getDescription():
	return "TXT_KEY_MAP_SCRIPT_TECTONICS_DESCR"

def isAdvancedMap():
	"This map should show up in simple mode"
	return 0

def isSeaLevelMap():
	return 0

def getNumCustomMapOptions():
	return 2

def getCustomMapOptionName(argsList):
	index = argsList[0]
	if (index == 0):
		translated_text = unicode(CyTranslator().getText("TXT_KEY_MAP_SCRIPT_LANDMASS_TYPE", ()))
	else:
		translated_text = unicode(CyTranslator().getText("TXT_KEY_MAP_SCRIPT_ARITITY", ()))
	return translated_text

def getNumCustomMapOptionValues(argsList):
	index = argsList[0]
	if (index == 0):
		return 9 # advc.021a: was 8
	else:
		return 4

def getWrapX():
	if (6 == CyMap().getCustomMapOption(0)): # advc.021a: was 5==...
		return False
	return True

def getWrapY():
	return False

def getTopLatitude():
	if (6 == CyMap().getCustomMapOption(0)): # advc.021a: was 5==...
		return 65
	#return 90
	CyPythonMgr().allowDefaultImpl() # advc.129

def getBottomLatitude():
	if (6 == CyMap().getCustomMapOption(0)): # advc.021a: was 5==...
		return 25
	#return -90
	CyPythonMgr().allowDefaultImpl() # advc.129
	
def getCustomMapOptionDescAt(argsList):
	iOption = argsList[0]
	iSelection = argsList[1]
	selection_names = ["TXT_KEY_MAP_SCRIPT_EARTH_70",
	                   "TXT_KEY_MAP_SCRIPT_EARTH_60",
					   "TXT_KEY_MAP_SCRIPT_EARTH_50", # advc.021a
	                   "TXT_KEY_MAP_SCRIPT_PANGAEA",
	                   "TXT_KEY_MAP_SCRIPT_LAKES",
	                   "TXT_KEY_MAP_SCRIPT_ISLANDS_90", # advc.021a: was ..._ISLANDS
	                   "TXT_KEY_MAP_SCRIPT_MEDITERRANEAN", 
	                   "TXT_KEY_MAP_SCRIPT_TERRA",
	                   "TXT_KEY_MAP_SCRIPT_TERRA_OLD_WORLD_START"]
	                   
	aridity_names = ["TXT_KEY_CLIMATE_ARID",
	                 "TXT_KEY_GAMESPEED_NORMAL",
	                 "TXT_KEY_MAP_SCRIPT_WET",
	                 "TXT_KEY_MAP_SCRIPT_NO_ICE"]
	                 
	if (iOption == 0):
		return unicode(CyTranslator().getText(selection_names[iSelection], ()))
	else:
		return unicode(CyTranslator().getText(aridity_names[iSelection], ()))

def getCustomMapOptionDefault(argsList):
	iOption = argsList[0]
	if (iOption == 0):
		return 1 # advc.021a: Was 0, i.e. EARTH_70. Now EARTH_60 as the default.
	else:
		return 1

def isClimateMap():
	return 0

def generateTerrainTypes():
	NiTextOut("Generating Terrain ...")
	terraingen = ClimateGenerator()
	terrainTypes = terraingen.generateTerrain()
	return terrainTypes

# advc: Obsolete (probably since v3.7)
'''
def addFeatures():
	NiTextOut("Adding Features (from Python Continents) ...")
	# advc.021a: was ...==5
	if (CyMap().getCustomMapOption(0) == 6):         #  "Mediterranean"
		featuregen = NoIceFeatureGenerator()
	else:
		featuregen = FeatureGenerator()
	featuregen.addFeatures()
	return 0

class NoIceFeatureGenerator(FeatureGenerator):
	def addIceAtPlot(self, pPlot, iX, iY, lat):
		return
'''

class voronoiMap:
	def __init__(self,landPlates,seaPlates,hotspotsF):
		map = CyMap()
		gc = CyGlobalContext()
		self.dice = gc.getGame().getMapRand()
		self.mapWidth = map.getGridWidth()
		self.mapHeight = map.getGridHeight()
		self.plotTypes = [PlotTypes.PLOT_OCEAN] * (self.mapWidth*self.mapHeight)
		self.heightMap = [0] * (self.mapWidth*self.mapHeight)
		self.plateMap = [0] * (self.mapWidth*self.mapHeight)
		self.numContinents = landPlates
		self.hotSpotFrequency = hotspotsF
		self.numSeaPlates = seaPlates + 1 # plate 0 is for initialisation
		self.plate = [0] * (self.numContinents + self.numSeaPlates)
		# plateSize is a random number which gives the probability of growing a plate
		self.plateSize = [0] * (self.numContinents + self.numSeaPlates)
		self.altitudeVariation = 2
		# advc.021a: was 12
		self.peakAltitude = 15
		# advc.021a: was 9
		self.hillAltitude = 10
		self.landAltitude = 6
		for x in range(self.mapWidth):
			for y in range(self.mapHeight):
				i = y*self.mapWidth + x
				self.plotTypes[i] = PlotTypes.PLOT_OCEAN

	def generate(self):
		self.sowSeeds()
		self.fillPlates()
		self.movePlates(true)
		self.erode()
		self.movePlates(false)
		self.blur()
		self.addFaults()
		self.hotspots()
		self.createMap()
		self.finalizeMap()
		return self.plotTypes

	def sowSeeds(self):
		self.mostLands = self.dice.get(2,"mostland hemisphere")
		for i in range(self.numSeaPlates):
			self.plate[i] = self.dice.get(3,"Sea altitude")
		for i in range(self.numContinents):
			self.plate[self.numSeaPlates + i] = self.landAltitude + self.dice.get(3,"Land altitude")
		for i in range(self.numContinents + self.numSeaPlates):
			x, y = self.getCoord(i)
			while self.plateMap[y*self.mapWidth + x] != 0:
				x, y = self.getCoord(i)
			self.plateMap[y*self.mapWidth + x] = i
			self.plateSize[i] = 2 + self.dice.get(6,"Some randomness in plate sizes")

	def getCoord(self,i):
		x = self.dice.get(self.mapWidth,"x seed for plate")
		if (i >= self.numSeaPlates + (self.numContinents/3)):
			y = 2 + self.dice.get(2*self.mapHeight/3,"y seed for plate")
			if (i >= self.numSeaPlates + 1 + (self.numContinents/3)):
				if (self.mostLands == 0):
					y = self.mapHeight - y - 1
			elif (self.mostLands == 1):
				y = self.mapHeight - y - 1
		else:
			y = self.dice.get(self.mapHeight,"y seed for plate")
		return x, y

	def fillPlates(self):
		filled = False
		bufferPlateMap = [0] * (self.mapWidth*self.mapHeight)
		while filled == False:
			filled = True
			for x in range(self.mapWidth):
				for y in range(self.mapHeight):
					i = y*self.mapWidth + x
					bufferPlateMap[i] = self.plateMap[i]
					if (self.plateMap[i] == 0):
						bufferPlateMap[i] = self.neighbour(x,y)
			for x in range(self.mapWidth):
				for y in range(self.mapHeight):
					i = y*self.mapWidth + x
					self.plateMap[i] = bufferPlateMap[i]
					if self.plateMap[i] == 0:
						filled = False
		for x in range(self.mapWidth):
			for y in range(self.mapHeight):
				i = y*self.mapWidth + x
				self.heightMap[i] = self.plate[self.plateMap[i]] + self.dice.get(self.altitudeVariation,"Random variation of altitude")

	def movePlates(self,dontMoveSeaPlates):
		plates = self.numContinents + self.numSeaPlates
		xMoves = [0] * plates
		yMoves = [0] * plates
		subduction = [0] * plates
		min = 0
		if dontMoveSeaPlates:
			min = self.numSeaPlates
		for i in range(min,plates):
			xMoves[i] = self.dice.get(3,"moves") - 2
			yMoves[i] = self.dice.get(3,"moves") - 2
			subduction[i] = self.dice.get(10,"subduction")
		self.doMovePlates(xMoves,yMoves,subduction)

	def doMovePlates(self,xMoves,yMoves,subduction):
		mapSize = self.mapWidth*self.mapHeight
		#FIXME There must be a clone method somewhere?
		oldHeightMap = [0] * mapSize
		for i in range(mapSize):
			oldHeightMap[i] = self.heightMap[i]
		for x in range(self.mapWidth):
			for y in range(self.mapHeight):
				currentCoord = y*self.mapWidth + x
				currentPlate = self.plateMap[currentCoord]
				if (xMoves[currentPlate] != 0 or yMoves[currentPlate] != 0):
					movedX = x + xMoves[currentPlate]
					movedY = y + yMoves[currentPlate]
					if (movedX >= 0 and movedX < self.mapWidth):
						if (movedY >= 0 and movedY < self.mapHeight):
							movedCoord = movedY*self.mapWidth + movedX
							targetPlate = self.plateMap[movedCoord]
							if (targetPlate != currentPlate):
								if (subduction[currentPlate] >= 6):
									sum = oldHeightMap[movedCoord] + oldHeightMap[currentCoord] + 2
									if (self.heightMap[movedCoord] < sum ):
										self.heightMap[movedCoord] = sum 
									self.heightMap[currentCoord] = self.heightMap[currentCoord] -1
								else:
									sum = oldHeightMap[movedCoord] + oldHeightMap[currentCoord] -2
									if (self.heightMap[movedCoord] < sum and self.heightMap[movedCoord] >= self.landAltitude):
										self.heightMap[movedCoord] = sum
									if (self.heightMap[currentCoord] < sum and self.heightMap[currentCoord] >= self.landAltitude):
										self.heightMap[currentCoord] = sum

	def addFaults(self):
		"Adds faultlines to break up big flat land masses. Think Rift Valley."
		plates = self.numContinents + self.numSeaPlates
		width = [0] * plates
		height = [0] * plates
		sum = [0] * plates
		lastPlate = 0
		for x in range(self.mapWidth):
			for y in range(self.mapHeight):
				currentCoord = y*self.mapWidth + x
				lastPlate = self.checkFault(currentCoord,sum,height,lastPlate)
		for y in range(self.mapHeight):
			for x in range(self.mapWidth):
				currentCoord = y*self.mapWidth + x
				lastPlate = self.checkFault(currentCoord,sum,width,lastPlate)
		for i in range(plates):
			if (width[i] != 0): self.verticalFault(i,width[i])
			elif (height[i] != 0): self.horizontalFault(i,height[i])

	def checkFault(self,currentCoord,sum,table,lastPlate):
		plates = self.numContinents + self.numSeaPlates
		faultLimit = 7
		if (self.heightMap[currentCoord] <= self.landAltitude):
			return 0
		if (self.heightMap[currentCoord] > self.hillAltitude):
			return 0
		currentPlate = self.plateMap[currentCoord]
		if (lastPlate != currentPlate):
			if (sum[lastPlate] >= 0):
				sum[lastPlate] = 0
			lastPlate = currentPlate
		elif (sum[lastPlate] >= 0):
			sum[lastPlate] = 1 + sum[lastPlate]
		if (sum[lastPlate] > faultLimit):
			table[lastPlate] = currentCoord
			sum[lastPlate] = -1
		return lastPlate

	def verticalFault(self,plateNumber,coord):
		nextCoord = coord - 3 + self.dice.get(6,"Fault position")
		mapSize = self.mapWidth*self.mapHeight
		while (nextCoord >= 0 and nextCoord < mapSize):
			if (self.plateMap[nextCoord] != plateNumber):
				break
			self.fault(nextCoord)
			nextCoord = nextCoord + self.mapWidth + self.dice.get(3,"Fault tilt") - 1

	def horizontalFault(self,plateNumber,coord):
		nextCoord = coord + (self.dice.get(6,"Fault position") - 3) * self.mapWidth 
		mapSize = self.mapWidth*self.mapHeight
		max = coord + self.mapWidth
		if (max > mapSize):
			max = mapSize
		while (nextCoord >= 0 and nextCoord < max):
			if (self.plateMap[nextCoord] != plateNumber):
				break
			self.fault(nextCoord)
			nextCoord = nextCoord + 1 + (self.dice.get(3,"Fault tilt") - 1)*self.mapWidth

	def fault(self,coord):
		dieRoll = self.dice.get(20,"Fault line effect")
		if (dieRoll > 11):
			self.heightMap[coord] = self.hillAltitude + 1
		elif (dieRoll > 9):
			self.heightMap[coord] = 0

	def erode(self):
		for x in range(self.mapWidth):
			for y in range(self.mapHeight):
				i = y*self.mapWidth + x
				if self.heightMap[i] > self.peakAltitude:
					self.heightMap[i] -= 2
				if self.heightMap[i] > self.hillAltitude:
					self.heightMap[i] -= 1
				hasSeaNeighbour = False
				hasHillNeighbour = False
				leftX = x-1
				if (leftX < 0):
					leftX = self.mapWidth - 1
				left = self.heightMap[leftX + y*self.mapWidth] 
				if (left < self.landAltitude):
					hasSeaNeighbour = True
				elif (left > self.hillAltitude):
					hasHillNeighbour = True
				rightX = x+1
				if (rightX >= self.mapWidth):
					rightX = 0
				right = self.heightMap[rightX + y*self.mapWidth] 
				if (right < self.landAltitude):
					hasSeaNeighbour = True
				elif (right > self.hillAltitude):
					hasHillNeighbour = True
				if (y>0):
					top = self.heightMap[x + (y-1)*self.mapWidth] 
					if (top < self.landAltitude):
						hasSeaNeighbour = True
					elif (top > self.hillAltitude):
						hasHillNeighbour = True
				if (y<self.mapHeight - 2):
					bottom = self.heightMap[x + (y+1)*self.mapWidth] 
					if (bottom < self.landAltitude):
						hasSeaNeighbour = True
					elif (bottom > self.hillAltitude):
						hasHillNeighbour = True
				if (hasSeaNeighbour):
					self.heightMap[i] = self.heightMap[i] - 1
				if (hasHillNeighbour):
					self.heightMap[i] = self.heightMap[i] - 1


	def min( height, left, right, top, bottom ):
		minHeight = height
		if ( minHeight > left ):
			minHeight = left
		if ( minHeight > right ):
			minHeight = right
		if ( minHeight > top ):
			minHeight = top
		if ( minHeight > bottom ):
			minHeight = bottom
		return minHeight

	def blur(self):
		#FIXME There must be a clone method somewhere?
		mapSize = self.mapWidth*self.mapHeight
		oldHeightMap = [0] * (mapSize)
		for i in range(mapSize):
			oldHeightMap[i] = self.heightMap[i]
		for x in range(self.mapWidth):
			for y in range(self.mapHeight):
				i = y*self.mapWidth + x
				height = self.heightMap[i]
				leftX = x-1
				if (leftX < 0):
					leftX = self.mapWidth - 1
				left = oldHeightMap[leftX + y*self.mapWidth]
				rightX = x+1
				if (rightX >= self.mapWidth):
					rightX = 0
				right = oldHeightMap[rightX + y*self.mapWidth]
				top = height
				if (y>0):
					top = oldHeightMap[x + (y-1)*self.mapWidth]
				bottom = height
				if (y<self.mapHeight - 2):
					bottom = oldHeightMap[x + (y+1)*self.mapWidth]
				self.heightMap[i] = (height * 4 + left + right + top + bottom) / 8
				minHeight = min(height,left,right,top,bottom)
				if (minHeight >= self.peakAltitude):
					oldHeightMap[leftX + y*self.mapWidth] = self.hillAltitude + 1 
					self.heightMap[leftX + y*self.mapWidth] = self.hillAltitude  + 1
					oldHeightMap[rightX + y*self.mapWidth] = self.hillAltitude  + 1
					self.heightMap[rightX + y*self.mapWidth] = self.hillAltitude  + 1
					if (y>0):
						oldHeightMap[x + (y-1)*self.mapWidth] = self.hillAltitude  + 1
						self.heightMap[x + (y-1)*self.mapWidth] = self.hillAltitude  + 1
					if (y<self.mapHeight - 2):
						oldHeightMap[x + (y+1)*self.mapWidth] = self.hillAltitude + 1
						self.heightMap[x + (y+1)*self.mapWidth] = self.hillAltitude + 1

	def hotspots(self):
		mapSize = self.mapWidth * self.mapHeight
		hotSpotsNumber = mapSize/self.hotSpotFrequency
		for hotspot in range(hotSpotsNumber):
			i = self.dice.get(mapSize,"Hotspot location")
			self.heightMap[i] = self.heightMap[i] + self.dice.get(self.peakAltitude,"Hotspot altitude")

	def createMap(self):
		for y in range(self.mapHeight):
			for x in range(self.mapWidth):
				i = y*self.mapWidth + x
				height = self.heightMap[i]
				if (height > self.peakAltitude):
					if (self.dice.get(7,"Random pass") == 6):
						self.plotTypes[i] = PlotTypes.PLOT_HILLS
					else:
						self.plotTypes[i] = PlotTypes.PLOT_PEAK
				elif (height > self.hillAltitude):
					if (self.dice.get(20,"Random peak") == 19):
						self.plotTypes[i] = PlotTypes.PLOT_PEAK
					else:
						self.plotTypes[i] = PlotTypes.PLOT_HILLS
				elif (height > self.landAltitude):
					# <advc.021a>
					if self.dice.get(100, "Random hill") < height:
						self.plotTypes[i] = PlotTypes.PLOT_HILLS
					# </advc.021a>
					self.plotTypes[i] = PlotTypes.PLOT_LAND
				else:
					self.plotTypes[i] = PlotTypes.PLOT_OCEAN

	def finalizeMap(self):
		return

	def neighbour(self,x,y):
		roll = self.dice.get(10,"Some randomness in plate shapes")
		leftX = x-1
		if (leftX < 0):
			leftX = self.mapWidth - 1
		left = self.plateMap[leftX + y*self.mapWidth]
		if (left != 0):
			if (roll <= self.plateSize[left]):
				return left
		rightX = x+1
		if (rightX >= self.mapWidth):
			rightX = 0
		right = self.plateMap[rightX + y*self.mapWidth]
		if (right != 0):
			if (roll <= self.plateSize[right]):
				return right
		if (y>0):
			top = self.plateMap[x + (y-1)*self.mapWidth]
			if (top != 0):
				if (roll <= self.plateSize[top]):
					return top
		if (y<self.mapHeight - 2):
			bottom = self.plateMap[x + (y+1)*self.mapWidth]
			if (bottom != 0):
				if (roll <= self.plateSize[bottom]):
					return bottom
		return 0

class voronoiMediterraneanMap(voronoiMap):
	def __init__(self,numPlayers):
		voronoiMap.__init__(self,numPlayers*5/2, numPlayers,150)
		self.peakAltitude = 13

	def movePlates(self,dontMoveSeaPlates):
		if dontMoveSeaPlates:
			return
		voronoiMap.movePlates(self,true)

	def getCoord(self,i):
		mapWidthFraction = self.mapWidth/self.numSeaPlates
			# Sea plates
		if (i < self.numSeaPlates): 
			x = mapWidthFraction*i + self.dice.get(mapWidthFraction,"x seed for sea plate")
			y = self.mapHeight/3 + self.dice.get(self.mapHeight/3,"y seed for plate")
		else:
			# One land plate to the east to link north and south
			if (i == self.numSeaPlates + self.numContinents - 1):
				x = self.dice.get(self.mapWidth - 2,"x seed for link land plate")
				y = self.mapHeight/3 + self.dice.get(self.mapHeight/3,"y seed for land plate")
			# Other land plates half north half south
			elif (i < self.numSeaPlates * 2):
				x = mapWidthFraction * (i - self.numSeaPlates) + self.dice.get(mapWidthFraction,"x seed for land plate")
				y = self.getLandY(0)
			elif (i >= self.numSeaPlates * 3):
				x = mapWidthFraction * (i - 2*self.numSeaPlates) + self.dice.get(mapWidthFraction,"x seed for land plate")
				y = self.getLandY(1)
			else:
				x = self.dice.get(self.mapWidth,"x seed for land plate")
				y = self.getLandY(i)
		return x, y

	def getLandY(self,i):
		y = 1 + self.dice.get(self.mapHeight/4,"y seed for land plate")
		if (i == 2*(i/2)):
			y = y + self.mapHeight*3/4 -1
		return y

	def hotspots(self):
		mapSize = self.mapWidth * self.mapHeight
		hotSpotsNumber = mapSize/self.hotSpotFrequency
		minX = 2
		maxX = self.mapWidth*9/10
		minY = self.mapHeight/10
		yRange = self.mapHeight*8/10
		for hotspot in range(hotSpotsNumber):
			x = minX + self.dice.get(maxX,"Hotspot X")
			y = minY + self.dice.get(yRange,"Hotspot Y")
			i = y*self.mapWidth + x
			while (self.plotTypes[i] != PlotTypes.PLOT_OCEAN):
				x = minX + self.dice.get(maxX,"Hotspot X")
				y = minY + self.dice.get(yRange,"Hotspot Y")
				i = y*self.mapWidth + x
			self.heightMap[i] = self.heightMap[i] + self.dice.get(self.peakAltitude,"Hotspot altitude")
			self.spreadHotSpot(i)

	def spreadHotSpot(self,i):
		self.spreadIsland(i+1)
		self.spreadIsland(i-1)
		self.spreadIsland(i+self.mapWidth)
		self.spreadIsland(i-self.mapWidth)

	def spreadIsland(self,i):
		self.heightMap[i] = self.heightMap[i] + self.dice.get(self.peakAltitude,"Hotspot altitude")
		if (self.heightMap[i] > self.landAltitude):
			self.spreadBigIsland(i+1)
			self.spreadBigIsland(i-1)
			self.spreadBigIsland(i+self.mapWidth)
			self.spreadBigIsland(i-self.mapWidth)

	def spreadBigIsland(self,i):
		if (self.heightMap[i] <= self.landAltitude):
			self.heightMap[i] = self.dice.get(self.peakAltitude,"Island altitude")

	def finalizeMap(self):
		# Make sure that the north and south borders are made of land.
		for y in range(self.mapHeight):
			for x in range(self.mapWidth):
				if self.checkY(y):
					i = y*self.mapWidth + x
					if (self.plotTypes[i] == PlotTypes.PLOT_OCEAN):
						self.plotTypes[i] = PlotTypes.PLOT_LAND
		# Make sure that there's a way north/south by foot or galley
		minEastWidth = self.mapWidth * 9 /10
		margin = self.mapWidth/10
		for y in range(self.mapHeight-1):
			for x in range(minEastWidth,self.mapWidth):
				if (x + 3 + self.dice.get(margin,"Border")) > self.mapWidth:
					i = y*self.mapWidth + x
					if (self.plotTypes[i] == PlotTypes.PLOT_OCEAN):
						self.plotTypes[i] = PlotTypes.PLOT_LAND

	def checkY(self,y):
		if (y > 9*self.mapHeight/10):
			y = self.mapHeight - y
		if (y < self.mapHeight/10):
			if (2 + self.dice.get(self.mapHeight/10,"Border")) > y:
				return True
		return False

class voronoiTerraMap(voronoiMap):
	def __init__(self):
		voronoiMap.__init__(self,12,8,800)
		self.altitudeVariation = 3

	def sowSeeds(self):
		for i in range(0,8):
			self.plate[i] = 2
		for i in range(8,20):
			self.plate[i] = self.landAltitude + 3
		#Pacific Ocean
		for i in range(self.mapHeight):
			self.plateMap[i*self.mapWidth] = 1
		for i in range(self.mapWidth/10):
			self.plateMap[self.mapHeight*self.mapWidth/2 -self.mapWidth/20 + i] = 1
		x = self.mapWidth/10
		y = self.mapHeight/5
		self.plateMap[x + y*self.mapWidth] = 1
		self.plateSize[1] = 7
		#North Atlantic
		x = self.mapWidth/3
		ymin = 2*self.mapHeight/3
		ymax = 7*self.mapHeight/8
		for y in range(ymin,ymax):
			self.plateMap[x + y*self.mapWidth] = 2
		x = 3*self.mapWidth/10
		y = 3*self.mapHeight/5
		self.plateMap[x + y*self.mapWidth] = 2
		self.plateSize[2] = 7
		#South Atlantic
		x = self.mapWidth/3
		yMin = self.mapHeight/5
		yMax = self.mapHeight/3
		for y in range(yMin,yMax):
			self.plateMap[x + y*self.mapWidth] = 3
		for x in range(self.mapWidth/4,self.mapWidth/2):
			self.plateMap[self.mapWidth/3 + self.mapHeight/5*self.mapWidth] = 3
		x = self.mapWidth/3
		y= 5*self.mapHeight/12
		self.plateMap[x + y*self.mapWidth] = 3
		x = self.mapWidth/4 +1
		y = self.mapHeight/4
		self.plateMap[x + y*self.mapWidth] = 3
		self.plateSize[3] = 7
		#Arctic Ocean
		for i in range(self.mapWidth):
			self.plateMap[self.mapWidth*(self.mapHeight-2) + i] = 4
		self.plateSize[4] = 3
		#Mediterranean
		x = 4*self.mapWidth/9
		y = 3*self.mapHeight/4
		self.plateMap[x + y*self.mapWidth] = 5
		self.plateSize[5] = 4
		#Indian Ocean
		x = 3*self.mapWidth/4
		y = self.mapHeight/3
		self.plateMap[x + y*self.mapWidth] = 6
		x = 3*self.mapWidth/5
		y = self.mapHeight/3
		self.plateMap[x + y*self.mapWidth] = 6
		x = 2*self.mapWidth/3
		y = 9*self.mapHeight/20
		self.plateMap[x + y*self.mapWidth] = 6
		self.plateSize[6] = 7
		#Antarctic Ocean
		y = self.mapHeight/8
		for i in range(self.mapWidth):
			self.plateMap[i+y*self.mapWidth] = 7
		self.plateSize[7] = 4
		#North America
		x = self.mapWidth/5
		yMin = 4*self.mapHeight/5
		yMax = 6*self.mapHeight/7
		for y in range(yMin,yMax):
			self.plateMap[x + y*self.mapWidth] = 8
		self.plateMap[self.mapWidth/20 + yMax*self.mapWidth] = 8
		self.plateSize[8] = 8
		#South America
		x = self.mapWidth/5
		y = self.mapHeight/4
		self.plateMap[x + y*self.mapWidth] = 9
		y = self.mapHeight/3
		self.plateMap[x + y*self.mapWidth] = 9
		x = self.mapWidth/4 +1
		y = 2*self.mapHeight/5
		self.plateMap[x + y*self.mapWidth] = 9
		self.plateSize[9] = 5
		#Europe
		x = self.mapWidth/2
		y = 6*self.mapHeight/7
		self.plateMap[x + y*self.mapWidth] = 10
		x = 3*self.mapWidth/7
		y = 4*self.mapHeight/5
		self.plateMap[x + y*self.mapWidth] = 10
		self.plateSize[10] = 6
		#Asia
		x = 3*self.mapWidth/4
		y = 7*self.mapHeight/10
		self.plateMap[x + y*self.mapWidth] = 11
		x = 4*self.mapWidth/5
		y = 4*self.mapHeight/5
		self.plateMap[x + y*self.mapWidth] = 11
		x = 2*self.mapWidth/3
		y = 4*self.mapHeight/5
		self.plateMap[x + y*self.mapWidth] = 11
		self.plateSize[11] = 9
		#Africa
		x = 7*self.mapWidth/20
		y = 2*self.mapHeight/3 -1
		for i in range(self.mapWidth/12):
			self.plateMap[x  + i + y*self.mapWidth] = 12
		x = self.mapWidth/2
		y = 2*self.mapHeight/5
		self.plateMap[x + y*self.mapWidth] = 12
		self.plateSize[12] = 6
		#India
		x = 3*self.mapWidth/4
		y = 5*self.mapHeight/9
		self.plateMap[x + y*self.mapWidth] = 13
		self.plateSize[13] = 3
		#Oceania
		x = 4*self.mapWidth/5
		y = self.mapHeight/4 +1
		self.plateMap[x + y*self.mapWidth] = 14
		self.plateSize[14] = 4
		#Middle East
		x = 3*self.mapWidth/5
		y = 4*self.mapHeight/7
		self.plateMap[x + y*self.mapWidth] = 15
		self.plateSize[15] = 2
		self.plate[15] = self.landAltitude + 1
		#South East Asia
		x = 17*self.mapWidth/20
		y = 4*self.mapHeight/7
		self.plateMap[x + y*self.mapWidth] = 16
		self.plateSize[16] = 3
		self.plate[16] = self.landAltitude
		#Greenland
		x = 3*self.mapWidth/10
		y = 7*self.mapHeight/8
		self.plateMap[x + y*self.mapWidth] = 17
		self.plateSize[17] = 4
		#Scandinavia
		x = 3*self.mapWidth/7 -1
		y = 7*self.mapHeight/8
		self.plateMap[x + y*self.mapWidth] = 18
		self.plateSize[18] = 3
		self.plate[18] = self.landAltitude
		#Bering
		x = 9*self.mapWidth/10
		y = 5*self.mapHeight/6
		self.plateMap[x + y*self.mapWidth] = 19
		self.plateSize[19] = 5

	def finalizeMap(self):
		#Force Gibraltar straits
		x = 4*self.mapWidth/9
		y = 3*self.mapHeight/4
		for i in range(self.mapWidth/5):
			self.plotTypes[x + y*self.mapWidth - i] = PlotTypes.PLOT_OCEAN
		#Force cut between India and Oceania
		x = 7*self.mapWidth/10
		y = 4*self.mapHeight/9 -1
		for i in range(self.mapWidth/5):
			self.plotTypes[x + y*self.mapWidth + i] = PlotTypes.PLOT_OCEAN
		#Force Greenland to be an island
		for x in range(self.mapWidth):
			for y in range(self.mapHeight):
				if (self.plateMap[x + y*self.mapWidth] == 17):
					if (self.plateMap[x-1 + y*self.mapWidth] != 17):
						self.plotTypes[x + y*self.mapWidth] = PlotTypes.PLOT_OCEAN
						self.plotTypes[x + (y-1)*self.mapWidth] = PlotTypes.PLOT_OCEAN
		#Force Arabia
		for x in range(self.mapWidth):
			for y in range(self.mapHeight):
				if self.plateMap[x + y*self.mapWidth] == 15:
					if self.plateMap[x + (y-1)*self.mapWidth] != 15:
						self.plotTypes[x + y*self.mapWidth] = PlotTypes.PLOT_OCEAN
						self.plotTypes[x + (y-1)*self.mapWidth] = PlotTypes.PLOT_OCEAN
					if self.plateMap[x+1 + y*self.mapWidth] != 15:
						self.plotTypes[x + y*self.mapWidth] = PlotTypes.PLOT_OCEAN
						self.plotTypes[x+1 + y*self.mapWidth] = PlotTypes.PLOT_OCEAN
		#Force Central America
		baseX = self.mapWidth/6
		x = baseX
		width = 2
		if (self.dice.get(10,"Width variation") > 8):
			width += 1
		if (width > 1 and self.dice.get(10,"Width variation") > 8):
			width -= 1
		for y in range(self.mapHeight/5,self.mapHeight*3/4):
			x = x + self.dice.get(3,"Not too straight") - 1
			if ( x - baseX > 4):
				x = baseX + 4
			if ( x - baseX < -4):
				x = baseX - 4
			if (self.plotTypes[x + y*self.mapWidth ] == PlotTypes.PLOT_OCEAN):
				for plot in range( width ):
					self.plotTypes[x + y*self.mapWidth + plot ] = PlotTypes.PLOT_LAND
					if (self.dice.get(10,"Some hills") > 5):
						self.plotTypes[x + y*self.mapWidth + plot ] = PlotTypes.PLOT_HILLS

	def movePlates(self,dontMoveSeaPlates):
		plates = self.numContinents + self.numSeaPlates
		if dontMoveSeaPlates:
			xMoves =     [0, 1, 0, 0, 0, 0, 0, 0,  -1,-1, 0,-1, 0, 0,-1, 0,-1, 1, 1, 0, 0]
			yMoves =     [0, 0, 0, 0,-1, 1, 1, 0,   0, 1,-1,-1, 0, 1, 0, 0, 0, 1, 0, 0, 0]
			subduction = [0, 9, 9, 0, 9, 0, 0, 0,   9, 9, 9, 0, 0, 9, 9, 9, 0, 9, 9, 0, 0]
		else:
			xMoves =     [0, 1, 0, 0, 0, 1,-1, 0,  -1,-1, 0, 1, 1,-1, 1, 0, 0,-1,-1, 1,-1]
			yMoves =     [0, 0, 0, 0, 1,-1, 0, 0,  -1, 1,-1,-1, 1,-1,-1,-1,-1,-1, 0, 1, 1]
			subduction = [0, 9, 9, 0, 9, 9, 9, 0,   9, 9, 9, 9, 0, 9, 9, 9, 0, 0, 9, 0, 0]
		self.doMovePlates(xMoves,yMoves,subduction)

class voronoiPangaeaMap(voronoiMap):
	def __init__(self,numPlayers):
		voronoiMap.__init__(self,numPlayers,1,1600)
		self.peakAltitude = 11
		self.hillAltitude = 7
		self.landAltitude = 3
		self.altitudeVariation = 3

	def sowSeeds(self):
		self.yTilt = self.dice.get(4,"YTilt")
		self.plate[0] = 0
		self.plate[1] = 0
		for x in range(self.mapWidth):
			self.plateMap[x] = 1
			self.plateMap[self.mapWidth + x] = 1
			self.plateMap[(self.mapHeight - 2)*self.mapWidth + x] = 1
			self.plateMap[(self.mapHeight - 1)*self.mapWidth + x] = 1
		for y in range(self.mapHeight):
			self.plateMap[y*self.mapWidth] = 1
			self.plateMap[y*self.mapWidth + 1] = 1
			self.plateMap[y*self.mapWidth + self.mapWidth - 2] = 1
			self.plateMap[y*self.mapWidth + self.mapWidth - 1] = 1
		for i in range(self.numContinents):
			self.plate[i + self.numSeaPlates] = 4 + self.dice.get(3,"Land altitude")
			x, y = self.getCoord(i)
			while self.plateMap[y*self.mapWidth + x] != 0:
				x, y = self.getCoord(i)
			self.plateMap[y*self.mapWidth + x] = i + 2

	def getCoord(self,i):
		step = self.mapWidth/(2*self.numContinents)
		x = self.mapWidth/4 + i*step + self.dice.get(step,"x seed for plate")
		quarterHeight = self.mapHeight/4 
		eigthHeight = self.mapHeight/8 
		y = quarterHeight + self.dice.get(self.mapHeight/2,"y seed for plate")
		if (self.yTilt == 0):
			y += i*(self.mapHeight/(self.numContinents*4)) - eigthHeight
		elif (self.yTilt == 1):
			y += eigthHeight - i*quarterHeight/self.numContinents
		elif (self.yTilt == 2):
			if (i%2 == 0):
				y += eigthHeight
			else:
				y -= eigthHeight
		# else: Let it be the way it was generated
		return x, y

class ClimateGenerator:
	def __init__(self):
		self.climate = CyMap().getCustomMapOption(1)
		gc = CyGlobalContext()
		self.map = gc.getMap()
		self.mapWidth = self.map.getGridWidth()
		if (self.climate == 0):                          # Arid
			self.maxWindForce = self.mapWidth / 12
		elif (self.climate == 1):                        # Normal
			self.maxWindForce = self.mapWidth / 8
		elif (self.climate == 2):                        # Wet
			self.maxWindForce = self.mapWidth / 6
		elif (self.climate == 3):                        # No ice
			self.maxWindForce = self.mapWidth / 8
		self.mapHeight = self.map.getGridHeight()
		self.terrainDesert = gc.getInfoTypeForString("TERRAIN_DESERT")
		self.terrainPlains = gc.getInfoTypeForString("TERRAIN_PLAINS")
		self.terrainIce = gc.getInfoTypeForString("TERRAIN_SNOW")
		self.terrainTundra = gc.getInfoTypeForString("TERRAIN_TUNDRA")
		self.terrainGrass = gc.getInfoTypeForString("TERRAIN_GRASS")
		if (self.climate == 3):                        # No ice
			self.terrainIce = gc.getInfoTypeForString("TERRAIN_TUNDRA")
			self.terrainTundra = gc.getInfoTypeForString("TERRAIN_GRASS")
		self.terrain = [0] * (self.mapWidth*self.mapHeight)
		self.moisture = [0] * (self.mapWidth*self.mapHeight)
		self.dice = gc.getGame().getMapRand()

	def getLatitudeAtPlot(self, iX, iY):
		"returns a value in the range of 0-90 degrees"
		# advc.021a: was ...==5
		if (CyMap().getCustomMapOption(0) == 6):         #  "Mediterranean"
			return 65 - (40 * (self.mapHeight - iY) / self.mapHeight)
		return self.map.plot(iX,iY).getLatitude()

	def generateTerrain(self):
		self.blowWinds()
		self.blur()
		self.computeTerrain()
		return self.terrain

	def computeTerrain(self):
		terrain = [0] * (self.mapWidth*self.mapHeight)
		for x in range(self.mapWidth):
			for y in range(self.mapHeight):
				if (self.map.plot(x,y).isWater()):
					self.terrain[y*self.mapWidth+x] = self.map.plot(x,y).getTerrainType()
				else:
					terrain[y*self.mapWidth+x] = self.getTerrain(self.getLatitudeAtPlot(x,y),self.moisture[y*self.mapWidth + x])
		for x in range(self.mapWidth):
			for y in range(self.mapHeight):
				if (not self.map.plot(x,y).isWater()):
					i = y*self.mapWidth+x
					self.terrain[i] = terrain[i]
					bias = self.dice.get(3,"Random terrain")
					if bias == 0 and y > 1:
						self.terrain[i] = terrain[i-self.mapWidth]
					if bias == 2 and y < self.mapHeight - 1:
						self.terrain[i] = terrain[i+self.mapWidth]
		for x in range(self.mapWidth):
			for y in range(self.mapHeight):
				if (not self.map.plot(x,y).isWater()):
					i = y*self.mapWidth+x
					if self.terrain[i] == self.terrainDesert:
						if y > 1 and y < self.mapHeight - 1:
							if self.terrain[i-self.mapWidth] == self.terrainGrass:
								self.terrain[i-self.mapWidth] = self.terrainPlains
							if self.terrain[i+self.mapWidth] == self.terrainGrass:
								self.terrain[i+self.mapWidth] = self.terrainPlains
							if self.terrain[i-1] == self.terrainGrass:
								self.terrain[i-1] = self.terrainPlains
							if self.terrain[i+1] == self.terrainGrass:
								self.terrain[i+1] = self.terrainPlains
					
	def getArcticTerrain(self, climate, latitude, moisture):
		polar = 0
		if (latitude > 70):
			polar = latitude - 70
			climate.ice += polar * polar * 3
			climate.tundra += polar * (2 + moisture)

	def getColdTerrain(self, climate, latitude, moisture):
		if (latitude > 60):
			polar = latitude - 60
			climate.tundra += polar * (5 + moisture) + self.dice.get(polar*3,"more tundra")
			if (moisture > 10):
				climate.plains += polar * (moisture - 10)

	def getTemperateTerrain(self, climate, latitude, moisture):
		temperate = 45 - abs(45 - latitude)
		climate.plains += temperate * (3 + moisture/2)
		climate.grass += temperate * (1 + moisture) + self.dice.get(temperate,"more grass")

	def getTropicalTerrain(self, climate, latitude, moisture):
		tropical = 0
		if (latitude < 40):
			tropical = 20 - abs(20 - latitude)
		climate.plains += tropical * (12 - self.climate + moisture/2) + self.dice.get(tropical,"more plains")
		climate.grass += tropical * (moisture + self.climate)
		climate.desert += tropical * (4 - self.climate) * 6

	def getEquatorialTerrain(self, climate, latitude, moisture):
		equator = 0
		if (latitude < 25):
			equator = 25 - latitude
		climate.plains += equator * 7
		climate.grass += equator * (3 + moisture) + self.dice.get(equator,"more grass")

	#I compute latitude as in the maputil but wtf is there a plot.latitude then?
	def getTerrain(self, latitude, moisture):
		class climates:
			def __init__(self):
				self.ice = 0
				self.tundra = 0
				self.plains = 0
				self.grass = 0
				self.desert = 0

		climate = climates()
		self.getArcticTerrain(climate, latitude, moisture)
		self.getColdTerrain(climate, latitude, moisture)
		self.getTemperateTerrain(climate, latitude, moisture)
		self.getTropicalTerrain(climate, latitude, moisture)
		self.getEquatorialTerrain(climate, latitude, moisture)

		if (climate.ice >= climate.tundra) and (climate.ice >= climate.plains) and (climate.ice >= climate.grass) and (climate.ice >= climate.desert):
			return self.terrainIce
		if (climate.tundra >= climate.plains) and (climate.tundra >= climate.grass) and (climate.tundra >= climate.desert):
			return self.terrainTundra
		if (climate.plains >= climate.grass) and (climate.plains >= climate.desert):
			return self.terrainPlains
		if (climate.grass >= climate.desert):
			return self.terrainGrass
		return self.terrainDesert

	def blowWinds(self):
	#Must find where the wind blows from and add moisture from there.
	#If there is a mountain in between, then terrain must become more arid:
	# Tundra -> ice (mmmh?), and grass -> plain -> desert.
		for x in range(self.mapWidth):
			for y in range(self.mapHeight):
				if (self.map.plot(x,y).isWater()):
					self.windBlowsFrom(x,y)

	def windBlowsFrom(self,x,y):
		latitude = self.getLatitudeAtPlot(x,y)
		horizontal = 0
		if (latitude > 80):
			horizontal = 1
		elif (latitude > 45):
			horizontal = -1
		elif (latitude > 30):
			horizontal = 1
		elif (latitude > 10):
			horizontal = -1
		else:
			horizontal = 1
		vertical = self.getVerticalWind(latitude,y)
		windForce = 1 + self.dice.get(self.maxWindForce,"Wind force")
		localMoisture = 5 + self.maxWindForce
		self.blow(localMoisture,windForce,horizontal,vertical,x,y)

	def getVerticalWind(self,latitude,y):
		if (latitude>70):
			vertical = -1
		elif (latitude>30):
			vertical = 1
		else:
			vertical = -1
		if (2*y < self.mapHeight):
			vertical *= -1
		return vertical

	def blow(self,localMoisture,maxHorizontal,horizontal,vertical,x,y):
		plotType = self.map.plot(x,y).getPlotType()
		if (y+vertical > 0 and y+vertical < self.mapHeight):
			if (plotType != PlotTypes.PLOT_PEAK):
				if (plotType == PlotTypes.PLOT_HILLS):
					self.blow(localMoisture - 7,maxHorizontal-2,horizontal,vertical,x,y+vertical)
				else:
					self.blow(localMoisture - 1,maxHorizontal-2,horizontal,vertical,x,y+vertical)
		for i in range(-1,maxHorizontal):
			adjustedX = x + i*horizontal
			if (adjustedX < 0):
				adjustedX += self.mapWidth
			elif (adjustedX >= self.mapWidth):
				adjustedX -= self.mapWidth
			self.moisture[y*self.mapWidth + adjustedX] = self.moisture[y*self.mapWidth + adjustedX] + localMoisture
			plotType = self.map.plot(adjustedX,y).getPlotType()
			if (plotType == PlotTypes.PLOT_PEAK):
				return
			elif (plotType == PlotTypes.PLOT_HILLS):
				localMoisture -= 7
			else:
				localMoisture -= 1
			if (localMoisture <= 0):
				return

	def blur(self):
		max = 1
		for y in range(self.mapHeight):
			for x in range(self.mapWidth):
				i = y*self.mapWidth + x
				if (max < self.moisture[i]):
					max = self.moisture[i]
		for y in range(1,self.mapHeight-2):
			for x in range(self.mapWidth):
				i = y*self.mapWidth + x
				self.moisture[i] = self.moisture[i]*100/max

#
# Main terrain generation fonction
#
def generatePlotTypes():
	"Generates a map with several continents and a few islands."
	userInputLandmass = CyMap().getCustomMapOption(0)
	gc = CyGlobalContext()
	numPlayers = gc.getGame().countCivPlayersEverAlive()
	surface = gc.getMap().getGridWidth() * gc.getMap().getGridHeight()
	numPlayers = (numPlayers + surface / 400) / 2
	numContinents = 1
	numSeaPlates = 1
	hotspotsFrequency = 900
	if (userInputLandmass == 0):       # "Earthlike (70% water)"
		numContinents = 1 + numPlayers
		numSeaPlates = numPlayers*3
	elif (userInputLandmass == 1):       # "Earthlike (60% water)"
		numContinents = 1 + numPlayers*2
		numSeaPlates = numPlayers*3 - 1
	# advc.021a: Added this block and pushed all subsequent ids one down
	elif (userInputLandmass == 2):       # "Earthlike (50% water)"
		numContinents = 1 + numPlayers*2
		numSeaPlates = 2 + numPlayers*2
	elif (userInputLandmass == 3):     # "Pangaea"
		generator = voronoiPangaeaMap(numPlayers)
		return generator.generate()
	elif (userInputLandmass == 4):     # "Lakes (30% water")
		numContinents = 1 + numPlayers*3
		numSeaPlates = numPlayers - 1
		hotspotsFrequency = 1600
	elif (userInputLandmass == 5):     # "Islands"
		numContinents = numPlayers
		numSeaPlates = numPlayers*6 - 1
		hotspotsFrequency = 300
	elif (userInputLandmass == 6):     #  "Mediterranean"
		generator = voronoiMediterraneanMap(numPlayers)
		return generator.generate()
	elif (userInputLandmass == 7 or userInputLandmass == 8): # "Terra"
		generator = voronoiTerraMap()
		return generator.generate()
	width = gc.getMap().getGridWidth()
	generator = voronoiMap(numContinents,numSeaPlates,hotspotsFrequency)
	return generator.generate()

#Rivers map second try...
class riversMap:
	def __init__(self):
		self.gc = CyGlobalContext()
		self.dice = self.gc.getGame().getMapRand()
		self.map = CyMap()
		self.mapWidth = self.map.getGridWidth()
		self.mapHeight = self.map.getGridHeight()
		self.file = open( "d:\\tmp\\toto.txt", 'w' )
		self.generateHeightMap()

	def initHeightMap(self,currentLands):
		#initialize with high altitudes on peaks and hills
		for x in range(self.mapWidth):
			for y in range(self.mapHeight):
				plot = self.map.plot(x,y)
				if (plot.getPlotType() == PlotTypes.PLOT_PEAK):
					currentLands[x + y*self.mapWidth]  = 1
					self.heightMap[x + y*self.mapWidth]  = 10000
				elif (plot.getPlotType() == PlotTypes.PLOT_HILLS):
					currentLands[x + y*self.mapWidth]  = 1
					self.heightMap[x + y*self.mapWidth]  = 1000
				elif (plot.getPlotType() == PlotTypes.PLOT_LAND):
					currentLands[x + y*self.mapWidth]  = 1
					self.heightMap[x + y*self.mapWidth]  = 1

	def generateHeightMap(self):
		self.heightMap = [0] * (self.mapWidth*self.mapHeight)
		currentLands = [0] * (self.mapWidth*self.mapHeight)
		self.initHeightMap(currentLands)
		finished = false
		#make sure there's a slope towards seas and lakes
		while not finished:
			finished = true
			buffer = [1] * (self.mapWidth*self.mapHeight)
			for x in range(self.mapWidth):
				for y in range(self.mapHeight):
					plot = x + y*self.mapWidth
					if currentLands[plot] == 0:
						buffer[plot] = 0
						for i in self.neighbours(x, y):
							buffer[i] = 0
			for x in range(self.mapWidth):
				for y in range(self.mapHeight):
					plot = x + y*self.mapWidth
					currentLands[plot] = buffer[plot]
					if buffer[plot] == 1:
						finished = false
						self.heightMap[plot] = 1 + self.heightMap[plot]
		#make sure there's a slope going downwards away from mountains
		for i in range(20):
			increase = []
			for x in range(self.mapWidth):
				for y in range(self.mapHeight):
					if self.heightMap[x + y*self.mapWidth] > 20 - i:
						for j in self.neighbours(x, y):
							increase.append(j)
			for plot in increase:
				self.heightMap[plot] = self.heightMap[plot] + 2
		for y in range(self.mapHeight):
			for x in range(self.mapWidth):
				plot = x + y*self.mapWidth
				self.file.write( str( self.heightMap[plot] ) + "\t" )
			self.file.write( "\n" )

	def neighbours(self, x, y):
		result = []
		if x == 0:
			result.append(y*self.mapWidth)
		else:
			result.append(x-1 + y*self.mapWidth)
		if x == self.mapWidth - 1:
			result.append(y*self.mapWidth)
		else:
			result.append(x+1 + y*self.mapWidth)
		if y > 0:
			result.append(x + (y-1)*self.mapWidth)
		if y < self.mapHeight - 1:
			result.append(x + (y+1)*self.mapWidth)
		return result

	def seedRivers(self):
		climate = CyMap().getCustomMapOption(1)
		if (climate == 0):                 # Arid
			divider = 6
		elif (climate == 1):               # Normal
			divider = 3
		elif (climate == 2):               # Wet
			divider = 2
		elif (climate == 3):               # No ice
			divider = 3
		probability = 30/divider
		seeds = []
		for x in range(self.mapWidth):
			for y in range(self.mapHeight):
				plot = self.map.plot(x,y)
				if (plot.getPlotType() == PlotTypes.PLOT_HILLS):
					if self.dice.get(100,"Start river") < probability:
						seeds.append( plot )
				elif (plot.getPlotType() == PlotTypes.PLOT_LAND):
					if self.dice.get(1000,"Start river in flatland") < probability + self.heightMap[x + y*self.mapWidth]:
						seeds.append( plot )
		for plot in seeds:
			riverID = self.gc.getMap().getNextRiverID()
			self.startRiver(riverID, plot)
		self.file.close()

	def startRiver(self, riverID, plot):
		if plot.isWater():
			return true
		x = plot.getX()
		y = plot.getY()
		height = self.heightMap[x + y * self.mapWidth]
		ns = self.checkNorthSouth(x, y, height)
		ew = self.checkEastWest(x, y, height)
		if ns == CardinalDirectionTypes.NO_CARDINALDIRECTION and ew == CardinalDirectionTypes.NO_CARDINALDIRECTION:
			self.file.write( "End river false\n" )
			return false
		self.file.write( "Will flow\n" )
		if ns != CardinalDirectionTypes.NO_CARDINALDIRECTION and ew != CardinalDirectionTypes.NO_CARDINALDIRECTION:
			if self.dice.get(self.mapHeight + self.mapWidth,"direction") < self.mapHeight:
				self.flow(riverID, plot, ns)
			else:
				self.flow(riverID, plot, ew)
		elif ns != CardinalDirectionTypes.NO_CARDINALDIRECTION:
			self.flow(riverID, plot, ns)
		elif ew != CardinalDirectionTypes.NO_CARDINALDIRECTION:
			self.flow(riverID, plot, ew)
		self.file.write( "End river true\n" )
		return true

	#checks for isWOfRiver
	def checkNorthSouth(self, x, y, height):
		if x == self.mapWidth - 1:
			delta = 1 - self.mapWidth
		else:
			delta = 1
		west = x + delta + y*self.mapWidth
		northSouthHeight = height + self.heightMap[west]
		result = CardinalDirectionTypes.NO_CARDINALDIRECTION
		plot = self.map.plot(x,y)
		if plot.isWOfRiver():
			return result
		if y > 0:
			nHeight = self.heightMap[x + (y-1)*self.mapWidth] + self.heightMap[x + delta + (y-1)*self.mapWidth]
			self.file.write( " For " + str(x) + ", " + str(y) + ", heights: " + str(nHeight) + " <? " + str(northSouthHeight) + "\n" )
			if nHeight < northSouthHeight:
				result = CardinalDirectionTypes.CARDINALDIRECTION_SOUTH
		if y < self.mapHeight -1:
			sHeight = self.heightMap[x + (y-1)*self.mapWidth] + self.heightMap[x + delta + (y-1)*self.mapWidth]
			self.file.write( " For " + str(x) + ", " + str(y) + ", heights: " + str(sHeight) + " <? " + str(northSouthHeight) + "\n" )
			if sHeight < northSouthHeight:
				if result == CardinalDirectionTypes.NO_CARDINALDIRECTION or sHeight < nHeight:
					result = CardinalDirectionTypes.CARDINALDIRECTION_NORTH
		return result

	#checks for isNOfRiver
	def checkEastWest(self, x, y, height):
		result = CardinalDirectionTypes.NO_CARDINALDIRECTION
		plot = self.map.plot(x,y)
		if plot.isNOfRiver():
			return result
		if y < self.mapHeight -1:
			south = x + (y+1)*self.mapWidth
			eastWestHeight = height + self.heightMap[south]
			if x == self.mapWidth - 1:
				west = y*self.mapWidth
				swest = (y+1)*self.mapWidth
			else:
				west = x + 1 + y*self.mapWidth
				swest = x + 1 + (y+1)*self.mapWidth
			wHeight = self.heightMap[west] + self.heightMap[swest] 
			self.file.write( " For " + str(x) + ", " + str(y) + ", heights: " + str(wHeight) + " <? " + str(eastWestHeight) + "\n" )
			if wHeight < eastWestHeight:
				result = CardinalDirectionTypes.CARDINALDIRECTION_WEST
			if x == 0:
				east = y*self.mapWidth
				seast = (y+1)*self.mapWidth
			else:
				east = x - 1 + y*self.mapWidth
				seast = x - 1 + (y+1)*self.mapWidth
			eHeight = self.heightMap[east] + self.heightMap[seast] 
			self.file.write( " For " + str(x) + ", " + str(y) + ", heights: " + str(eHeight) + " <? " + str(eastWestHeight) + "\n" )
			if eHeight < eastWestHeight:
				if result == CardinalDirectionTypes.NO_CARDINALDIRECTION or eHeight < wHeight:
					result = CardinalDirectionTypes.CARDINALDIRECTION_EAST
		return result

	def joins(self, riverPlot, riverID):
		return (riverPlot.isWOfRiver() or riverPlot.isNOfRiver()) and riverPlot.getRiverID() != riverID

	def flow(self, riverID, plot, direction):
		x = plot.getX()
		y = plot.getY()
		self.file.write( "Flow to " + str(x) + ", " + str(y) + "\n" )
		if direction == CardinalDirectionTypes.CARDINALDIRECTION_EAST:
			if x < self.mapWidth - 1:
				riverPlot = self.map.plot(x+1,y)
				if y == self.mapHeight - 1 or self.map.plot(x+1,y+1).isWater() or riverPlot.isWater():
					return
			else:
				riverPlot = self.map.plot(0,y)
				if y == self.mapHeight - 1 or self.map.plot(0,y+1).isWater() or riverPlot.isWater():
					return
			joinRiver = self.joins(riverPlot, riverID)
			riverPlot.setNOfRiver(True,direction)
		if direction == CardinalDirectionTypes.CARDINALDIRECTION_WEST:
			if x > 0:
				riverPlot = self.map.plot(x-1,y)
				if y == self.mapHeight - 1 or self.map.plot(x-1,y+1).isWater() or riverPlot.isWater():
					return
			else:
				riverPlot = self.map.plot(self.mapWidth-1,y)
				if y == self.mapHeight - 1 or self.map.plot(self.mapWidth-1,y+1).isWater() or riverPlot.isWater():
					return
			joinRiver = self.joins(riverPlot, riverID)
			riverPlot.setNOfRiver(True,direction)
		if direction == CardinalDirectionTypes.CARDINALDIRECTION_NORTH:
			riverPlot = self.map.plot(x,y-1)
			if ( x == self.mapWidth - 1 and self.map.plot(0,y).isWater() ) or ( x < self.mapWidth - 1 and self.map.plot(x+1,y).isWater() ) or riverPlot.isWater():
				return
			joinRiver = self.joins(riverPlot, riverID)
			riverPlot.setWOfRiver(True,direction)
		if direction == CardinalDirectionTypes.CARDINALDIRECTION_SOUTH:
			riverPlot = self.map.plot(x,y+1)
			if ( x == self.mapWidth - 1 and self.map.plot(0,y).isWater() ) or ( x < self.mapWidth - 1 and self.map.plot(x+1,y).isWater() ) or riverPlot.isWater():
				return
			joinRiver = self.joins(riverPlot, riverID)
			riverPlot.setWOfRiver(True,direction)
		if joinRiver:
			self.file.write( "Joining rivers\n" )
			return
		riverPlot.setRiverID(riverID)
		self.startRiver(riverID,riverPlot)
		#if not self.startRiver(riverID,riverPlot):
			#self.file.write( "Add ocean in " + str(riverPlot.getX()) + ", " + str(riverPlot.getY()) + "\n" )
			#riverPlot.setPlotType(PlotTypes.PLOT_OCEAN,true,true)

# This whole class is needlessly complex. It would be better to rewrite it by first defining
# a new map, which is the map of the places between squares, giving them an altitude which would be the max
# of the surrounding squares. This would simplify this a lot but I'm too lazy for now to rewrite all.
class riversFromSea:
	def __init__(self):
		self.gc = CyGlobalContext()
		self.dice = self.gc.getGame().getMapRand()
		self.map = CyMap()
		self.width = self.map.getGridWidth()
		self.height = self.map.getGridHeight()
		self.straightThreshold = 4
		self.riverLength = {}
		self.riverTurns = {}
		self.minRiverLength = self.height/6
		if (self.width * self.height > 400):
			self.straightThreshold = 3

	def seedRivers(self):
		climate = CyMap().getCustomMapOption(1)
		if (climate == 0):                 # Arid
			divider = 4
		elif (climate == 1):               # Normal
			divider = 2
		elif (climate == 2):               # Wet
			divider = 1
		elif (climate == 3):               # No ice
			divider = 2
		maxNumber = (self.width + self.height) / divider
		userInputLandmass = self.map.getCustomMapOption(0)
		# <advc.021a> ==1 isn't Pangaea, should've been 2 (bug); with
		# the 50% option added, it should now be 3.
		# However: Too many rivers in 3.16 in general, so
		# let's always reduce their number.
		if (userInputLandmass == 3):       # Pangaea
			maxNumber /= 2.5 # was riversNumber=maxNumber/2
		else:
			maxNumber /= 2
		# Moved down; guaranteeing at least 1 river sounds prudent
		riversNumber = int(1 + maxNumber)
		# </advc.021a>
		self.coasts = self.collateCoasts()
		coastsNumber = len(self.coasts)
		if (coastsNumber == 0):
			return
		coastShare = coastsNumber/riversNumber
		for i in range(riversNumber):
			flow = CardinalDirectionTypes.NO_CARDINALDIRECTION
			tries = 0
			while flow == CardinalDirectionTypes.NO_CARDINALDIRECTION and tries < 6:
				tries = tries + 1
				(x,y,flow) = self.generateRiver(i,coastShare)
			if flow != CardinalDirectionTypes.NO_CARDINALDIRECTION:
				riverID = self.gc.getMap().getNextRiverID()
				self.riverLength[riverID] = 0
				self.riverTurns[riverID] = 0
				self.addRiverFrom(x,y,flow,riverID)

	def collateCoasts(self):
		result = []
		for x in range(self.width):
			for y in range(self.height):
				plot = self.map.plot(x,y)
				if (plot.isCoastalLand()):
					result.append(plot)
		return result

	def generateRiver(self,i,coastShare):
		choiceCoast = coastShare * i + self.dice.get(coastShare,"Pick a coast for the river")
		plot = self.coasts[choiceCoast]
		FlowDirection = CardinalDirectionTypes.NO_CARDINALDIRECTION
		x = plot.getX()
		y = plot.getY()
		if ((y < 1 or y >= self.height - 1) or plot.isNOfRiver() or plot.isWOfRiver()):
			return (x,y,FlowDirection)
		eastX = self.eastX(x)
		westX = self.westX(x)
		otherPlot = True
		eastPlot = self.map.plot(eastX,y)
		if (eastPlot.isCoastalLand()):
			seaPlot = self.map.plot(x,y+1)
			if ((self.map.plot(x,y+1).isWater()) or (self.map.plot(eastX,y+1).isWater())):
				landPlot1 = self.map.plot(x,y-1)
				landPlot2 = self.map.plot(eastX,y-1)
				if (landPlot1.isWater() or landPlot2.isWater()):
					otherPlot = True
				else:
					FlowDirection = CardinalDirectionTypes.CARDINALDIRECTION_NORTH
					otherPlot = False
			if (otherPlot == True):
				if ((self.map.plot(x,y-1).isWater()) or (self.map.plot(eastX,y-1).isWater())):
					landPlot1 = self.map.plot(x,y+1)
					landPlot2 = self.map.plot(eastX,y+1)
					if (landPlot1.isWater() or landPlot2.isWater()):
						otherPlot = True
					else:
						FlowDirection = CardinalDirectionTypes.CARDINALDIRECTION_SOUTH
						otherPlot = False
		if (otherPlot == True):
			southPlot = self.map.plot(x,y-1)
			if (southPlot.isCoastalLand()):
				if ((self.map.plot(eastX,y).isWater()) or (self.map.plot(eastX,y-1).isWater())):
					landPlot1 = self.map.plot(westX,y)
					landPlot2 = self.map.plot(westX,y-1)
					if (landPlot1.isWater() or landPlot2.isWater()):
						otherPlot = True
					else:
						FlowDirection = CardinalDirectionTypes.CARDINALDIRECTION_EAST
						otherPlot = False
				if (otherPlot == True):
					if ((self.map.plot(westX,y).isWater()) or (self.map.plot(westX,y-1).isWater())):
						landPlot1 = self.map.plot(eastX,y)
						landPlot2 = self.map.plot(eastX,y-1)
						if (landPlot1.isWater() or landPlot2.isWater()):
							otherPlot = True
						else:
							FlowDirection = CardinalDirectionTypes.CARDINALDIRECTION_WEST
		return (x,y,FlowDirection)

	# prevent rivers from crossing each other
	def preventRiversFromCrossing(self,x,y,flow,riverID):
		plot = self.map.plot(x,y)
		eastX = self.eastX(x)
		westX = self.westX(x)
		if (flow == CardinalDirectionTypes.CARDINALDIRECTION_WEST):
			if (plot.isNOfRiver()):
				return true
			if (self.map.plot(eastX,y).isNOfRiver()):
				return true
			southPlot = self.map.plot(x,y-1)
			if (southPlot.isWOfRiver() and southPlot.getRiverNSDirection() == CardinalDirectionTypes.CARDINALDIRECTION_SOUTH):
				return true
			if (plot.isWOfRiver() and plot.getRiverNSDirection() == CardinalDirectionTypes.CARDINALDIRECTION_NORTH):
				return true
			if (self.map.plot(eastX,y).isWater()):
				return true
			if (self.map.plot(x,y-1).isWater()):
				return true
			if (self.map.plot(eastX,y-1).isWater()):
				return true
		if (flow == CardinalDirectionTypes.CARDINALDIRECTION_EAST):
			if (plot.isNOfRiver()):
				return true
			if (self.map.plot(westX,y).isNOfRiver()):
				return true
			southPlot = self.map.plot(westX,y-1)
			if (southPlot.isWOfRiver() and southPlot.getRiverNSDirection() == CardinalDirectionTypes.CARDINALDIRECTION_SOUTH):
				return true
			westPlot = self.map.plot(westX,y)
			if (westPlot.isWOfRiver() and westPlot.getRiverNSDirection() == CardinalDirectionTypes.CARDINALDIRECTION_NORTH):
				return true
			if (self.map.plot(westX,y).isWater()):
				return true
			if (self.map.plot(x,y-1).isWater()):
				return true
			if (self.map.plot(westX,y-1).isWater()):
				return true
		if (flow == CardinalDirectionTypes.CARDINALDIRECTION_NORTH):
			if (plot.isWOfRiver()):
				return true
			eastPlot = self.map.plot(eastX,y)
			if (eastPlot.isNOfRiver() and eastPlot.getRiverWEDirection() == CardinalDirectionTypes.CARDINALDIRECTION_EAST):
				return true
			if (plot.isNOfRiver() and plot.getRiverWEDirection() == CardinalDirectionTypes.CARDINALDIRECTION_WEST):
				return true
			if (self.map.plot(x,y-1).isWOfRiver()):
				return true
			if (self.map.plot(x,y-1).isWater()):
				return true
			if (self.map.plot(x+1,y).isWater()):
				return true
			if (self.map.plot(x+1,y-1).isWater()):
				return true
		if (flow == CardinalDirectionTypes.CARDINALDIRECTION_SOUTH):
			if (plot.isWOfRiver()):
				return true
			eastPlot = self.map.plot(eastX,y+1)
			if (eastPlot.isNOfRiver() and eastPlot.getRiverWEDirection() == CardinalDirectionTypes.CARDINALDIRECTION_EAST):
				return true
			northPlot = self.map.plot(x,y+1)
			if (northPlot.isNOfRiver() and northPlot.getRiverWEDirection() == CardinalDirectionTypes.CARDINALDIRECTION_WEST):
				return true
			if (self.map.plot(x,y+1).isWOfRiver()):
				return true
			if (self.map.plot(x,y+1).isWater()):
				return true
			if (self.map.plot(x+1,y).isWater()):
				return true
			if (self.map.plot(x+1,y+1).isWater()):
				return true
		return false


	def addRiverFrom(self,x,y,flow,riverID):
		plot = self.map.plot(x,y)
		if (plot.isWater()):
			return
		self.riverLength[riverID] = self.riverLength[riverID] + 1
		eastX = self.eastX(x)
		westX = self.westX(x)
		if (self.preventRiversFromCrossing(x,y,flow,riverID)):
			return
		plot.setRiverID(riverID)
		if ((flow == CardinalDirectionTypes.CARDINALDIRECTION_WEST) or (flow == CardinalDirectionTypes.CARDINALDIRECTION_EAST)):
			plot.setNOfRiver(True,flow)
		else:
			plot.setWOfRiver(True,flow)
		xShift = 0
		yShift = 0
		if (flow == CardinalDirectionTypes.CARDINALDIRECTION_WEST):
			xShift = 1
		if (flow == CardinalDirectionTypes.CARDINALDIRECTION_EAST):
			xShift = -1
		if (flow == CardinalDirectionTypes.CARDINALDIRECTION_NORTH):
			yShift = -1
		if (flow == CardinalDirectionTypes.CARDINALDIRECTION_SOUTH):
			yShift = 1
		nextX = x + xShift
		nextY = y + yShift
		if (nextX >= self.width):
			nextX = 0
		if (nextY >= self.height):
			return
		nextI = nextY*self.width + nextX
		if (self.canFlowFrom(plot,self.map.plot(nextX,nextY)) == False):
			return
		if (plot.getTerrainType() == CyGlobalContext().getInfoTypeForString("TERRAIN_SNOW") and self.dice.get(10,"Stop on ice") > 3):
			return
		flatDesert = (plot.getPlotType() == PlotTypes.PLOT_LAND) and (plot.getTerrainType() == CyGlobalContext().getInfoTypeForString("TERRAIN_DESERT"))
		#Prevent Uturns in rivers
		turnThreshold = 13
		if flatDesert:
			turnThreshold = 17
		turned = False
		northY = y + 1
		southY = y - 1
		if ((flow == CardinalDirectionTypes.CARDINALDIRECTION_WEST) or (flow == CardinalDirectionTypes.CARDINALDIRECTION_EAST)):
			if ((northY < self.height) and (self.dice.get(20,"branch from north") > turnThreshold)):
				nextI = northY*self.width + x
				if (self.canFlowFrom(plot,self.map.plot(x,northY)) and self.canFlowFrom(self.map.plot(self.eastX(x),y),self.map.plot(self.eastX(x),northY))):
					turned = True
					self.riverTurns[riverID] = self.riverTurns[riverID] + 1
					if (flow == CardinalDirectionTypes.CARDINALDIRECTION_WEST):
						self.addRiverFrom(x,y,CardinalDirectionTypes.CARDINALDIRECTION_SOUTH,riverID)
					else:
						westPlot = self.map.plot(westX,y)
						westPlot.setRiverID(riverID)
						self.addRiverFrom(westX,y,CardinalDirectionTypes.CARDINALDIRECTION_SOUTH,riverID)
			if ((not turned) and (southY >= 0) and (self.dice.get(20,"branch from south") > turnThreshold)):
				nextI = southY*self.width + x
				if (self.canFlowFrom(plot,self.map.plot(x,southY)) and self.canFlowFrom(self.map.plot(self.eastX(x),y),self.map.plot(self.eastX(x),southY))):
					turned = True
					self.riverTurns[riverID] = self.riverTurns[riverID] + 1
					if (flow == CardinalDirectionTypes.CARDINALDIRECTION_WEST):
						southPlot = self.map.plot(x,y-1)
						southPlot.setRiverID(riverID)
						self.addRiverFrom(x,southY,CardinalDirectionTypes.CARDINALDIRECTION_NORTH,riverID)
					else:
						westPlot = self.map.plot(westX,southY)
						westPlot.setRiverID(riverID)
						self.addRiverFrom(westX,southY,CardinalDirectionTypes.CARDINALDIRECTION_NORTH,riverID)
		else:
			nextI = y*self.width + eastX
			if (self.canFlowFrom(plot,self.map.plot(eastX,y)) and self.canFlowFrom(self.map.plot(x,southY),self.map.plot(eastX,y)) and (self.dice.get(20,"branch from east") > turnThreshold)):
				turned = True
				self.riverTurns[riverID] = self.riverTurns[riverID] + 1
				if (flow == CardinalDirectionTypes.CARDINALDIRECTION_NORTH):
					eastPlot = self.map.plot(eastX,y)
					eastPlot.setRiverID(riverID)
					self.addRiverFrom(eastX,y,CardinalDirectionTypes.CARDINALDIRECTION_WEST,riverID)
				else:
					northEastPlot = self.map.plot(eastX,y+1)
					northEastPlot.setRiverID(riverID)
					self.addRiverFrom(eastX,y+1,CardinalDirectionTypes.CARDINALDIRECTION_WEST,riverID)
			nextI = y*self.width + westX
			if ((not turned) and self.canFlowFrom(plot,self.map.plot(westX,y)) and self.canFlowFrom(self.map.plot(x,southY),self.map.plot(westX,southY)) and (self.dice.get(20,"branch from west") > turnThreshold)):
				turned = True
				if (flow == CardinalDirectionTypes.CARDINALDIRECTION_NORTH):
					self.addRiverFrom(x,y,CardinalDirectionTypes.CARDINALDIRECTION_EAST,riverID)
				else:
					northPlot = self.map.plot(x,y+1)
					northPlot.setRiverID(riverID)
					self.addRiverFrom(x,y+1,CardinalDirectionTypes.CARDINALDIRECTION_EAST,riverID)
		spawnInDesert = (not turned) and flatDesert
		if ((self.dice.get(10,"straight river") > self.straightThreshold) or spawnInDesert):
			if (not turned) or (self.riverTurns[riverID] * 5 < self.riverLength[riverID]):
				self.addRiverFrom(nextX,nextY,flow,riverID)
		else:
			if (not turned):
				if self.riverLength[riverID] < self.minRiverLength:
					self.addRiverFrom(nextX,nextY,flow,riverID)
				else:
					plot = self.map.plot(nextX,nextY)
					if ((plot.getPlotType() == PlotTypes.PLOT_LAND) and (self.dice.get(10,"Rivers start in hills") > 3)):
						plot.setPlotType(PlotTypes.PLOT_HILLS,true,true)
						if ((flow == CardinalDirectionTypes.CARDINALDIRECTION_WEST) or (flow == CardinalDirectionTypes.CARDINALDIRECTION_EAST)):
							if southY > 0:
								self.map.plot(nextX,southY).setPlotType(PlotTypes.PLOT_HILLS,true,true)
						else:
							self.map.plot(eastX,nextY).setPlotType(PlotTypes.PLOT_HILLS,true,true)

	def canFlowFrom(self,plot,upperPlot):
		if (plot.isWater()):
			return False
		if (plot.getPlotType() == PlotTypes.PLOT_PEAK):
			return False
		if (plot.getPlotType() == PlotTypes.PLOT_HILLS):
			if ((upperPlot.getPlotType() == PlotTypes.PLOT_HILLS) or (upperPlot.getPlotType() == PlotTypes.PLOT_PEAK)):
				return True
			else:
				return False
		if (plot.getPlotType() == PlotTypes.PLOT_LAND):
			if (upperPlot.isWater()):
				return False
		return True
	
	def westX(self,x):
		westX = x - 1
		if (westX < 0):
			westX = self.width
		return westX

	def eastX(self,x):
		eastX = x + 1
		if (eastX >= self.width):
			eastX = 0
		return eastX

def addRivers():
	#riverGenerator = riversMap()
	riverGenerator = riversFromSea()
	riverGenerator.seedRivers()

#
# Starting position generation.
#
def findStartingPlot(argsList):
	gc = CyGlobalContext()
	map = CyMap()
	map.recalculateAreas()
	dice = gc.getGame().getMapRand()
	iPlayers = gc.getGame().countCivPlayersEverAlive()
	areas = CvMapGeneratorUtil.getAreas()
	areaValue = {}

	if iPlayers < 2 or iPlayers > 18:
		bSuccessFlag = False
		CyPythonMgr().allowDefaultImpl()
		return

	allOnBest = false
	isolatedStarts = false
	userInputLandmass = CyMap().getCustomMapOption(0)
	# advc.021a: was ...==4 and ...==7
	if (userInputLandmass == 5):     #                 "Islands"
		isolatedStarts = true
	if (userInputLandmass == 8):     #                 "Terra"
		allOnBest = true

	for area in areas:
		if area.isWater(): continue 
		areaValue[area.getID()] = area.calculateTotalBestNatureYield() + area.getNumRiverEdges() + 2 * area.countCoastalLand() + 3 * area.countNumUniqueBonusTypes()

	# Shuffle players so the same player doesn't always get the first pick.
	player_list = []
	for plrCheckLoop in range(18):
		if CyGlobalContext().getPlayer(plrCheckLoop).isEverAlive():
			player_list.append(plrCheckLoop)
	shuffledPlayers = []
	for playerLoop in range(iPlayers):
		iChoosePlayer = dice.get(len(player_list), "Shuffling Players - Highlands PYTHON")
		shuffledPlayers.append(player_list[iChoosePlayer])
		del player_list[iChoosePlayer]

	# advc.021a: Need to return sth. to avoid an exception in
	# CvPlayer::findStartingPlot
	r = -1
	
	# Loop through players, assigning starts for each.
	for assign_loop in range(iPlayers):
		playerID = shuffledPlayers[assign_loop]
		player = gc.getPlayer(playerID)
		if (allOnBest):
			def isValid(playerID, x, y):
				map = CyMap()
				pPlot = map.plot(x, y)
				if (pPlot.getArea() != map.findBiggestArea(False).getID()):
					return False
				return True
		else:
			bestAreaValue = 0
			global bestArea
			bestArea = -1
			for area in areas:
				if area.isWater(): continue 
				players = 2*area.getNumStartingPlots()
				#Avoid single players on landmasses:
				if (false == isolatedStarts and players == 0):
					if (assign_loop == iPlayers - 1):
						players = 4
					else:
						players = 2
				value = areaValue[area.getID()] / (1 + 2*players )
				if (value > bestAreaValue):
					bestAreaValue = value;
					bestArea = area.getID()
			def isValid(playerID, x, y):
				global bestArea
				plot = CyMap().plot(x,y)
				if (plot.getArea() != bestArea):
					return false
				if (plot.getLatitude() >= 75):
					return false
				return true
		findstart = CvMapGeneratorUtil.findStartingPlot(playerID,isValid)
		sPlot = map.plotByIndex(findstart)
		player.setStartingPlot(sPlot,true)
		r = findstart # advc.021a

	if r >= 0: # advc.021a: Code to tell the DLL not to worry
		return -10
	return None

# <advc.001> (from Taurus) The AdvCiv DLL ensures that map scripts without
# a climate option use Temperate climate, but let's still include the
# local bugfix - for portability.
class TectonicsFeatureGenerator(FeatureGenerator):
	def patch_getClimate(self, func, *args, **kwargs):
		getClimate = self.map.getClimate
		def getTemperateClimate(self):
			return 0
		self.map.getClimate = getTemperateClimate.__get__(self.map, type(self.map))
		try:
			getattr(FeatureGenerator, func)(self, *args, **kwargs)
		finally:
			self.map.getClimate = getClimate
	def addIceAtPlot(self, pPlot, iX, iY, lat):
		self.patch_getClimate('addIceAtPlot', pPlot, iX, iY, lat)
	def addJunglesAtPlot(self, pPlot, iX, iY, lat):
		self.patch_getClimate('addJunglesAtPlot', pPlot, iX, iY, lat)

class MediterraneanFeatureGenerator(TectonicsFeatureGenerator): # </advc.001>
	def getLatitudeAtPlot(self, iX, iY):
		"returns 0.0 for tropical, up to 1.0 for polar"
		# 25/90 to 65/90:
		lat = 5/float(18) + 4*(self.iGridH - iY)/float(9*self.iGridH)
		return lat

def addFeatures():
	if (6 == CyMap().getCustomMapOption(0)): # advc.021a: was 5==...
		featuregen = MediterraneanFeatureGenerator()
		featuregen.addFeatures()
		return 0
	else:
		featuregen = TectonicsFeatureGenerator() # advc.001 (was FeatureGenerator)
		featuregen.addFeatures()
		return 0

def addFloodPlains(plot):
	gc = CyGlobalContext()
	if plot.isRiverSide() and plot.isFlatlands():
		if (plot.getFeatureType() == FeatureTypes.NO_FEATURE):
			for iI in range(gc.getNumFeatureInfos()):
				if plot.canHaveFeature(iI):
					if 10000 == gc.getFeatureInfo(iI).getAppearanceProbability():
						plot.setFeatureType(iI, -1)

def normalizeRemovePeaks():
	"A hack. I remove the peaks and I use this as it is the first method called after normalizeAddRiver, which needs a post treatment, so it comes here."
	# Force flood plains
	map = CyMap()
	mapWidth = map.getGridWidth()
	mapHeight = map.getGridHeight()
	width = map.getGridWidth()
	height = map.getGridHeight()
	for x in range(width):
		for y in range(height):
			addFloodPlains(map.plot(x,y))
	# And now the peaks.
	CyPythonMgr().allowDefaultImpl()
