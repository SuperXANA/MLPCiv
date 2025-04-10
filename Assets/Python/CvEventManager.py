## Sid Meier's Civilization 4
## Copyright Firaxis Games 2006
## 
## CvEventManager
## This class is passed an argsList from CvAppInterface.onEvent
## The argsList can contain anything from mouse location to key info
## The EVENTLIST that are being notified can be found 


from CvPythonExtensions import *
import CvUtil
import CvScreensInterface
import CvDebugTools
import CvWBPopups
import PyHelpers
import Popup as PyPopup
import CvCameraControls
import CvTopCivs
import sys
import CvWorldBuilderScreen
import CvAdvisorUtils
import CvTechChooser
import SdToolKitCustom as SDTK
import CustomFunctions

gc = CyGlobalContext()
cf = CustomFunctions.CustomFunctions()
localText = CyTranslator()
PyPlayer = PyHelpers.PyPlayer
PyInfo = PyHelpers.PyInfo


# globals
###################################################
class CvEventManager:
	def __init__(self):
		#################### ON EVENT MAP ######################
		#print "EVENTMANAGER INIT"
				
		self.bCtrl = False
		self.bShift = False
		self.bAlt = False
		self.bAllowCheats = False
		
		# OnEvent Enums
		self.EventLButtonDown=1
		self.EventLcButtonDblClick=2
		self.EventRButtonDown=3
		self.EventBack=4
		self.EventForward=5
		self.EventKeyDown=6
		self.EventKeyUp=7

		# <advc.007> Master switch
		self.__LOG_ALL = 0
		b = 0
		if self.__LOG_ALL:
			b = 1
		# </advc.007>
		self.__LOG_MOVEMENT = b
		self.__LOG_BUILDING = b
		self.__LOG_COMBAT = b
		self.__LOG_CONTACT = b
		self.__LOG_IMPROVEMENT = b
		self.__LOG_PLOTPICKED = b # advc.007
		self.__LOG_NUKEEXPLOSION = b # advc.007
		self.__LOG_CITYLOST = b
		self.__LOG_CITYBUILDING = b
		# <advc.007>
		self.__LOG_CITY_CULTURE = b
		self.__LOG_CITY_GROWTH = b
		self.__LOG_SAVING = b
		# </advc.007>
		self.__LOG_TECH = b
		self.__LOG_UNITBUILD = b
		self.__LOG_UNITKILLED = b
		self.__LOG_UNITLOST = b
		self.__LOG_UNITPROMOTED = b
		self.__LOG_UNITSELECTED = b
		self.__LOG_UNITPILLAGE = b
		self.__LOG_GOODYRECEIVED = b
		self.__LOG_GREATPERSON = b
		self.__LOG_RELIGION = b
		self.__LOG_RELIGIONSPREAD = b
		self.__LOG_GOLDENAGE = b
		self.__LOG_ENDGOLDENAGE = b
		self.__LOG_WARPEACE = b
		self.__LOG_CITYBUILT = b # advc.007
		self.__LOG_CITYACQUIRED = b # advc.007
		self.__LOG_PUSH_MISSION = b

		#self.__LOG_UNITKILLED = 1 # advc.007

		## EVENTLIST
		self.EventHandlerMap = {
			'mouseEvent'			: self.onMouseEvent,
			'kbdEvent' 				: self.onKbdEvent,
			'ModNetMessage'					: self.onModNetMessage,
			'Init'					: self.onInit,
			'Update'				: self.onUpdate,
			'UnInit'				: self.onUnInit,
			'OnSave'				: self.onSaveGame,
			'OnPreSave'				: self.onPreSave,
			'OnLoad'				: self.onLoadGame,
			'GameStart'				: self.onGameStart,
			'GameEnd'				: self.onGameEnd,
			'plotRevealed' 			: self.onPlotRevealed,
			'plotFeatureRemoved' 	: self.onPlotFeatureRemoved,
			'plotPicked'			: self.onPlotPicked,
			'nukeExplosion'			: self.onNukeExplosion,
			'gotoPlotSet'			: self.onGotoPlotSet,
			'BeginGameTurn'			: self.onBeginGameTurn,
			'EndGameTurn'			: self.onEndGameTurn,
			'BeginPlayerTurn'		: self.onBeginPlayerTurn,
			'EndPlayerTurn'			: self.onEndPlayerTurn,
			'endTurnReady'			: self.onEndTurnReady,
			'combatResult' 			: self.onCombatResult,
		  'combatLogCalc'	 		: self.onCombatLogCalc,
		  'combatLogHit'				: self.onCombatLogHit,
			'improvementBuilt' 		: self.onImprovementBuilt,
			'improvementDestroyed' 		: self.onImprovementDestroyed,
			'routeBuilt' 		: self.onRouteBuilt,
			'firstContact' 			: self.onFirstContact,
			'cityBuilt' 			: self.onCityBuilt,
			'cityRazed'				: self.onCityRazed,
			'cityAcquired' 			: self.onCityAcquired,
			'cityAcquiredAndKept' 	: self.onCityAcquiredAndKept,
			'cityLost'				: self.onCityLost,
			'cultureExpansion' 		: self.onCultureExpansion,
			'cityGrowth' 			: self.onCityGrowth,
			'cityDoTurn' 			: self.onCityDoTurn,
			'cityBuildingUnit'	: self.onCityBuildingUnit,
			'cityBuildingBuilding'	: self.onCityBuildingBuilding,
			'cityRename'				: self.onCityRename,
			'cityHurry'				: self.onCityHurry,
			'selectionGroupPushMission'		: self.onSelectionGroupPushMission,
			'unitMove' 				: self.onUnitMove,
			'unitSetXY' 			: self.onUnitSetXY,
			'unitCreated' 			: self.onUnitCreated,
			'unitBuilt' 			: self.onUnitBuilt,
			'unitKilled'			: self.onUnitKilled,
			'unitLost'				: self.onUnitLost,
			'unitPromoted'			: self.onUnitPromoted,
			'unitSelected'			: self.onUnitSelected, 
			'UnitRename'				: self.onUnitRename,
			'unitPillage'				: self.onUnitPillage,
			'unitSpreadReligionAttempt'	: self.onUnitSpreadReligionAttempt,
			'unitGifted'				: self.onUnitGifted,
			'unitBuildImprovement'				: self.onUnitBuildImprovement,
			'goodyReceived'        	: self.onGoodyReceived,
			'greatPersonBorn'      	: self.onGreatPersonBorn,
			'buildingBuilt' 		: self.onBuildingBuilt,
			'projectBuilt' 			: self.onProjectBuilt,
			'techAcquired'			: self.onTechAcquired,
			'techSelected'			: self.onTechSelected,
			'religionFounded'		: self.onReligionFounded,
			'religionSpread'		: self.onReligionSpread, 
			'religionRemove'		: self.onReligionRemove, 
			'corporationFounded'	: self.onCorporationFounded,
			'corporationSpread'		: self.onCorporationSpread, 
			'corporationRemove'		: self.onCorporationRemove, 
			'goldenAge'				: self.onGoldenAge,
			'endGoldenAge'			: self.onEndGoldenAge,
			'chat' 					: self.onChat,
			'victory'				: self.onVictory,
			'vassalState'			: self.onVassalState,
			'changeWar'				: self.onChangeWar,
			'setPlayerAlive'		: self.onSetPlayerAlive,
			'playerChangeStateReligion'		: self.onPlayerChangeStateReligion,
			'playerGoldTrade'		: self.onPlayerGoldTrade,
			'windowActivation'		: self.onWindowActivation,
			'gameUpdate'			: self.onGameUpdate,		# sample generic event
		}

		################## Events List ###############################
		#
		# Dictionary of Events, indexed by EventID (also used at popup context id)
		#   entries have name, beginFunction, applyFunction [, randomization weight...]
		#
		# Normal events first, random events after
		#	
		################## Events List ###############################
		self.Events={
			CvUtil.EventEditCityName : ('EditCityName', self.__eventEditCityNameApply, self.__eventEditCityNameBegin),
			CvUtil.EventEditCity : ('EditCity', self.__eventEditCityApply, self.__eventEditCityBegin),
			CvUtil.EventPlaceObject : ('PlaceObject', self.__eventPlaceObjectApply, self.__eventPlaceObjectBegin),
			CvUtil.EventAwardTechsAndGold: ('AwardTechsAndGold', self.__eventAwardTechsAndGoldApply, self.__eventAwardTechsAndGoldBegin),
			CvUtil.EventEditUnitName : ('EditUnitName', self.__eventEditUnitNameApply, self.__eventEditUnitNameBegin),
			CvUtil.EventWBAllPlotsPopup : ('WBAllPlotsPopup', self.__eventWBAllPlotsPopupApply, self.__eventWBAllPlotsPopupBegin),
			CvUtil.EventWBLandmarkPopup : ('WBLandmarkPopup', self.__eventWBLandmarkPopupApply, self.__eventWBLandmarkPopupBegin),
			CvUtil.EventWBScriptPopup : ('WBScriptPopup', self.__eventWBScriptPopupApply, self.__eventWBScriptPopupBegin),
			CvUtil.EventWBStartYearPopup : ('WBStartYearPopup', self.__eventWBStartYearPopupApply, self.__eventWBStartYearPopupBegin),
			CvUtil.EventShowWonder: ('ShowWonder', self.__eventShowWonderApply, self.__eventShowWonderBegin),
		}	
#################### EVENT STARTERS ######################
	def handleEvent(self, argsList):
		'EventMgr entry point'
		# extract the last 6 args in the list, the first arg has already been consumed
		self.origArgsList = argsList	# point to original
		tag = argsList[0]				# event type string
		idx = len(argsList)-6
		bDummy = false
		self.bDbg, bDummy, self.bAlt, self.bCtrl, self.bShift, self.bAllowCheats = argsList[idx:]
		ret = 0
		if self.EventHandlerMap.has_key(tag):
			fxn = self.EventHandlerMap[tag]
			ret = fxn(argsList[1:idx])
		return ret
		
#################### EVENT APPLY ######################	
	def beginEvent( self, context, argsList=-1 ):
		'Begin Event'
		entry = self.Events[context]
		return entry[2]( argsList )
	
	def applyEvent( self, argsList ):
		'Apply the effects of an event '
		context, playerID, netUserData, popupReturn = argsList
		
		if context == CvUtil.PopupTypeEffectViewer:
			return CvDebugTools.g_CvDebugTools.applyEffectViewer( playerID, netUserData, popupReturn )
		
		entry = self.Events[context]
				
		if ( context not in CvUtil.SilentEvents ):
			self.reportEvent(entry, context, (playerID, netUserData, popupReturn) )
		return entry[1]( playerID, netUserData, popupReturn )   # the apply function

	def reportEvent(self, entry, context, argsList):
		'Report an Event to Events.log '
		if (gc.getGame().getActivePlayer() != -1):
			message = "DEBUG Event: %s (%s)" %(entry[0], gc.getActivePlayer().getName())
			CyInterface().addImmediateMessage(message,"")
			CvUtil.pyPrint(message)
		return 0
		
#################### ON EVENTS ######################
	def onKbdEvent(self, argsList):
		'keypress handler - return 1 if the event was consumed'
		# advc.007b: Body (mostly cheat commands) deleted; keyboard input is handled by BugEventManager.py.
		return 0

	def onModNetMessage(self, argsList):
		'Called whenever CyMessageControl().sendModNetMessage() is called - this is all for you modders!'
		
		iData1, iData2, iData3, iData4, iData5 = argsList
		
		print("Modder's net message!")
		
		CvUtil.pyPrint( 'onModNetMessage' )

	def onInit(self, argsList):
		'Called when Civ starts up'
		CvUtil.pyPrint( 'OnInit' )
		
	def onUpdate(self, argsList):
		'Called every frame'
		# advc (note): I don't think this is ever called(?).
		fDeltaTime = argsList[0]
		
		# allow camera to be updated
		CvCameraControls.g_CameraControls.onUpdate( fDeltaTime )
		
	def onWindowActivation(self, argsList):
		'Called when the game window activates or deactivates'
		bActive = argsList[0]
		
	def onUnInit(self, argsList):
		'Called when Civ shuts down'
		CvUtil.pyPrint('OnUnInit')
	
	def onPreSave(self, argsList):
		"called before a game is actually saved"
		# <advc.007>
		if (not self.__LOG_SAVING):
			return # </advc.007>
		CvUtil.pyPrint('OnPreSave')
	
	def onSaveGame(self, argsList):
		"return the string to be saved - Must be a string"
		return ""

	def onLoadGame(self, argsList):
		CvAdvisorUtils.resetNoLiberateCities()
		return 0

	# advc.704: Trigger DoM from the DLL instead
	def onGameStart(self, argsList):
		'Called at the start of the game'
		if (gc.getGame().getGameTurnYear() == gc.getDefineINT("START_YEAR") and not gc.getGame().isOption(GameOptionTypes.GAMEOPTION_ADVANCED_START) and not gc.getGame().isOption(GameOptionTypes.GAMEOPTION_RISE_FALL)):
			for iPlayer in range(gc.getMAX_PLAYERS()):
				player = gc.getPlayer(iPlayer)
				if (player.isAlive() and player.isHuman()):
					popupInfo = CyPopupInfo()
					popupInfo.setButtonPopupType(ButtonPopupTypes.BUTTONPOPUP_PYTHON_SCREEN)
					popupInfo.setText(u"showDawnOfMan")
					popupInfo.addPopup(iPlayer)
		else:
			CyInterface().setSoundSelectionReady(true)

## Platyping's Promotions and Traits - Start ##
## Spiritual Trait Start ##
		# for iPlayer in xrange(gc.getMAX_CIV_PLAYERS()):
			# pPlayer = gc.getPlayer(iPlayer)
			# if pPlayer.isAlive():
				# if pPlayer.hasTrait(gc.getInfoTypeForString("TRAIT_SPIRITUAL")):
					# pPlayer.changeStateReligionUnitProductionModifier(20)
## Spiritual Trait End ##
## Platyping's Promotions and Traits - End ##

		if gc.getGame().isPbem():
			for iPlayer in range(gc.getMAX_PLAYERS()):
				player = gc.getPlayer(iPlayer)
				if (player.isAlive() and player.isHuman()):
					popupInfo = CyPopupInfo()
					popupInfo.setButtonPopupType(ButtonPopupTypes.BUTTONPOPUP_DETAILS)
					popupInfo.setOption1(true)
					popupInfo.addPopup(iPlayer)

		CvAdvisorUtils.resetNoLiberateCities()

	def onGameEnd(self, argsList):
		'Called at the End of the game'
		print("Game is ending")
		return

	def onBeginGameTurn(self, argsList):
		'Called at the beginning of the end of each turn'
		iGameTurn = argsList[0]
		CvTopCivs.CvTopCivs().turnChecker(iGameTurn)

	def onEndGameTurn(self, argsList):
		'Called at the end of the end of each turn'
		iGameTurn = argsList[0]
		
	def onBeginPlayerTurn(self, argsList):
		'Called at the beginning of a players turn'
		iGameTurn, iPlayer = argsList
		
		pPlayer = gc.getPlayer(iPlayer)
		pPlayerTeam = gc.getTeam(pPlayer.getTeam())
		
# Celestia Unique Trait ##
		# if pPlayer.getLeaderType() == gc.getInfoTypeForString("LEADER_CELESTIA"):
			# if pPlayerTeam.getAtWarCount(True) == 0:
				# sGoldenAgeBoost = "0"
				# if pPlayer.isGoldenAge():
					# sGoldenAgeBoost = "5"
				# (loopCity, iter) = pPlayer.firstCity(False)
				# while(loopCity):
					# iLoopCityGPProgress = loopCity.getGreatPeopleProgress()
					# if iLoopCityGPProgress > 0:
						# sLoopCityPopulation = str(loopCity.getPopulation())
						# if len(sLoopCityPopulation) == 1:
							# sLoopCityPopulation = "0"+sLoopCityPopulation
						# fValue = (iLoopCityGPProgress * float("1."+sLoopCityPopulation+sGoldenAgeBoost)) - iLoopCityGPProgress
						# iValue = int(fValue)
						# iA = iValue-1
						# iB = iValue+1
						# if iA < iB:
							# bFloatCanRound = (iA < fValue < iB)
						# else:
							# bFloatCanRound = (iB < fValue < iA)
						# if bFloatCanRound:
							# iValue = iValue+1
						# if iValue > 0:
							# loopCity.changeGreatPeopleProgress(iValue)
					# (loopCity, iter) = pPlayer.nextCity(iter, False)
# Celestia Unique Trait ##

# Twilight Unique Trait ##
		# if pPlayer.getLeaderType() == gc.getInfoTypeForString("LEADER_TWILIGHT"):
			# iTech = pPlayer.getCurrentResearch()
			# if iTech > -1:
				# iOurProgress = pPlayerTeam.getResearchLeft(iTech)
				# iPlayerValue = int((iOurProgress * 1.1) - iOurProgress)
				# iFriendValue = 0
				# eAttitude = AttitudeTypes.ATTITUDE_PLEASED
				# if iPlayerValue > 0:
					# for iLoopPlayer in xrange(gc.getMAX_CIV_PLAYERS()):
						# if iLoopPlayer == iPlayer: continue
						# pLoopPlayer = gc.getPlayer(iLoopPlayer)
						# if not pLoopPlayer.isAlive(): continue
						# if pLoopPlayer.getCurrentResearch() != iTech: continue
						# if pLoopPlayer.canTradeNetworkWith(iPlayer) != True: continue
						# if (not pLoopPlayer.isHuman() and pLoopPlayer.AI_getAttitude(iPlayer) >= eAttitude) or (pLoopPlayer.isHuman() and pPlayer.AI_getAttitude(iLoopPlayer) >= eAttitude):
							# pLoopTeam = gc.getTeam(pLoopPlayer.getTeam())
							# iTheirProgress = pLoopTeam.getResearchLeft(iTech)
							# iFriendValue += int((iTheirProgress * 1.1) - iTheirProgress)
							# if iFriendValue > 0:
								# pLoopTeam.changeResearchProgress(iTech, iPlayerValue, iLoopPlayer)
					# if iFriendValue > 0:
						# pPlayerTeam.changeResearchProgress(iTech, iFriendValue, iPlayer)
# Twilight Unique Trait ##

# Rusa Imperio Unique Trait ##
		# if pPlayer.getLeaderType() == gc.getInfoTypeForString("LEADER_RUSA"):
			# if pPlayer.getMaxConscript() > 0:
				# (loopCity, iter) = pPlayer.firstCity(False)
				# while(loopCity):
					# iValue = loopCity.getConscriptAngerTimer()
					# if iValue > 0:
						# loopCity.changeConscriptAngerTimer(-iValue)
					# (loopCity, iter) = pPlayer.nextCity(iter, False)
# Rusa Imperio Unique Trait ##

# King Sombra Unique Trait ##
		# if pPlayer.getLeaderType() == gc.getInfoTypeForString("LEADER_SOMBRA"):
			# if pPlayer.canHurry(gc.getInfoTypeForString("HURRY_POPULATION")):
				# (loopCity, iter) = pPlayer.firstCity(False)
				# while(loopCity):
					# iValue = loopCity.getHurryAngerTimer()
					# if iValue > 0:
						# loopCity.changeHurryAngerTimer(-iValue)
					# (loopCity, iter) = pPlayer.nextCity(iter, False)
# King Sombra Unique Trait ##

	def onEndPlayerTurn(self, argsList):
		'Called at the end of a players turn'
		iGameTurn, iPlayer = argsList
		
		pPlayer = gc.getPlayer(iPlayer)

## Platyping's Promotions and Traits - Start ##
## Traditional Trait ##
		# if pPlayer.hasTrait(gc.getInfoTypeForString("TRAIT_TRADITIONAL")):
			# pCapital = pPlayer.getCapitalCity()
			# if pCapital:
				# pCapital.changeDefenseDamage(-100)
## Traditional Trait ##
## Platyping's Promotions and Traits - End ##

		if (gc.getGame().getElapsedGameTurns() == 1):
			if (gc.getPlayer(iPlayer).isHuman()):
				if (gc.getPlayer(iPlayer).canRevolution(0)):
					popupInfo = CyPopupInfo()
					popupInfo.setButtonPopupType(ButtonPopupTypes.BUTTONPOPUP_CHANGECIVIC)
					popupInfo.addPopup(iPlayer)
		
		CvAdvisorUtils.resetAdvisorNags()
		CvAdvisorUtils.endTurnFeats(iPlayer)

	def onEndTurnReady(self, argsList):
		iGameTurn = argsList[0]

	def onFirstContact(self, argsList):
		'Contact'
		iTeamX,iHasMetTeamY = argsList
		
## Platyping's Promotions and Traits - Start ##
		# pTeam = gc.getTeam(iTeamX)
		# if pTeam.isVassal(iHasMetTeamY):
			# pPlayer = gc.getPlayer(pTeam.getLeaderID())
## Spiritual Trait ##
			# if pPlayer.hasTrait(gc.getInfoTypeForString("TRAIT_SPIRITUAL")):
				# pPlayer.changeStateReligionUnitProductionModifier(20)
## Philosophical Trait ##
			# if pPlayer.hasTrait(gc.getInfoTypeForString("TRAIT_PHILOSOPHICAL")):
				# pCapital = pPlayer.getCity(0)
				# pCapital.setNumRealBuilding(gc.getInfoTypeForString("BUILDING_PHILOSOPHICAL"), 1)
## Imperialist Trait ##
			# if pPlayer.hasTrait(gc.getInfoTypeForString("TRAIT_IMPERIALIST")):
				# pCapital = pPlayer.getCity(0)
				# Bonus = [gc.getInfoTypeForString("BONUS_GEMS"), gc.getInfoTypeForString("BONUS_SILVER"), gc.getInfoTypeForString("BONUS_GOLD")]
				# LuxuryPlot = []
				# for i in xrange(21):
					# pPlot = pCapital.getCityIndexPlot(i)
					# if pPlot.getBonusType(-1) == -1:
						# if not pPlot.isPeak() and not pPlot.isWater() and not pPlot.isCity():
							# LuxuryPlot.append(pPlot)
				# if len(LuxuryPlot) > 0:
					# pPlot = LuxuryPlot[CyGame().getSorenRandNum(len(LuxuryPlot), "where")]
					# pPlot.setBonusType(Bonus[CyGame().getSorenRandNum(3, "which")])
				# else:
					# pPlot = pCapital.plot()
					# if pPlot.getBonusType(-1) == -1:
						# pPlot.setBonusType(Bonus[CyGame().getSorenRandNum(3, "which")])
					# else:
						# pCapital.changeFreeBonus(Bonus[CyGame().getSorenRandNum(3, "which")], 1)
## Charismatic Trait ##
		# for iPlayerX in xrange(gc.getMAX_CIV_PLAYERS()):
			# pPlayerX = gc.getPlayer(iPlayerX)
			# if pPlayerX.isAlive() and pPlayerX.getTeam() == iTeamX:
				# if pPlayerX.hasTrait(gc.getInfoTypeForString("TRAIT_CHARISMATIC")):
					# for iPlayerY in xrange(gc.getMAX_CIV_PLAYERS()):
						# pPlayerY = gc.getPlayer(iPlayerY)
						# if pPlayerY.isAlive() and pPlayerY.getTeam() == iHasMetTeamY:
							# pPlayerY.AI_changeAttitudeExtra(iPlayerX, 2)
## Platyping's Promotions and Traits - End ##
		
		if (not self.__LOG_CONTACT):
			return
		CvUtil.pyPrint('Team %d has met Team %d' %(iTeamX, iHasMetTeamY))
	
	def onCombatResult(self, argsList):
		'Combat Result'
		pWinner,pLoser = argsList
		playerX = PyPlayer(pWinner.getOwner())
		unitX = PyInfo.UnitInfo(pWinner.getUnitType())
		playerY = PyPlayer(pLoser.getOwner())
		unitY = PyInfo.UnitInfo(pLoser.getUnitType())
		
## Platyping's Promotions and Traits - Start ##
## Aggressive Trait Start ##
		# iPlayer = pWinner.getOwner()
		# pPlayer = gc.getPlayer(iPlayer)
		# if pPlayer.hasTrait(gc.getInfoTypeForString("TRAIT_AGGRESSIVE")):
			# LoserInfo = gc.getUnitInfo(pLoser.getUnitType())
			# if not LoserInfo.isMechUnit() and pLoser.getUnitCombatType() != -1:
				# if not pWinner.plot().isWater():
					# if CyGame().getSorenRandNum(4, "enslave") == 0:
						# iWorker = gc.getCivilizationInfo(pPlayer.getCivilizationType()).getCivilizationUnits(gc.getInfoTypeForString("UNITCLASS_WORKER"))
						# if iWorker == -1:
							# iWorker = gc.getInfoTypeForString("UNIT_WORKER")
						# pNewUnit = pPlayer.initUnit(iWorker, pWinner.getX(), pWinner.getY(), UnitAITypes.NO_UNITAI, DirectionTypes.NO_DIRECTION)
						# pNewUnit.finishMoves()
						# CyInterface().addMessage(iPlayer,True,15,CyTranslator().getText("TXT_ENSLAVE",(pNewUnit.getName(),)),'',0, pNewUnit.getButton(),ColorTypes(11),pWinner.getX(), pWinner.getY(), True,True)
## Aggressive Trait End ##
## Arrogant Trait ##
		# iPlayer = pWinner.getOwner()
		# pPlayer = gc.getPlayer(iPlayer)
		# if pPlayer.hasTrait(gc.getInfoTypeForString("TRAIT_ARROGANT")):
			# if pLoser.baseCombatStr() > 0 or pLoser.airBaseCombatStr() > 0:
				# if pLoser.getDomainType() == pWinner.getDomainType():
					# if CyGame().getSorenRandNum(10, "Immobile") == 0:
						# pWinner.finishMoves()
## Arrogant Trait ##
## Platyping's Promotions and Traits - End ##

		iPlayer = pWinner.getOwner()
		pPlayer = gc.getPlayer(iPlayer)
		iPlayer2 = pLoser.getOwner()
		pPlayer2 = gc.getPlayer(iPlayer2)
		pTeam = gc.getTeam(pPlayer.getTeam())
		pPlot = pWinner.plot()
		pPlot2 = pLoser.plot()
		
# Sunset Unique Trait ##
		# if pPlayer.getLeaderType() == gc.getInfoTypeForString("LEADER_SUNSET"):
			# if (pPlot.getOwner() == iPlayer) and not pLoser.isAnimal():
				# iUnitsOnPlot = pPlot.getNumDefenders(iPlayer)
				# if iUnitsOnPlot > 1:
					# game = CyGame()
					# if ((game.getSorenRandNum(iUnitsOnPlot, "Unique Ability Rand Chance") * 2) < game.getSorenRandNum(iUnitsOnPlot, "Unique Ability Rand Chance")):
						# pCity = pPlot.getWorkingCity()
						# if pCity.isNone() or (pCity.getOwner() != iPlayer):
							# pCity = pPlayer.getCapitalCity()
						# if not pCity.isNone() and (pCity.getGreatPeopleProgress > 0):
							# pCity.changeGreatPeopleProgress(min(3,max(1,game.getSorenRandNum(4, "Unique Ability GPP Random"))))
# Sunset Unique Trait ##

# Equalis Unique Trait ##
		# if pPlayer.getLeaderType() == gc.getInfoTypeForString("LEADER_EQUALIS"):
			# if iPlayer != pPlot.getOwner():
				# iUnitLevel = (pWinner.getLevel()*5)
				# if CyGame().getSorenRandNum(abs(55-iUnitLevel), "Unique Ability Rand Chance") == 0:
					# pPlayer.changeGoldenAgeTurns(pPlayer.getGoldenAgeLength())
# Equalis Unique Trait ##

# Rusa Imperio Unique Trait ##
		# if pPlayer.getLeaderType() == gc.getInfoTypeForString("LEADER_RUSA"):
			# iUnitCombatGun = gc.getInfoTypeForString("UNITCOMBAT_GUN")
			# if pLoser.getUnitCombatType() == iUnitCombatGun:
				# for iLoopUnit in xrange(pPlot.getNumDefenders(iPlayer)):
					# pLoopUnit = pPlot.getUnit(iLoopUnit)
					# if pLoopUnit.isNone(): continue
					# if pLoopUnit.isDead(): continue
					# if pLoopUnit.getUnitCombatType() == iUnitCombatGun:
						# pLoopUnit.changeMoves(-60)
						# pLoopUnit.setMadeAttack(False)
# Rusa Imperio Unique Trait ##

## Platyping's Promotions and Traits - Start ##
## Hunter Start ##
		if pLoser.isAnimal():
			if pWinner.isHasPromotion(gc.getInfoTypeForString("PROMOTION_HUNTER")):
				pCity = pPlot.getWorkingCity()
				if pCity.isNone() or (pCity.getOwner() != iPlayer):
					pCity = pPlayer.getCapitalCity()
				pCity.changeFood(pLoser.baseCombatStr() * 3)
## Artifacts Start ##
		cf.doArtifactFeats(pWinner,pLoser)
## Cornucopia Start ##
		if pWinner.isHasPromotion(gc.getInfoTypeForString("ARTIFACT_CORNUCOPIA")):
			if CyGame().getSorenRandNum(40, "Resource") == 0:
				AvailableBonus = []
				for iBonus in xrange(gc.getNumBonusInfos()):
					BonusInfo = gc.getBonusInfo(iBonus)
					if BonusInfo.getTechCityTrade() > -1 and not pTeam.isHasTech(BonusInfo.getTechCityTrade()): continue
					if BonusInfo.getTechObsolete() > -1 and pTeam.isHasTech(BonusInfo.getTechObsolete()): continue
					AvailableBonus.append(iBonus)	
				Capital = pPlayer.getCapitalCity()
				iCornucopia = AvailableBonus[CyGame().getSorenRandNum(len(AvailableBonus), "Cornucopia")]
				Capital.changeFreeBonus(iCornucopia, 1)
				CyInterface().addMessage(iPlayer,true,10,CyTranslator().getText("TXT_CORNUCOPIA",(gc.getBonusInfo(iCornucopia).getDescription(),Capital.getName(),)),'',0,gc.getBonusInfo(iCornucopia).getButton(),ColorTypes(11),Capital.getX(),Capital.getY(), false,false)
## Fire Storm I Start ##
		if pPlot2.isCity():
			pCity2 = pPlot2.getPlotCity()
			if pTeam.isAtWar(gc.getPlayer(pCity2.getOwner()).getTeam()):
				if pWinner.isHasPromotion(gc.getInfoTypeForString("PROMOTION_FIRESTORM1")):
					pCity2.setPopulation(max(1, pCity2.getPopulation() -1))
## Fire Storm II Start ##
				if pWinner.isHasPromotion(gc.getInfoTypeForString("PROMOTION_FIRESTORM2")):
					if CyGame().getSorenRandNum(2, "Fire") == 0:
						if pPlot2.getFeatureType() == -1:
							pPlot2.setFeatureType(gc.getInfoTypeForString("FEATURE_FIRE"), -1)
## SiegeBreaker Start ##
				if pWinner.isHasPromotion(gc.getInfoTypeForString("PROMOTION_SIEGEBREAKER")):
					pCity2.changeDefenseDamage(5)
## Sorrow Start ##
				if pWinner.isHasPromotion(gc.getInfoTypeForString("PROMOTION_SORROW")):
					pCity2.changeEspionageHappinessCounter(3)
					if pCity2.getEspionageHappinessCounter() > 10:
						pCity2.setOccupationTimer(max(pCity2.getOccupationTimer(), pCity2.getEspionageHappinessCounter() - 10))
## Divine Shield Start ##
		if pWinner.isHasPromotion(gc.getInfoTypeForString("PROMOTION_DIVINE_SHIELD")):
			if CyGame().getSorenRandNum(5, "Shield Break") == 0:
				pWinner.setHasPromotion(gc.getInfoTypeForString("PROMOTION_DIVINE_SHIELD"), false)
				CyInterface().addMessage(iPlayer,true,10,CyTranslator().getText("TXT_SHIELD_BREAK",(pWinner.getName(),)),'',0, '',-1,-1,-1, true,true)
## Heroic Start ##
		if pWinner.isHasPromotion(gc.getInfoTypeForString("PROMOTION_HEROIC")):
			if pPlot.getOwner() > -1:
				if CyGame().getSorenRandNum(50, "Golden Age") == 0:
					pPlayer.changeGoldenAgeTurns(pPlayer.getGoldenAgeLength())
## Diplomat Start ##
		if pWinner.isHasPromotion(gc.getInfoTypeForString("PROMOTION_DIPLOMAT")):
			iCulture = pPlot2.getCulture(iPlayer2) /100
			pPlot2.changeCulture(iPlayer2, -iCulture, true)
			pPlot2.changeCulture(iPlayer, iCulture, true)
## Fear Start ##
		if pWinner.isHasPromotion(gc.getInfoTypeForString("PROMOTION_FEAR")):
			for iUnit in xrange(pPlot2.getNumUnits()):
				pUnit = pPlot2.getUnit(iUnit)
				if pUnit.isNone(): continue
				if pUnit.isDead(): continue
				if pUnit.getDomainType() != pWinner.getDomainType(): continue
				if pUnit.getDamage() < 85: continue
				iPlayerX = pUnit.getOwner()
				if pTeam.isAtWar(gc.getPlayer(iPlayerX).getTeam()):
					pUnit.setImmobileTimer(3)
					pUnit.setDamage(min(99, pUnit.getDamage() + 15), false)
					break
## Rain of Arrows Start ##
		if pWinner.isHasPromotion(gc.getInfoTypeForString("PROMOTION_RAIN_OF_ARROWS")):
			for iUnit in xrange(pPlot2.getNumUnits()):
				pUnit = pPlot2.getUnit(iUnit)
				if pUnit.isNone(): continue
				if pUnit.isDead(): continue
				if pUnit.getDomainType() != pWinner.getDomainType(): continue
				if pUnit.getDamage() < 85: continue
				iPlayerX = pUnit.getOwner()
				if pTeam.isAtWar(gc.getPlayer(iPlayerX).getTeam()):
					pUnit.setDamage(100, false)
					pWinner.changeExperience(1, 9999, false, false, false)
					CyInterface().addMessage(iPlayer,true,10,CyTranslator().getText("TXT_RAIN_OF_ARROWS",(pUnit.getName(),)),'',0,'',-1, -1, -1, true,true)
					CyInterface().addMessage(iPlayerX,true,10,CyTranslator().getText("TXT_RAIN_OF_ARROWS",(pUnit.getName(),)),'',0,'',-1, -1, -1, true,true)
## Spoils of War Start ##
		if pWinner.isHasPromotion(gc.getInfoTypeForString("PROMOTION_SPOILS_OF_WAR")):
			iSpoils = 5 * pWinner.getLevel()
			pPlayer.changeGold(iSpoils)
			CyInterface().addMessage(iPlayer,true,10,CyTranslator().getText("TXT_SPOILS",(iSpoils,)),'',0,'',-1,-1,-1, true,true)
## Rally Start ##
		if pWinner.isHasPromotion(gc.getInfoTypeForString("PROMOTION_RALLY")):
			if not pPlot.isWater():
				if CyGame().getSorenRandNum(5, "Rally") == 0:
					pMessage = pPlot
					if pPlot2.getNumVisibleEnemyDefenders(pWinner) == 1:
						pMessage = pPlot2
					pNewUnit = pPlayer.initUnit(pPlayer.getCapitalCity().getConscriptUnit(), pMessage.getX(), pMessage.getY(), UnitAITypes.NO_UNITAI, DirectionTypes.NO_DIRECTION)
					pNewUnit.finishMoves()
					CyInterface().addMessage(iPlayer,true,10,CyTranslator().getText("TXT_RALLY_TROOP",(pWinner.getName(), pNewUnit.getName(),)),'',0, pNewUnit.getButton(),ColorTypes(11), pMessage.getX(), pMessage.getY(), true,true)
## Inspiration Start ##
		if pWinner.isHasPromotion(gc.getInfoTypeForString("PROMOTION_INSPIRATION")):
			pPlayer.changeCombatExperience(2)
## Reconnaissance Start ##
		if pWinner.isHasPromotion(gc.getInfoTypeForString("PROMOTION_RECONNAISSANCE")):
			pWinner.setReconPlot(CyMap().plot(pPlot.getX() - 3, pPlot.getY() -3))
			pWinner.setReconPlot(CyMap().plot(pPlot.getX() + 3, pPlot.getY() -3))
			pWinner.setReconPlot(CyMap().plot(pPlot.getX() - 3, pPlot.getY() +3))
			pWinner.setReconPlot(CyMap().plot(pPlot.getX() + 3, pPlot.getY() +3))
## Giant Slayer Start ##
		if pLoser.getLevel() - pWinner.getLevel() > 2:
			pWinner.setHasPromotion(gc.getInfoTypeForString("PROMOTION_GIANT_SLAYER"), true)
			CyInterface().addMessage(iPlayer,true,10,CyTranslator().getText("TXT_LEARN_PROMO",(pWinner.getName(), gc.getPromotionInfo(gc.getInfoTypeForString("PROMOTION_GIANT_SLAYER")).getDescription(),)),'',0,'',-1,-1,-1, true,true)
## Frenzy Start ##
		if pWinner.isHasPromotion(gc.getInfoTypeForString("PROMOTION_FRENZY")):
			pWinner.setDamage(min(99, pWinner.getDamage() + 5), false)
## Cold Blooded Start ##
		if not pWinner.isHasPromotion(gc.getInfoTypeForString("PROMOTION_COLD_BLOODED")):
## Despair Start ##
			if pLoser.isHasPromotion(gc.getInfoTypeForString("PROMOTION_DESPAIR")):
				pWinner.setImmobileTimer(pWinner.getImmobileTimer() + 5)
				if pLoser.isHasPromotion(gc.getInfoTypeForString("PROMOTION_RETRIBUTION")):
					pWinner.setImmobileTimer(pWinner.getImmobileTimer() + 5)
## Retribution Start ##
			if pLoser.isHasPromotion(gc.getInfoTypeForString("PROMOTION_RETRIBUTION")):
				pWinner.changeDamage(25, false)
				if pLoser.isHasPromotion(gc.getInfoTypeForString("PROMOTION_DESPAIR")):
					pWinner.changeDamage(25, false)
## Stupify Start ##
			if pLoser.isHasPromotion(gc.getInfoTypeForString("PROMOTION_STUPIFY")):
				pWinner.setExperience(pWinner.getExperience() * 4/5, 9999)
## Possession Start ##
			if pLoser.isHasPromotion(gc.getInfoTypeForString("PROMOTION_POSSESSION")):
				if CyGame().getSorenRandNum(4, "Possession") == 0:
					pNewUnit = gc.getPlayer(iPlayer2).initUnit(pWinner.getUnitType(), pLoser.getX(), pLoser.getY(), UnitAITypes.NO_UNITAI, DirectionTypes.NO_DIRECTION)
					pNewUnit.convert(pWinner)
					pNewUnit.setBaseCombatStr(pWinner.baseCombatStr())
					pNewUnit.finishMoves()
					CyInterface().addMessage(iPlayer,true,10,CyTranslator().getText("TXT_POSSESSION",(pWinner.getName() + CyTranslator().getText("[COLOR_WARNING_TEXT]", ()),)),'',0,'',-1, -1, -1, true,true)
					CyInterface().addMessage(iPlayer2,true,10,CyTranslator().getText("TXT_POSSESSION",(pWinner.getName() + CyTranslator().getText("[COLOR_POSITIVE_TEXT]", ()),)),'',0,'',-1, -1, -1, true,true)
## Banshee Cry Start ##
		if pLoser.isHasPromotion(gc.getInfoTypeForString("PROMOTION_BANSHEE_CRY")):
			for iUnit in xrange(pPlot.getNumUnits()):
				pUnit = pPlot.getUnit(iUnit)
				if pUnit.isNone(): continue
				if pUnit.isHasPromotion(gc.getInfoTypeForString("PROMOTION_COLD_BLOODED")): continue
				if pUnit.getUnitCombatType() == -1: continue
				if pUnit.getLevel() > 4: continue
				if pUnit.getOwner() == iPlayer:
					pUnit.setHasPromotion(gc.getInfoTypeForString("PROMOTION_CURSE"), true)
## Regeneration Start ##
		if pWinner.isHasPromotion(gc.getInfoTypeForString("PROMOTION_REGENERATION")):
			pWinner.changeDamage(-15, false)
## Bloodlust Start ##
		if pWinner.isHasPromotion(gc.getInfoTypeForString("PROMOTION_BLOODLUST")):
			pWinner.changeMoves(-30 * (pWinner.getDamage()/25))
## Unstoppable Start ##
		if pWinner.isHasPromotion(gc.getInfoTypeForString("PROMOTION_UNSTOPPABLE")):
			if pWinner.getDamage() == 0:
				pWinner.changeMoves(-60)
				pWinner.setMadeAttack(false)
## Triumph Start ##
		if pWinner.isHasPromotion(gc.getInfoTypeForString("PROMOTION_TRIUMPH")):
			if pPlot.isCity():
				pCity = pPlot.getPlotCity()
				pCity.changeHappinessTimer(5)
## Sword of Justice Start ##
		if pWinner.isHasPromotion(gc.getInfoTypeForString("PROMOTION_JUSTICE")):
			LevelDifference = pWinner.getLevel() - pLoser.getLevel()
			if CyGame().getSorenRandNum(20, "Stun") < min(5, LevelDifference):
				if pPlot.getOwner() != iPlayer:
					pWinner.setImmobileTimer(pWinner.getImmobileTimer() + (LevelDifference + 2) /3)
## Gifted Start ##
		if pWinner.isHasPromotion(gc.getInfoTypeForString("PROMOTION_GIFTED")):
			Promotions = []
			for iPromotion in xrange(gc.getNumPromotionInfos()):
				if pLoser.isHasPromotion(iPromotion) and pWinner.isPromotionValid(iPromotion):
					if pWinner.isHasPromotion(iPromotion): continue
					if iPromotion == gc.getInfoTypeForString("PROMOTION_LEADER"): continue
					Promotions.append(iPromotion)
			if len(Promotions) > 0:
				chosenPromotion = Promotions[CyGame().getSorenRandNum(len(Promotions), "which promotion")]
				pWinner.setHasPromotion(chosenPromotion, true)
				arguments = pWinner, chosenPromotion
				self.onUnitPromoted(arguments)
				CyInterface().addMessage(iPlayer,true,10,CyTranslator().getText("TXT_LEARN_PROMO",(pWinner.getName(), gc.getPromotionInfo(chosenPromotion).getDescription(),)),'',0,'',-1,-1,-1, true,true)
## Shapeshifter Start ##
		if pWinner.isHasPromotion(gc.getInfoTypeForString("PROMOTION_SHAPESHIFTER")):
			Shapeshift = ["PROMOTION_EARTH_ELEMENTAL", "PROMOTION_WATER_ELEMENTAL", "PROMOTION_FIRE_ELEMENTAL", "PROMOTION_AIR_ELEMENTAL"]
			for iShape in Shapeshift:
				pWinner.setHasPromotion(gc.getInfoTypeForString(iShape), false)
			pWinner.setHasPromotion(gc.getInfoTypeForString(Shapeshift[CyGame().getSorenRandNum(4, "New Form")]), true)
## Rampage Start ##
		if pWinner.isHasPromotion(gc.getInfoTypeForString("PROMOTION_RAMPAGE")):
			if pWinner.getExperience() >= pWinner.experienceNeeded():
				pWinner.setPromotionReady(true)
## WindRunner Start ##
		if pWinner.isHasPromotion(gc.getInfoTypeForString("PROMOTION_WINDRUNNER")):
			if not pPlot.isCity() and pPlot.getOwner() == iPlayer and pWinner.getDamage() >= 75:
				pCity = CyMap().findCity(pPlot.getX(), pPlot.getY(), iPlayer, -1, false, false, -1, -1, CyCity())
				pNewUnit = pPlayer.initUnit(pWinner.getUnitType(),pCity.getX(), pCity.getY(), UnitAITypes.NO_UNITAI, DirectionTypes.NO_DIRECTION)
				pNewUnit.convert(pWinner)
				pNewUnit.setBaseCombatStr(pWinner.baseCombatStr())
				pNewUnit.finishMoves()
				CyInterface().addMessage(iPlayer,true,10,CyTranslator().getText("TXT_WINDRUNNER",(pWinner.getName(),pCity.getName(),)),'',0, gc.getPromotionInfo(gc.getInfoTypeForString("PROMOTION_WINDRUNNER")).getButton(),ColorTypes(11), pCity.getX(), pCity.getY(), true,true)
## Platyping's Promotions and Traits - End ##

		if (not self.__LOG_COMBAT):
			return
		#if playerX and playerX and unitX and playerY:
		# advc.001: The above looks like a copy-paste error
		if playerX and playerY and unitX and unitY:
			CvUtil.pyPrint('Player %d Civilization %s Unit %s has defeated Player %d Civilization %s Unit %s' 
				%(playerX.getID(), playerX.getCivilizationName(), unitX.getDescription(), 
				playerY.getID(), playerY.getCivilizationName(), unitY.getDescription()))

	def onCombatLogCalc(self, argsList):
		'Combat Result'	
		genericArgs = argsList[0][0]
		cdAttacker = genericArgs[0]
		cdDefender = genericArgs[1]
		iCombatOdds = genericArgs[2]
		CvUtil.combatMessageBuilder(cdAttacker, cdDefender, iCombatOdds)
		
	def onCombatLogHit(self, argsList):
		'Combat Message'
		global gCombatMessages, gCombatLog
		genericArgs = argsList[0][0]
		cdAttacker = genericArgs[0]
		cdDefender = genericArgs[1]
		iIsAttacker = genericArgs[2]
		iDamage = genericArgs[3]
		
		if cdDefender.eOwner == cdDefender.eVisualOwner:
			szDefenderName = gc.getPlayer(cdDefender.eOwner).getNameKey()
		else:
			szDefenderName = localText.getText("TXT_KEY_TRAIT_PLAYER_UNKNOWN", ())
		if cdAttacker.eOwner == cdAttacker.eVisualOwner:
			szAttackerName = gc.getPlayer(cdAttacker.eOwner).getNameKey()
		else:
			szAttackerName = localText.getText("TXT_KEY_TRAIT_PLAYER_UNKNOWN", ())

		if (iIsAttacker == 0):				
			combatMessage = localText.getText("TXT_KEY_COMBAT_MESSAGE_HIT", (szDefenderName, cdDefender.sUnitName, iDamage, cdDefender.iCurrHitPoints, cdDefender.iMaxHitPoints))
			CyInterface().addCombatMessage(cdAttacker.eOwner,combatMessage)
			CyInterface().addCombatMessage(cdDefender.eOwner,combatMessage)
			if (cdDefender.iCurrHitPoints <= 0):
				combatMessage = localText.getText("TXT_KEY_COMBAT_MESSAGE_DEFEATED", (szAttackerName, cdAttacker.sUnitName, szDefenderName, cdDefender.sUnitName))
				CyInterface().addCombatMessage(cdAttacker.eOwner,combatMessage)
				CyInterface().addCombatMessage(cdDefender.eOwner,combatMessage)
		elif (iIsAttacker == 1):
			combatMessage = localText.getText("TXT_KEY_COMBAT_MESSAGE_HIT", (szAttackerName, cdAttacker.sUnitName, iDamage, cdAttacker.iCurrHitPoints, cdAttacker.iMaxHitPoints))
			CyInterface().addCombatMessage(cdAttacker.eOwner,combatMessage)
			CyInterface().addCombatMessage(cdDefender.eOwner,combatMessage)
			if (cdAttacker.iCurrHitPoints <= 0):
				combatMessage = localText.getText("TXT_KEY_COMBAT_MESSAGE_DEFEATED", (szDefenderName, cdDefender.sUnitName, szAttackerName, cdAttacker.sUnitName))
				CyInterface().addCombatMessage(cdAttacker.eOwner,combatMessage)
				CyInterface().addCombatMessage(cdDefender.eOwner,combatMessage)

	def onImprovementBuilt(self, argsList):
		'Improvement Built'
		iImprovement, iX, iY = argsList
		if (not self.__LOG_IMPROVEMENT):
			return
		CvUtil.pyPrint('Improvement %s was built at %d, %d'
			%(PyInfo.ImprovementInfo(iImprovement).getDescription(), iX, iY))

	def onImprovementDestroyed(self, argsList):
		'Improvement Destroyed'
		iImprovement, iOwner, iX, iY = argsList
		if (not self.__LOG_IMPROVEMENT):
			return
		CvUtil.pyPrint('Improvement %s was Destroyed at %d, %d'
			%(PyInfo.ImprovementInfo(iImprovement).getDescription(), iX, iY))

	def onRouteBuilt(self, argsList):
		'Route Built'
		iRoute, iX, iY = argsList
		if (not self.__LOG_IMPROVEMENT):
			return
		CvUtil.pyPrint('Route %s was built at %d, %d'
			%(gc.getRouteInfo(iRoute).getDescription(), iX, iY))

	def onPlotRevealed(self, argsList):
		'Plot Revealed'
		pPlot = argsList[0]
		iTeam = argsList[1]

	def onPlotFeatureRemoved(self, argsList):
		'Plot Revealed'
		pPlot = argsList[0]
		iFeatureType = argsList[1]
		pCity = argsList[2] # This can be null

	def onPlotPicked(self, argsList):
		'Plot Picked'
		pPlot = argsList[0]
		# <advc.007>
		if (not self.__LOG_PLOTPICKED):
			return # </advc.007>
		CvUtil.pyPrint('Plot was picked at %d, %d'
			%(pPlot.getX(), pPlot.getY()))

	def onNukeExplosion(self, argsList):
		'Nuke Explosion'
		pPlot, pNukeUnit = argsList
		
## Platyping's Promotions and Traits - Start ##		
## Energetic Trait Start ##
		# iPlayer = pNukeUnit.getOwner()
		# if iPlayer > -1:
			# pPlayer = gc.getPlayer(iPlayer)
			# if pPlayer.hasTrait(gc.getInfoTypeForString("TRAIT_ENERGETIC")):
				# iNukedUs = gc.getInfoTypeForString("MEMORY_NUKED_US")
				# iNukedFriend = gc.getInfoTypeForString("MEMORY_NUKED_FRIEND")
				# for iPlayerX in xrange(gc.getMAX_CIV_PLAYERS()):
					# pPlayerX = gc.getPlayer(iPlayerX)
					# if pPlayerX.isAlive():
						# pPlayerX.AI_changeMemoryCount(iPlayer, iNukedUs, - pPlayerX.AI_getMemoryCount(iPlayer, iNukedUs))
						# pPlayerX.AI_changeMemoryCount(iPlayer, iNukedFriend, - pPlayerX.AI_getMemoryCount(iPlayer, iNukedFriend))
				# iX = pPlot.getX()
				# iY = pPlot.getY()
				# nukerange = pNukeUnit.nukeRange()
				# for x in xrange (iX - nukerange, iX + nukerange + 1):
					# for y in xrange (iY - nukerange, iY + nukerange + 1):
						# nukePlot = CyMap().plot(x,y)
						# if nukePlot.isCity():
							# nukeCity = nukePlot.getPlotCity()
							# nukeCity.changeOccupationTimer(4)
## Energetic Trait End ##
## Platyping's Promotions and Traits - End ##

		# <advc.007>
		if (not self.__LOG_NUKEEXPLOSION):
			return # </advc.007>
		CvUtil.pyPrint('Nuke detonated at %d, %d'
			%(pPlot.getX(), pPlot.getY()))

	def onGotoPlotSet(self, argsList):
		'Nuke Explosion'
		pPlot, iPlayer = argsList

	def onBuildingBuilt(self, argsList):
		'Building Completed'
		pCity, iBuildingType = argsList
		game = gc.getGame()
		if ((not gc.getGame().isNetworkMultiPlayer()) and (pCity.getOwner() == gc.getGame().getActivePlayer()) and isWorldWonderClass(gc.getBuildingInfo(iBuildingType).getBuildingClassType())):
			# If this is a wonder...
			popupInfo = CyPopupInfo()
			popupInfo.setButtonPopupType(ButtonPopupTypes.BUTTONPOPUP_PYTHON_SCREEN)
			popupInfo.setData1(iBuildingType)
			popupInfo.setData2(pCity.getID())
			popupInfo.setData3(0)
			popupInfo.setText(u"showWonderMovie")
			popupInfo.addPopup(pCity.getOwner())

		CvAdvisorUtils.buildingBuiltFeats(pCity, iBuildingType)
		
## Platyping's Promotions and Traits - Start ##
## Dynamic Trait Start ##
		# if isWorldWonderClass(gc.getBuildingInfo(iBuildingType).getBuildingClassType()):
			# pPlayer = gc.getPlayer(pCity.getOwner())
			# if pPlayer.hasTrait(gc.getInfoTypeForString("TRAIT_DYNAMIC")):
				# pCity.changeFreeSpecialistCount(gc.getInfoTypeForString("SPECIALIST_ENGINEER"), 1)
## Dynamic Trait End ##
## Corrupt Trait ##
		# iPlayer = pCity.getOwner()
		# pPlayer = gc.getPlayer(iPlayer)
		# if pPlayer.hasTrait(gc.getInfoTypeForString("TRAIT_CORRUPT")):
			# pPlayer.changeGold(- pCity.getProductionNeeded() /10)
## Corrupt Trait ##
## Negligent Trait ##
		# if pPlayer.hasTrait(gc.getInfoTypeForString("TRAIT_NEGLIGENT")):
			# if CyGame().getSorenRandNum(100, "Collapse") < 8:
				# BuildingInfo = gc.getBuildingInfo(iBuildingType)
				# if not isLimitedWonderClass(BuildingInfo.getBuildingClassType()):
					# pCity.setNumRealBuilding(iBuildingType, 0)
					# CyInterface().addMessage(iPlayer,True,15,CyTranslator().getText("TXT_KEY_COLLAPSE",(BuildingInfo.getDescription(), pCity.getName(),)),'',0, BuildingInfo.getButton(),ColorTypes(11),pCity.getX(), pCity.getY(), True,True)
## Negligent Trait ##
## Platyping's Promotions and Traits - End ##

		if (not self.__LOG_BUILDING):
			return
		CvUtil.pyPrint('%s was finished by Player %d Civilization %s' 
			%(PyInfo.BuildingInfo(iBuildingType).getDescription(), pCity.getOwner(), gc.getPlayer(pCity.getOwner()).getCivilizationDescription(0)))
	
	def onProjectBuilt(self, argsList):
		'Project Completed'
		pCity, iProjectType = argsList
		game = gc.getGame()
		if ((not gc.getGame().isNetworkMultiPlayer()) and (pCity.getOwner() == gc.getGame().getActivePlayer())):
			popupInfo = CyPopupInfo()
			popupInfo.setButtonPopupType(ButtonPopupTypes.BUTTONPOPUP_PYTHON_SCREEN)
			popupInfo.setData1(iProjectType)
			popupInfo.setData2(pCity.getID())
			popupInfo.setData3(2)
			popupInfo.setText(u"showWonderMovie")
			popupInfo.addPopup(pCity.getOwner())
				
	def onSelectionGroupPushMission(self, argsList):
		'selection group mission'
		eOwner = argsList[0]
		eMission = argsList[1]
		iNumUnits = argsList[2]
		listUnitIds = argsList[3]
		
		if (not self.__LOG_PUSH_MISSION):
			return
		if pHeadUnit:
			CvUtil.pyPrint("Selection Group pushed mission %d" %(eMission))
	
	def onUnitMove(self, argsList):
		'unit move'
		pPlot,pUnit,pOldPlot = argsList
		player = PyPlayer(pUnit.getOwner())
		unitInfo = PyInfo.UnitInfo(pUnit.getUnitType())
		if (not self.__LOG_MOVEMENT):
			return
		if player and unitInfo:
			CvUtil.pyPrint('Player %d Civilization %s unit %s is moving to %d, %d' 
				%(player.getID(), player.getCivilizationName(), unitInfo.getDescription(), 
				pUnit.getX(), pUnit.getY()))

	def onUnitSetXY(self, argsList):
		'units xy coords set manually'
		pPlot,pUnit = argsList
		player = PyPlayer(pUnit.getOwner())
		unitInfo = PyInfo.UnitInfo(pUnit.getUnitType())
		if (not self.__LOG_MOVEMENT):
			return
		
	def onUnitCreated(self, argsList):
		'Unit Completed'
		unit = argsList[0]
		player = PyPlayer(unit.getOwner())
		if (not self.__LOG_UNITBUILD):
			return

	def onUnitBuilt(self, argsList):
		'Unit Completed'
		city = argsList[0]
		unit = argsList[1]
		player = PyPlayer(city.getOwner())
		pPlayer = gc.getPlayer(city.getOwner())
		
# Equalis Unique Trait ##
		# if pPlayer.getLeaderType() == gc.getInfoTypeForString("LEADER_EQUALIS"):
			# if unit.getUnitCombatType() == gc.getInfoTypeForString('UNITCOMBAT_ARCHER') or unit.getUnitCombatType() == gc.getInfoTypeForString('UNITCOMBAT_MOUNTED'):
				# unit.setHasPromotion(gc.getInfoTypeForString("PROMOTION_REGENERATION"), true)
# Equalis Unique Trait ##

# Evening Love Unique Trait ##
		# if pPlayer.getLeaderType() == gc.getInfoTypeForString("LEADER_EVENINGLOVE"):
			# if unit.getUnitCombatType() == gc.getInfoTypeForString('UNITCOMBAT_MOUNTED'):
				# unit.setHasPromotion(gc.getInfoTypeForString("PROMOTION_"), true)
# Evening Love Unique Trait ##

# Rusa Imperio Unique Trait ##
		# if pPlayer.getLeaderType() == gc.getInfoTypeForString("LEADER_RUSA"):
			# if unit.getUnitCombatType() == gc.getInfoTypeForString('UNITCOMBAT_MOUNTED') or unit.getUnitCombatType() == gc.getInfoTypeForString('UNITCOMBAT_GUN'):
				# unit.setHasPromotion(gc.getInfoTypeForString("PROMOTION_RAIDER"), true)
# Rusa Imperio Unique Trait ##

# Rusa Imperio Unique Trait ##
		# if pPlayer.getLeaderType() == gc.getInfoTypeForString("LEADER_RUSA"):
			# if unit.getUnitCombatType() == gc.getInfoTypeForString('UNITCOMBAT_GUN'):
				# unit.setHasPromotion(gc.getInfoTypeForString("PROMOTION_SPOILS_OF_WAR"), true)
# Rusa Imperio Unique Trait ##

## Platyping's Promotions and Traits - Start ##
## Devotee Start ##
		if unit.getUnitCombatType() > -1:
			if city.isHolyCity():
				unit.setHasPromotion(gc.getInfoTypeForString("PROMOTION_DEVOTEE"), true)
## Economist Start ##
			if city.isHeadquarters():
				unit.setHasPromotion(gc.getInfoTypeForString("PROMOTION_ECONOMIST"), true)
## Nobility Start ##
			if city.isGovernmentCenter():
				unit.setHasPromotion(gc.getInfoTypeForString("PROMOTION_NOBILITY"), true)
## Energetic Trait Start ##
		# pPlayer = gc.getPlayer(unit.getOwner())
		# if pPlayer.hasTrait(gc.getInfoTypeForString("TRAIT_ENERGETIC")):
			# if unit.getSpecialUnitType() == gc.getInfoTypeForString("SPECIALUNIT_MISSILE"):
				# unit.setHasPromotion(gc.getInfoTypeForString("PROMOTION_RANGE1"), True)
				# unit.setHasPromotion(gc.getInfoTypeForString("PROMOTION_RANGE2"), True)
			# if unit.specialCargo() == gc.getInfoTypeForString("SPECIALUNIT_MISSILE"):
				# unit.changeCargoSpace(2)
## Faithful Trait Start ##
		if city.isHolyCity():
			if pPlayer.hasTrait(gc.getInfoTypeForString("TRAIT_FAITHFUL")):
				city.addProductionExperience(unit, True)
## Perceptive Trait Start ##
		if gc.getUnitInfo(unit.getUnitType()).isSpy():
			if pPlayer.hasTrait(gc.getInfoTypeForString("TRAIT_PERCEPTIVE")):
				unit.setHasPromotion(gc.getInfoTypeForString("PROMOTION_MORALE"), True)
				unit.setHasPromotion(gc.getInfoTypeForString("PROMOTION_SENTRY"), True)
## Lazy Trait ##
		# pPlayer = gc.getPlayer(city.getOwner())
		# if pPlayer.hasTrait(gc.getInfoTypeForString("TRAIT_LAZY")):
			# unit.setExperience(unit.getExperience() * 3/4, 99999)
## Lazy Trait ##
## Platyping's Promotions and Traits - End ##

		CvAdvisorUtils.unitBuiltFeats(city, unit)
		
		if (not self.__LOG_UNITBUILD):
			return
		CvUtil.pyPrint('%s was finished by Player %d Civilization %s' 
			%(PyInfo.UnitInfo(unit.getUnitType()).getDescription(), player.getID(), player.getCivilizationName()))
	
	def onUnitKilled(self, argsList):
		'Unit Killed'
		unit, iAttacker = argsList
		player = PyPlayer(unit.getOwner())
		attacker = PyPlayer(iAttacker)
		
## Platyping's Promotions and Traits - Start ##
		iPlayer = unit.getOwner()
		pPlayer = gc.getPlayer(iPlayer)
		RealDeath = ["PROMOTION_REBIRTH", "PROMOTION_LAST_WISH", "PROMOTION_LEGEND", "PROMOTION_INTERCEPTION3", "PROMOTION_ENTERTAINER"]
		DeathEffect = ["PROMOTION_BLOOD_PACT", "PROMOTION_AMBASSADOR",  "PROMOTION_BANSHEE_CRY", "PROMOTION_RETRIBUTION", "PROMOTION_DESPAIR", "PROMOTION_STUPIFY"]

# Aqasha Unique Trait ##
		# if not (pPlayer.getLeaderType() == gc.getInfoTypeForString("LEADER_AQASHA")) and unit.getUnitCombatType() > -1:
			# if not unit.isHasPromotion(gc.getInfoTypeForString("PROMOTION_REBIRTH")) and not unit.isAnimal():
				# pAttacker = gc.getPlayer(iAttacker)
				# if pAttacker.getLeaderType() == gc.getInfoTypeForString("LEADER_AQASHA") and CyGame().getSorenRandNum((3*unit.getLevel()), "Unique Ability Rand Chance") == 0:
					# pPlot = unit.plot()
					# if pPlot.getOwner() == iAttacker:
						# pReviveCity = pPlot.getWorkingCity()
						# if pReviveCity.isNone() or (pReviveCity.getOwner() != iAttacker):
							# pReviveCity = pAttacker.getCapitalCity()
						# if not pReviveCity.isNone():
							# pNewUnit = pAttacker.initUnit(unit.getUnitType(), pReviveCity.getX(), pReviveCity.getY(), UnitAITypes.NO_UNITAI, DirectionTypes.NO_DIRECTION)
							# unit.setDamage(0, false)
							# pNewUnit.convert(unit)
							# unit.setLeaderUnitType(-1)
							# pNewUnit.setBaseCombatStr(unit.baseCombatStr())
# Aqasha Unique Trait ##

# Nerath Unique Trait ##
		# if not (pPlayer.getLeaderType() == gc.getInfoTypeForString("LEADER_NERATH")) and unit.getUnitCombatType() > -1:
			# if not unit.isHasPromotion(gc.getInfoTypeForString("PROMOTION_REBIRTH")) and not unit.isAnimal():
				# pAttacker = gc.getPlayer(iAttacker)
				# if pAttacker.getLeaderType() == gc.getInfoTypeForString("LEADER_NERATH") and CyGame().getSorenRandNum((3*unit.getLevel()), "Unique Ability Rand Chance") == 0:
					# pPlot = unit.plot()
					# if pPlot.getOwner() == iAttacker:
						# pReviveCity = pPlot.getWorkingCity()
						# if pReviveCity.isNone() or (pReviveCity.getOwner() != iAttacker):
							# pReviveCity = pAttacker.getCapitalCity()
						# if not pReviveCity.isNone():
							# pNewUnit = pAttacker.initUnit(unit.getUnitType(), pReviveCity.getX(), pReviveCity.getY(), UnitAITypes.NO_UNITAI, DirectionTypes.NO_DIRECTION)
							# unit.setDamage(0, false)
							# pNewUnit.convert(unit)
							# unit.setLeaderUnitType(-1)
							# pNewUnit.setBaseCombatStr(unit.baseCombatStr())
# Nerath Unique Trait ##

## Rebirth Flames ##
		if unit.isHasPromotion(gc.getInfoTypeForString("PROMOTION_REBIRTH")):
			if CyGame().getSorenRandNum(3, "Revive") == 0:
				pReviveCity = pPlayer.getCapitalCity()
				if pReviveCity:
					pNewUnit = pPlayer.initUnit(unit.getUnitType(), pReviveCity.getX(), pReviveCity.getY(), UnitAITypes.NO_UNITAI, DirectionTypes.NO_DIRECTION)
					unit.setDamage(0, false)
					pNewUnit.convert(unit)
					for iDeath in RealDeath:
						unit.setHasPromotion(gc.getInfoTypeForString(iDeath), false)
					for iPromotion in xrange(gc.getNumPromotionInfos()):
						if gc.getPromotionInfo(iPromotion).getType().startswith("ARTIFACT"):
							unit.setHasPromotion(iPromotion, false)
					unit.setLeaderUnitType(-1)
					pNewUnit.setBaseCombatStr(unit.baseCombatStr())
					pNewUnit.finishMoves()
					CyInterface().addMessage(iPlayer,false,10,CyTranslator().getText("TXT_REBIRTH_FLAMES",(pNewUnit.getName(),pReviveCity.getName(),)),'',0, gc.getPromotionInfo(gc.getInfoTypeForString("PROMOTION_REBIRTH")).getButton(),ColorTypes(11),pNewUnit.getX(), pNewUnit.getY(), true,true)
## Last Wish Start ##
		if unit.isHasPromotion(gc.getInfoTypeForString("PROMOTION_LAST_WISH")):
			Wish = []
			DeathXP = unit.getExperience() * 2
			pPlot = unit.plot()
			for iUnit in xrange(pPlot.getNumUnits()):
				pUnit = pPlot.getUnit(iUnit)
				if pUnit.isNone(): continue
				if pUnit.isDead(): continue
				if pUnit.getUnitCombatType() == -1: continue
				if pUnit.getOwner() == iPlayer:
					Wish.append(pUnit)
			for i in xrange(len(Wish)):
				Wish[i].changeExperience(DeathXP /len(Wish),9999,False,False,False)
				if i < DeathXP % len(Wish):
					Wish[i].changeExperience(1,9999,False,False,False)
## Blood Pact Start ##
		if unit.isHasPromotion(gc.getInfoTypeForString("PROMOTION_BLOOD_PACT")):
			pPlot = unit.plot()
			for iUnit in xrange(pPlot.getNumUnits()):
				pUnit = pPlot.getUnit(iUnit)
				if pUnit.isNone(): continue
				if pUnit.isDead(): continue
				if pUnit.getOwner() == iPlayer:	
					pUnit.changeDamage(-(unit.getLevel() * 10), false)
## Interception III Start ##
		if unit.isHasPromotion(gc.getInfoTypeForString("PROMOTION_INTERCEPTION3")):
			pTeam = gc.getTeam(pPlayer.getTeam())
			pTeam.changeNukeInterception(-2)
## Entertainer Start ##
		if unit.isHasPromotion(gc.getInfoTypeForString("PROMOTION_ENTERTAINER")):
			pPlayer.changeExtraHappiness(-1)
## Legend Start ##
		if unit.isHasPromotion(gc.getInfoTypeForString("PROMOTION_LEGEND")):
			pPlayer.changeAnarchyTurns(unit.getLevel())
			CyInterface().addMessage(iPlayer,true,10,CyTranslator().getText("TXT_MOURNING",()),'',0,'',-1,-1,-1,false,false)
## Ambasador Start ##
		if unit.isHasPromotion(gc.getInfoTypeForString("PROMOTION_AMBASSADOR")):
			pPlayer2 = gc.getPlayer(iAttacker)
			iTeam2 = pPlayer2.getTeam()
			for iTeamX in xrange(gc.getMAX_CIV_TEAMS()):
				pTeamX = gc.getTeam(iTeamX)
				pLeaderX = gc.getPlayer(pTeamX.getLeaderID())
				if pTeamX.canDeclareWar(iTeam2):
					if CyGame().getSorenRandNum(5, "Declare War") > 3 * pLeaderX.AI_getAttitude(iAttacker) - pLeaderX.AI_getAttitude(iPlayer):
						pTeamX.declareWar(iTeam2, true, -1)
## Pessimistic Trait ##
		# iPlayer = unit.getOwner()
		# pPlayer = gc.getPlayer(iPlayer)
		# if pPlayer.hasTrait(gc.getInfoTypeForString("TRAIT_PESSIMISITC")):
			# if CyGame().getSorenRandNum(25, "Anarchy") == 0:
				# pPlayer.changeAnarchyTurns(4)
## Pessimistic Trait ##
## Platyping's Promotions and Traits - End ##

		if (not self.__LOG_UNITKILLED):
			return
		CvUtil.pyPrint('Player %d Civilization %s Unit %s was killed by Player %d' 
			%(player.getID(), player.getCivilizationName(), PyInfo.UnitInfo(unit.getUnitType()).getDescription(), attacker.getID()))

	def onUnitLost(self, argsList):
		'Unit Lost'
		unit = argsList[0]
		player = PyPlayer(unit.getOwner())
		if (not self.__LOG_UNITLOST):
			return
		CvUtil.pyPrint('%s was lost by Player %d Civilization %s' 
			%(PyInfo.UnitInfo(unit.getUnitType()).getDescription(), player.getID(), player.getCivilizationName()))
	
	def onUnitPromoted(self, argsList):
		'Unit Promoted'
		pUnit, iPromotion = argsList
		player = PyPlayer(pUnit.getOwner())

## Platyping's Promotions and Traits - Start ##
		pPlayer = gc.getPlayer(pUnit.getOwner())
## AI Promotion ##
		if not pPlayer.isHuman() and not pUnit.isFighting():
			pUnit.setHasPromotion(iPromotion, false)
			if CyGame().getSorenRandNum(5, "Platy Promotion") == 0:
				Promotions = []
				for iPromo in xrange(gc.getNumPromotionInfos()):
					if pUnit.canAcquirePromotion(iPromo):
						if len(gc.getPromotionInfo(iPromo).getHelp()) == 0: continue
						Promotions.append(iPromo)
				if len(Promotions) > 0:
					chosenPromotion = CyGame().getSorenRandNum(len(Promotions), "which promotion")
					iPromotion = Promotions[chosenPromotion]
			pUnit.setHasPromotion(iPromotion, true)
## Enlightenment Start ##
		if iPromotion == gc.getInfoTypeForString("PROMOTION_ENLIGHTENMENT"):
			pUnit.changeLevel(-1)
			pCurrentXP = min(pUnit.getExperience(), pUnit.experienceNeeded())
			pUnit.changeLevel(2)
			pUnit.changeExperience(pUnit.experienceNeeded() - pCurrentXP, 9999, false, false, false)
			pUnit.changeLevel(-1)
			pUnit.setPromotionReady(true)
## Interception III Start ##
		elif iPromotion == gc.getInfoTypeForString("PROMOTION_INTERCEPTION3"):
			pTeam = gc.getTeam(pPlayer.getTeam())
			pTeam.changeNukeInterception(2)
## Entertainer Start ##
		elif iPromotion == gc.getInfoTypeForString("PROMOTION_ENTERTAINER"):
			pPlayer.changeExtraHappiness(1)
## Shapeshifter Start ##
		elif iPromotion == gc.getInfoTypeForString("PROMOTION_SHAPESHIFTER"):
			Shapeshift = ["PROMOTION_EARTH_ELEMENTAL", "PROMOTION_WATER_ELEMENTAL", "PROMOTION_FIRE_ELEMENTAL", "PROMOTION_AIR_ELEMENTAL"]
			pUnit.setHasPromotion(gc.getInfoTypeForString(Shapeshift[CyGame().getSorenRandNum(4, "New Form")]), true)
## Destiny Start ##
		if pUnit.isHasPromotion(gc.getInfoTypeForString("PROMOTION_DESTINY")):
			if CyGame().getSorenRandNum(4, "Destiny") == 0:
				pUnit.changeLevel(-1)
				pUnit.setPromotionReady(true)
## Heal Start ##
		if pUnit.isHasPromotion(gc.getInfoTypeForString("PROMOTION_HEAL")):
			pPlot = pUnit.plot()
			for iloopUnit in xrange(pPlot.getNumUnits()):
				ploopUnit = pPlot.getUnit(iloopUnit)
				if not ploopUnit.isNone():
					if ploopUnit.getOwner() == pUnit.getOwner():
						ploopUnit.setDamage(ploopUnit.getDamage() - 3 * pUnit.getLevel(), false)
## Grandmaster Start ##
		if not pUnit.isHasPromotion(gc.getInfoTypeForString("PROMOTION_GRANDMASTER")):
			Grandmaster = ["PROMOTION_AMBUSH", "PROMOTION_CHARGE", "PROMOTION_COVER", "PROMOTION_FORMATION", "PROMOTION_PINCH", "PROMOTION_SHOCK"]
			iCombat = 0
			for i in Grandmaster:
				CombatPromotion = gc.getInfoTypeForString(i)
				if pUnit.isHasPromotion(CombatPromotion):
					iCombat += 1
				if iCombat == 3:
					pUnit.setHasPromotion(gc.getInfoTypeForString("PROMOTION_GRANDMASTER"), true)
					break
## Banshee Cry Start ##
		if pUnit.getLevel() == 5:
			pUnit.setHasPromotion(gc.getInfoTypeForString("PROMOTION_CURSE"), false)
## Legend Start ##
		elif pUnit.getLevel() == 12:
			pUnit.setHasPromotion(gc.getInfoTypeForString("PROMOTION_LEGEND"), true)
## Dim-Witted Trait ##
		# pPlayer = gc.getPlayer(pUnit.getOwner())
		# if pPlayer.hasTrait(gc.getInfoTypeForString("TRAIT_DIM_WITTED")):
			# pUnit.setPromotionReady(False)
## Dim-Witted Trait ##
## Platyping's Promotions and Traits - End ##

		if (not self.__LOG_UNITPROMOTED):
			return
		CvUtil.pyPrint('Unit Promotion Event: %s - %s' %(player.getCivilizationName(), pUnit.getName(),))
	
	def onUnitSelected(self, argsList):
		'Unit Selected'
		unit = argsList[0]
		player = PyPlayer(unit.getOwner())
		if (not self.__LOG_UNITSELECTED):
			return
		CvUtil.pyPrint('%s was selected by Player %d Civilization %s' 
			%(PyInfo.UnitInfo(unit.getUnitType()).getDescription(), player.getID(), player.getCivilizationName()))
	
	def onUnitRename(self, argsList):
		'Unit is renamed'
		pUnit = argsList[0]
		if (pUnit.getOwner() == gc.getGame().getActivePlayer()):
			self.__eventEditUnitNameBegin(pUnit)
	
	def onUnitPillage(self, argsList):
		'Unit pillages a plot'
		pUnit, iImprovement, iRoute, iOwner = argsList
		iPlotX = pUnit.getX()
		iPlotY = pUnit.getY()
		pPlot = CyMap().plot(iPlotX, iPlotY)

## Platyping's Promotions and Traits - Start ##
## Raider Start ##
		if pUnit.isHasPromotion(gc.getInfoTypeForString("PROMOTION_RAIDER")):
			pUnit.changeMoves(-30)
		if pPlot.getOwner() != iOwner:
			if pUnit.isHasPromotion(gc.getInfoTypeForString("PROMOTION_RAIDER")):
				pCity = CyMap().findCity(pPlot.getX(), pPlot.getY(), iOwner, -1, false, false, -1, -1, CyCity())
				if iImprovement > -1 and pCity:
					iFood = pPlot.calculateImprovementYieldChange(iImprovement, YieldTypes.YIELD_FOOD, pPlot.getOwner(), false) * pUnit.getLevel()
					iProduction = pPlot.calculateImprovementYieldChange(iImprovement, YieldTypes.YIELD_PRODUCTION, pPlot.getOwner(), false) * pUnit.getLevel()
					iCommerce = pPlot.calculateImprovementYieldChange(iImprovement, YieldTypes.YIELD_COMMERCE, pPlot.getOwner(), false) * pUnit.getLevel()
					if iFood > 0:
						pCity.changeFood(iFood)
						CyInterface().addMessage(iOwner,true,10,CyTranslator().getText("TXT_PILLAGE_FOOD",(iFood, pCity.getName(),)),'',0,'',-1, -1, -1, true,true)
					if iProduction > 0:
						pCity.changeProduction(iProduction)
						CyInterface().addMessage(iOwner,true,10,CyTranslator().getText("TXT_PILLAGE_PRODUCTION",(iProduction, pCity.getName(),)),'',0,'',-1, -1, -1, true,true)
					if iCommerce > 0:
						pCity.changeCulture(iOwner, iCommerce, true)
						CyInterface().addMessage(iOwner,true,10,CyTranslator().getText("TXT_PILLAGE_CULTURE",(iCommerce, pCity.getName(),)),'',0,'',-1, -1, -1, true,true)
## Toxic Cloud Start ##
			if pUnit.isHasPromotion(gc.getInfoTypeForString("PROMOTION_TOXIC_CLOUD")):
				if pPlot.getFeatureType() == -1:
					pPlot.setFeatureType(gc.getInfoTypeForString("FEATURE_FALLOUT"), -1)
## Cleave Start ##
			if pUnit.isHasPromotion(gc.getInfoTypeForString("PROMOTION_CLEAVE")):
				for x in xrange(iPlotX - 1, iPlotX + 2):
					for y in xrange(iPlotY - 1, iPlotY + 2):
						if x != iPlotX or y != iPlotY:
							pPlot2 = CyMap().plot(x, y)
							if not pPlot2.isWater() and pPlot2.getOwner() == pPlot.getOwner():
								if CyGame().getSorenRandNum(2, "Pillage") == 0:
									currentImprovement = pPlot2.getImprovementType()
									if currentImprovement == -1: continue
									pPlot2.setImprovementType(gc.getImprovementInfo(currentImprovement).getImprovementPillage())
## Platyping's Promotions and Traits - End ##

		if (not self.__LOG_UNITPILLAGE):
			return
		CvUtil.pyPrint("Player %d's %s pillaged improvement %d and route %d at plot at (%d, %d)" 
			%(iOwner, PyInfo.UnitInfo(pUnit.getUnitType()).getDescription(), iImprovement, iRoute, iPlotX, iPlotY))
	
	def onUnitSpreadReligionAttempt(self, argsList):
		'Unit tries to spread religion to a city'
		pUnit, iReligion, bSuccess = argsList
		
		iX = pUnit.getX()
		iY = pUnit.getY()
		pPlot = CyMap().plot(iX, iY)
		pCity = pPlot.getPlotCity()
	
	def onUnitGifted(self, argsList):
		'Unit is gifted from one player to another'
		pUnit, iGiftingPlayer, pPlotLocation = argsList
		
## Platyping's Promotions and Traits - Start ##
## Interception III Start ##
		pPlayer = gc.getPlayer(pUnit.getOwner())
		pPlayer2 = gc.getPlayer(iGiftingPlayer)
		if pUnit.isHasPromotion(gc.getInfoTypeForString("PROMOTION_INTERCEPTION3")):
			pTeam = gc.getTeam(pPlayer.getTeam())
			pTeam2 = gc.getTeam(pPlayer2.getTeam())
			pTeam.changeNukeInterception(2)
			pTeam2.changeNukeInterception(-2)
## Entertainer Start ##
		if pUnit.isHasPromotion(gc.getInfoTypeForString("PROMOTION_ENTERTAINER")):
			pPlayer2 = gc.getPlayer(iGiftingPlayer)
			pPlayer2.changeExtraHappiness(-1)
## Platyping's Promotions and Traits - End ##

	def onUnitBuildImprovement(self, argsList):
		'Unit begins enacting a Build (building an Improvement or Route)'
		pUnit, iBuild, bFinished = argsList

	def onGoodyReceived(self, argsList):
		'Goody received'
		iPlayer, pPlot, pUnit, iGoodyType = argsList

## Platyping's Promotions and Traits - Start ##
## Adventurous Trait Start ##
		pPlayer = gc.getPlayer(iPlayer)
		if pPlayer.hasTrait(gc.getInfoTypeForString("TRAIT_ADVENTUROUS")):
			Goody = []
			for iGoody in xrange(gc.getNumGoodyInfos()):
				if iGoody == gc.getInfoTypeForString("GOODY_SETTLER"): continue
				if iGoody == gc.getInfoTypeForString("GOODY_WORKER"): continue
				if pPlayer.canReceiveGoody(pPlot, iGoody, pUnit):
					Goody.append(iGoody)
			if len(Goody) > 0:
				pPlayer.receiveGoody(pPlot, Goody[CyGame().getSorenRandNum(len(Goody), "Which Goody")], pUnit)
## Adventurous Trait End ##
## Platyping's Promotions and Traits - End ##
		
		if (not self.__LOG_GOODYRECEIVED):
			return
		CvUtil.pyPrint('%s received a goody' %(gc.getPlayer(iPlayer).getCivilizationDescription(0)),)
	
	def onGreatPersonBorn(self, argsList):
		'Unit Promoted'
		pUnit, iPlayer, pCity = argsList
		player = PyPlayer(iPlayer)
		if pUnit.isNone() or pCity.isNone():
			return

## Platyping's Promotions and Traits - Start ##			
## Faithful Trait Start ##
		# pPlayer = gc.getPlayer(iPlayer)
			# if pPlayer.hasTrait(gc.getInfoTypeForString("TRAIT_FAITHFUL")):
				# if pUnit.getUnitType() == gc.getInfoTypeForString("UNIT_PROPHET"):
					# pPlayer.changeGoldenAgeTurns(pPlayer.getGoldenAgeLength())
## Perceptive Trait Start ##
		# if pPlayer.hasTrait(gc.getInfoTypeForString("TRAIT_PERCEPTIVE")):
			# if pUnit.getUnitType() == gc.getInfoTypeForString("UNIT_GREAT_SPY"):
				# pUnit.setHasPromotion(gc.getInfoTypeForString("PROMOTION_MORALE"), True)
				# pUnit.setHasPromotion(gc.getInfoTypeForString("PROMOTION_SENTRY"), True)
## Perceptive Trait End ##
## Irrational Trait ##
		# pPlayer = gc.getPlayer(iPlayer)
		# if pPlayer.hasTrait(gc.getInfoTypeForString("TRAIT_IRRATIONAL")):
			# (loopCity, iter) = pPlayer.firstCity(False)
			# while(loopCity):
				# loopCity.changeGreatPeopleProgress(- loopCity.getGreatPeopleProgress() /2)
				# (loopCity, iter) = pPlayer.nextCity(iter, False)
## Irrational Trait ##
## Platyping's Promotions and Traits - End ##

		if (not self.__LOG_GREATPERSON):
			return
		CvUtil.pyPrint('A %s was born for %s in %s' %(pUnit.getName(), player.getCivilizationName(), pCity.getName()))
	
	def onTechAcquired(self, argsList):
		'Tech Acquired'
		iTechType, iTeam, iPlayer, bAnnounce = argsList
		# Note that iPlayer may be NULL (-1) and not a refer to a player object
		
## Platyping's Promotions and Traits - Start ##
## Scientific Trait Start ##
		pTeam = gc.getTeam(iTeam)
		bNewEra = True
		for iTech in xrange(gc.getNumTechInfos()):
			if gc.getTechInfo(iTech).getEra() < gc.getTechInfo(iTechType).getEra(): continue
			if iTech == iTechType: continue
			if pTeam.isHasTech(iTech):
				bNewEra = False
				break
		if bNewEra:
			for iPlayerX in xrange(gc.getMAX_CIV_PLAYERS()):
				pPlayerX = gc.getPlayer(iPlayerX)
				if pPlayerX.isAlive() and pPlayerX.getTeam() == iTeam:
					if pPlayerX.hasTrait(gc.getInfoTypeForString("TRAIT_SCIENTIFIC")):
						if pPlayerX.getNumCities() < 1: continue
						pCapital = pPlayerX.getCapitalCity()
						pNewUnit = pPlayerX.initUnit(gc.getInfoTypeForString("UNIT_SCIENTIST"), pCapital.getX(), pCapital.getY(), UnitAITypes.NO_UNITAI, DirectionTypes.NO_DIRECTION)
## Traditional Trait ##
					if pPlayerX.hasTrait(gc.getInfoTypeForString("TRAIT_TRADITIONAL")):
						(loopCity, iter) = pPlayerX.firstCity(False)
						while(loopCity):
							loopCity.setBuildingYieldChange(gc.getInfoTypeForString("BUILDINGCLASS_PALACE"), YieldTypes.YIELD_FOOD, (pPlayerX.getCurrentEra() + 1) * 2)
							loopCity.setBuildingYieldChange(gc.getInfoTypeForString("BUILDINGCLASS_PALACE"), YieldTypes.YIELD_PRODUCTION, (pPlayerX.getCurrentEra() + 1) * 2)
							(loopCity, iter) = pPlayerX.nextCity(iter, False)
## Platyping's Promotions and Traits - End ##

		# Show tech splash when applicable
 		# (advc - note: CvTeam::setHasTech may now also show the tech splash)
		if (iPlayer > -1 and bAnnounce and not CyInterface().noTechSplash()):
			if (gc.getGame().isFinalInitialized() and not gc.getGame().GetWorldBuilderMode()):
				if ((not gc.getGame().isNetworkMultiPlayer()) and (iPlayer == gc.getGame().getActivePlayer())):
					popupInfo = CyPopupInfo()
					popupInfo.setButtonPopupType(ButtonPopupTypes.BUTTONPOPUP_PYTHON_SCREEN)
					popupInfo.setData1(iTechType)
					popupInfo.setText(u"showTechSplash")
					popupInfo.addPopup(iPlayer)
				
		if (not self.__LOG_TECH):
			return
		CvUtil.pyPrint('%s was finished by Team %d' 
			%(PyInfo.TechnologyInfo(iTechType).getDescription(), iTeam))
	
	def onTechSelected(self, argsList):
		'Tech Selected'
		iTechType, iPlayer = argsList
		if (not self.__LOG_TECH):
			return
		CvUtil.pyPrint('%s was selected by Player %d' %(PyInfo.TechnologyInfo(iTechType).getDescription(), iPlayer))
	
	def onReligionFounded(self, argsList):
		'Religion Founded'
		iReligion, iFounder = argsList
		player = PyPlayer(iFounder)
		
		iCityId = gc.getGame().getHolyCity(iReligion).getID()
		if (gc.getGame().isFinalInitialized() and not gc.getGame().GetWorldBuilderMode()):
			if ((not gc.getGame().isNetworkMultiPlayer()) and (iFounder == gc.getGame().getActivePlayer())):
				popupInfo = CyPopupInfo()
				popupInfo.setButtonPopupType(ButtonPopupTypes.BUTTONPOPUP_PYTHON_SCREEN)
				popupInfo.setData1(iReligion)
				popupInfo.setData2(iCityId)
				popupInfo.setData3(1)
				popupInfo.setText(u"showWonderMovie")
				popupInfo.addPopup(iFounder)
		
		if (not self.__LOG_RELIGION):
			return
		CvUtil.pyPrint('Player %d Civilization %s has founded %s'
			%(iFounder, player.getCivilizationName(), gc.getReligionInfo(iReligion).getDescription()))

	def onReligionSpread(self, argsList):
		'Religion Has Spread to a City'
		iReligion, iOwner, pSpreadCity = argsList
		player = PyPlayer(iOwner)
		
## Platyping's Promotions and Traits - Start ##
## Intolerant Trait ##
		# pPlayer = gc.getPlayer(iOwner)
		# if pPlayer.hasTrait(gc.getInfoTypeForString("TRAIT_INTOLERANT")):
			# iStateReligion = pPlayer.getStateReligion()
			# if iStateReligion > -1 and iReligion != iStateReligion:
				# pSpreadCity.changeOccupationTimer(2)
## Intolerant Trait ##
## Platyping's Promotions and Traits - End ##
		
		if (not self.__LOG_RELIGIONSPREAD):
			return
		CvUtil.pyPrint('%s has spread to Player %d Civilization %s city of %s'
			%(gc.getReligionInfo(iReligion).getDescription(), iOwner, player.getCivilizationName(), pSpreadCity.getName()))

	def onReligionRemove(self, argsList):
		'Religion Has been removed from a City'
		iReligion, iOwner, pRemoveCity = argsList
		player = PyPlayer(iOwner)
		if (not self.__LOG_RELIGIONSPREAD):
			return
		CvUtil.pyPrint('%s has been removed from Player %d Civilization %s city of %s'
			%(gc.getReligionInfo(iReligion).getDescription(), iOwner, player.getCivilizationName(), pRemoveCity.getName()))
				
	def onCorporationFounded(self, argsList):
		'Corporation Founded'
		iCorporation, iFounder = argsList
		player = PyPlayer(iFounder)
		
		if (not self.__LOG_RELIGION):
			return
		CvUtil.pyPrint('Player %d Civilization %s has founded %s'
			%(iFounder, player.getCivilizationName(), gc.getCorporationInfo(iCorporation).getDescription()))

	def onCorporationSpread(self, argsList):
		'Corporation Has Spread to a City'
		iCorporation, iOwner, pSpreadCity = argsList
		player = PyPlayer(iOwner)
		if (not self.__LOG_RELIGIONSPREAD):
			return
		CvUtil.pyPrint('%s has spread to Player %d Civilization %s city of %s'
			%(gc.getCorporationInfo(iCorporation).getDescription(), iOwner, player.getCivilizationName(), pSpreadCity.getName()))

	def onCorporationRemove(self, argsList):
		'Corporation Has been removed from a City'
		iCorporation, iOwner, pRemoveCity = argsList
		player = PyPlayer(iOwner)
		if (not self.__LOG_RELIGIONSPREAD):
			return
		CvUtil.pyPrint('%s has been removed from Player %d Civilization %s city of %s'
			%(gc.getReligionInfo(iReligion).getDescription(), iOwner, player.getCivilizationName(), pRemoveCity.getName()))
				
	def onGoldenAge(self, argsList):
		'Golden Age'
		iPlayer = argsList[0]
		player = PyPlayer(iPlayer)
		
## Platyping's Promotions and Traits - Start ##
## Agricultural Trait Start ##
		# pPlayer = gc.getPlayer(iPlayer)
		# if pPlayer.hasTrait(gc.getInfoTypeForString("TRAIT_AGRICULTURAL")):
			# (loopCity, iter) = pPlayer.firstCity(False)
			# while(loopCity):
				# loopCity.changeBaseYieldRate(YieldTypes.YIELD_FOOD, 5)
				# (loopCity, iter) = pPlayer.nextCity(iter, False)
## Agricultural Trait End ##
## Jealous Trait ##
		# for iPlayerX in xrange(gc.getMAX_CIV_PLAYERS()):
			# if iPlayerX == iPlayer: continue
			# pPlayerX = gc.getPlayer(iPlayerX)
			# if pPlayerX.isAlive():
				# if pPlayerX.hasTrait(gc.getInfoTypeForString("TRAIT_JEALOUS")):
					# if gc.getTeam(pPlayerX.getTeam()).isHasMet(gc.getPlayer(iPlayer).getTeam()):
						# (loopCity, iter) = pPlayerX.firstCity(False)
						# while(loopCity):
							# loopCity.changeEspionageHappinessCounter(8)
							# (loopCity, iter) = pPlayerX.nextCity(iter, False)
## Jealous Trait ##
## Platyping's Promotions and Traits - End ##
		
		if (not self.__LOG_GOLDENAGE):
			return
		CvUtil.pyPrint('Player %d Civilization %s has begun a golden age'
			%(iPlayer, player.getCivilizationName()))

	def onEndGoldenAge(self, argsList):
		'End Golden Age'
		iPlayer = argsList[0]
		player = PyPlayer(iPlayer)
		
## Platyping's Promotions and Traits - Start ##
## Agricultural Trait Start ##
		# pPlayer = gc.getPlayer(iPlayer)
		# if pPlayer.hasTrait(gc.getInfoTypeForString("TRAIT_AGRICULTURAL")):
			# (loopCity, iter) = pPlayer.firstCity(False)
			# while(loopCity):
				# loopCity.changeBaseYieldRate(YieldTypes.YIELD_FOOD, -5)
				# (loopCity, iter) = pPlayer.nextCity(iter, False)
## Agricultural Trait End ##
## Sentimental Trait ##
		# pPlayer = gc.getPlayer(iPlayer)
		# if pPlayer.hasTrait(gc.getInfoTypeForString("TRAIT_SENTIMENTAL")):
			# pPlayer.changeAnarchyTurns(max(2, pPlayer.getGoldenAgeLength() /4) + 1)
## Sentimental Trait ##
## Platyping's Promotions and Traits - End ##
		
		if (not self.__LOG_ENDGOLDENAGE):
			return
		CvUtil.pyPrint('Player %d Civilization %s golden age has ended'
			%(iPlayer, player.getCivilizationName()))

	def onChangeWar(self, argsList):
		'War Status Changes'
		bIsWar = argsList[0]
		iTeam = argsList[1]
		iRivalTeam = argsList[2]

## Platyping's Promotions and Traits - Start ##
## Cowardly Trait ##
		# if bIsWar:
			# pTeam = gc.getTeam(iTeam)
			# if not pTeam.isAVassal() and not pTeam.isBarbarian():
				# for iPlayerX in xrange(gc.getMAX_CIV_PLAYERS()):
					# pPlayerX = gc.getPlayer(iPlayerX)
					# fi pPlayerX.getTeam() != iRivalTeam: continue
					# if pPlayerX.hasTrait(gc.getInfoTypeForString("TRAIT_COWARDLY")):
						# (loopUnit, iter) = pPlayerX.firstUnit(false)
						# while(loopUnit):
							# if loopUnit.baseCombatStr() > 0 or loopUnit.airBaseCombatStr() > 0:
								# loopUnit.setImmobileTimer(loopUnit.getImmobileTimer() + 2)
							# (loopUnit, iter) = pPlayerX.nextUnit(iter, false)
## Cowardly Trait ##
## Platyping's Promotions and Traits - End ##
		
		if (not self.__LOG_WARPEACE):
			return
		if (bIsWar):
			strStatus = "declared war"
		else:
			strStatus = "declared peace"
		CvUtil.pyPrint('Team %d has %s on Team %d'
			%(iTeam, strStatus, iRivalTeam))
	
	def onChat(self, argsList):
		'Chat Message Event'
		chatMessage = "%s" %(argsList[0],)
		
	def onSetPlayerAlive(self, argsList):
		'Set Player Alive Event'
		iPlayerID = argsList[0]
		bNewValue = argsList[1]
		CvUtil.pyPrint("Player %d's alive status set to: %d" %(iPlayerID, int(bNewValue)))
		
	def onPlayerChangeStateReligion(self, argsList):
		'Player changes his state religion'
		iPlayer, iNewReligion, iOldReligion = argsList
		
	def onPlayerGoldTrade(self, argsList):
		'Player Trades gold to another player'
		iFromPlayer, iToPlayer, iGoldAmount = argsList
		
## Platyping's Promotions and Traits - Start ##
## Gullible Trait ##
		# pPlayer2 = gc.getPlayer(iToPlayer)
		# if pPlayer2.hasTrait(gc.getInfoTypeForString("TRAIT_GULLIBLE")):
			# pPlayer1 = gc.getPlayer(iFromPlayer)
			# pPlayer1.changeGold(iGoldAmount /3)
			# pPlayer2.changeGold(- iGoldAmount /3)
## Gullible Trait ##
## Platyping's Promotions and Traits - End ##
		
	def onCityBuilt(self, argsList):
		'City Built'
		city = argsList[0]
		if (city.getOwner() == gc.getGame().getActivePlayer()):
			self.__eventEditCityNameBegin(city, False)
			
## Platyping's Promotions and Traits - Start ##
		iPlayer = city.getOwner()
		pPlayer = gc.getPlayer(iPlayer)
## Agricultural Trait ##
		# if pPlayer.isGoldenAge() and pPlayer.hasTrait(gc.getInfoTypeForString("TRAIT_AGRICULTURAL")):
			# city.changeBaseYieldRate(YieldTypes.YIELD_FOOD, 5)
## Airborne Trait ##
		# if pPlayer.hasTrait(gc.getInfoTypeForString("TRAIT_AIRBORNE")):
			# city.setNumRealBuilding(gc.getInfoTypeForString("BUILDING_AIRBORNE"), 1)
## Industrious Trait ##
		# if pPlayer.hasTrait(gc.getInfoTypeForString("TRAIT_INDUSTRIOUS")):
			# for i in xrange(pPlayer.getCurrentEra() + 1):
				# RandBuilding = []
				# for iBuildingClass in xrange(gc.getNumBuildingClassInfos()):
					# if isLimitedWonderClass(iBuildingClass): continue
					# iBuilding = gc.getCivilizationInfo(pPlayer.getCivilizationType()).getCivilizationBuildings(iBuildingClass)
					# if iBuilding == -1: continue
					# if gc.getBuildingInfo(iBuilding).getProductionCost() < 1: continue
					# if city.canConstruct(iBuilding, True, True, True):
						# RandBuilding.append(iBuilding)
				# if len(RandBuilding) > 0:
					# city.setNumRealBuilding(RandBuilding[CyGame().getSorenRandNum(len(RandBuilding), "Free Building")], 1)
## Creative Trait ##
		# if pPlayer.hasTrait(gc.getInfoTypeForString("TRAIT_CREATIVE")):
			# FledgingInfo = gc.getCultureLevelInfo(gc.getInfoTypeForString("CULTURELEVEL_FLEDGLING"))
			# city.changeCulture(iPlayer, FledgingInfo.getSpeedThreshold(CyGame().getGameSpeedType()), True)
## Dynamic Trait ##
		# if pPlayer.hasTrait(gc.getInfoTypeForString("TRAIT_DYNAMIC")):
			# city.changeBaseYieldRate(YieldTypes.YIELD_PRODUCTION, 1)
## Expansive Trait ##
		# if pPlayer.hasTrait(gc.getInfoTypeForString("TRAIT_EXPANSIVE")):
			# city.changePopulation(1)
## Financial Trait ##
		# if pPlayer.hasTrait(gc.getInfoTypeForString("TRAIT_FINANCIAL")):
			# city.changeExtraTradeRoutes(1)
## Organized Trait ##
		# if pPlayer.hasTrait(gc.getInfoTypeForString("TRAIT_ORGANIZED")):
			# lRoute = []
			# for iItem in xrange(gc.getNumRouteInfos()):
				# ItemInfo = gc.getRouteInfo(iItem)
				# if ItemInfo.isGraphicalOnly(): continue
				# lRoute.append([ItemInfo.getValue(), iItem])
			# lRoute.sort()
			# lRoute.reverse()

			# for i in xrange(21):
				# pPlot = city.getCityIndexPlot(i)
				# if pPlot.isNone(): continue
				# if pPlot.isWater(): continue
				# if pPlot.isImpassable(): continue
				# if pPlot.getOwner() == iPlayer:
					# for iRoute in lRoute:
						# if pPlayer.canBuild(pPlot, iRoute[1], True, False):
							# pPlot.setRouteType(iRoute[1])
## Philosophical Trait ##
		# if pPlayer.hasTrait(gc.getInfoTypeForString("TRAIT_PHILOSOPHICAL")) and city.isCapital():
			# city.setNumRealBuilding(gc.getInfoTypeForString("BUILDING_PHILOSOPHICAL"), 1)
## Protective Trait ##
		# if pPlayer.hasTrait(gc.getInfoTypeForString("TRAIT_PROTECTIVE")):
			# city.plot().setImprovementType(gc.getInfoTypeForString("IMPROVEMENT_FORT"))
## Spiritual Trait ##
		# if pPlayer.hasTrait(gc.getInfoTypeForString("TRAIT_SPIRITUAL")):
			# iStateReligion = pPlayer.getStateReligion()
			# if iStateReligion > -1:
				# city.setHasReligion(iStateReligion,True,True,True)
## Imperialist Trait ##
		# if pPlayer.hasTrait(gc.getInfoTypeForString("TRAIT_IMPERIALIST")) and city.isCapital():
			# Bonus = [gc.getInfoTypeForString("BONUS_GEMS"), gc.getInfoTypeForString("BONUS_SILVER"), gc.getInfoTypeForString("BONUS_GOLD")]
			# LuxuryPlot = []
			# for i in xrange(21):
				# pPlot = city.getCityIndexPlot(i)
				# if pPlot.getBonusType(-1) == -1:
					# if not pPlot.isPeak() and not pPlot.isWater() and not pPlot.isCity():
						# LuxuryPlot.append(pPlot)
			# if len(LuxuryPlot) > 0:
				# pPlot = LuxuryPlot[CyGame().getSorenRandNum(len(LuxuryPlot), "where")]
				# pPlot.setBonusType(Bonus[CyGame().getSorenRandNum(3, "which")])
			# else:
				# pPlot = city.plot()
				# if pPlot.getBonusType(-1) == -1:
					# pPlot.setBonusType(Bonus[CyGame().getSorenRandNum(3, "which")])
				# else:
					# city.changeFreeBonus(Bonus[CyGame().getSorenRandNum(3, "which")], 1)
## Traditional Trait ##
		# iPalace = gc.getInfoTypeForString("BUILDINGCLASS_PALACE")
		# if pPlayer.hasTrait(gc.getInfoTypeForString("TRAIT_TRADITIONAL")):
			# city.setBuildingYieldChange(iPalace, YieldTypes.YIELD_FOOD, (pPlayer.getCurrentEra() + 1) * 2)
			# city.setBuildingYieldChange(iPalace, YieldTypes.YIELD_PRODUCTION, (pPlayer.getCurrentEra() + 1) * 2)
## Primitive Trait ##
		# pPlayer = gc.getPlayer(city.getOwner())
		# if pPlayer.hasTrait(gc.getInfoTypeForString("TRAIT_PRIMITIVE")):
			# city.changeEspionageHealthCounter(8)
## Primitive Trait ##
## Platyping's Promotions and Traits - End ##

		# <advc.007>
		if (not self.__LOG_CITYBUILT):
			return # </advc.007>
		CvUtil.pyPrint('City Built Event: %s' %(city.getName()))
		
	def onCityRazed(self, argsList):
		'City Razed'
		city, iPlayer = argsList
		#iOwner = city.findHighestCulture()
		# Partisans!
		# advc.003y: Code deleted; reimplemented in the DLL (cf. CvCity::doPartisans).
		
		# <advc.007>
		if (not self.__LOG_CITYACQUIRED):
			return # </advc.007>
		CvUtil.pyPrint("City Razed Event: %s" %(city.getName(),))
	
	def onCityAcquired(self, argsList):
		'City Acquired'
		iPreviousOwner,iNewOwner,pCity,bConquest,bTrade = argsList
		
## Platyping's Promotions and Traits - Start ##
		pPlayer = gc.getPlayer(iPreviousOwner)
		pPlayer2 = gc.getPlayer(iNewOwner)
## Airborne Trait ##
		# if pPlayer2.hasTrait(gc.getInfoTypeForString("TRAIT_AIRBORNE")):
			# pCity.setNumRealBuilding(gc.getInfoTypeForString("BUILDING_AIRBORNE"), 1)
		# elif pPlayer.hasTrait(gc.getInfoTypeForString("TRAIT_AIRBORNE")):
			# pCity.setNumRealBuilding(gc.getInfoTypeForString("BUILDING_AIRBORNE"), 0)
## Dynamic Trait ##
		# if pPlayer2.hasTrait(gc.getInfoTypeForString("TRAIT_DYNAMIC")):
			# pCity.changeBaseYieldRate(YieldTypes.YIELD_PRODUCTION, 1)
			# pCity.changeFreeSpecialistCount(gc.getInfoTypeForString("SPECIALIST_ENGINEER"), pCity.getNumWorldWonders())
		# if pPlayer.hasTrait(gc.getInfoTypeForString("TRAIT_DYNAMIC")):
			# pCity.changeFreeSpecialistCount(gc.getInfoTypeForString("SPECIALIST_ENGINEER"), - pCity.getNumWorldWonders())
## Philosophical Trait ##
		# if pCity.getNumBuilding(gc.getInfoTypeForString("BUILDING_PHILOSOPHICAL")):
			# pCity.setNumRealBuilding(gc.getInfoTypeForString("BUILDING_PHILOSOPHICAL"), 0)
			# pPlayer.getCapitalCity().setNumRealBuilding(gc.getInfoTypeForString("BUILDING_PHILOSOPHICAL"), 1)
## Barbaric Trait ##
			# if pPlayer.hasTrait(gc.getInfoTypeForString("TRAIT_BARBARIC")):
				# pCity.changeCulture(iPreviousOwner, - pCity.getCulture(iPreviousOwner) /4, True)
## Barbaric Trait ##
## Platyping's Promotions and Traits - End ##

		# <advc.007>
		if (not self.__LOG_CITYACQUIRED):
			return # </advc.007>
		CvUtil.pyPrint('City Acquired Event: %s' %(pCity.getName()))
	
	def onCityAcquiredAndKept(self, argsList):
		'City Acquired and Kept'
		iOwner,pCity = argsList
		
## Platyping's Promotions and Traits - Start ##
		pPlayer = gc.getPlayer(iOwner)
## Agricultural Trait ##
		# if pPlayer.isGoldenAge() and pPlayer.hasTrait(gc.getInfoTypeForString("TRAIT_AGRICULTURAL")):
			# pCity.changeBaseYieldRate(YieldTypes.YIELD_FOOD, 5)
## Creative Trait ##
		# if pPlayer.hasTrait(gc.getInfoTypeForString("TRAIT_CREATIVE")):
			# FledgingInfo = gc.getCultureLevelInfo(gc.getInfoTypeForString("CULTURELEVEL_FLEDGLING"))
			# pCity.setCulture(iNewOwner, max(pCity.getCulture(iNewOwner), FledgingInfo.getSpeedThreshold(CyGame().getGameSpeedType())), True)## Expansive Trait ##
		# if pPlayer.hasTrait(gc.getInfoTypeForString("TRAIT_EXPANSIVE")):
			# pCity.setPopulation(max(2, pCity.getPopulation()))
## Financial Trait ##
		# if pPlayer.hasTrait(gc.getInfoTypeForString("TRAIT_FINANCIAL")):
			# pCity.changeExtraTradeRoutes(1)## Organized Trait ##
		# if pPlayer.hasTrait(gc.getInfoTypeForString("TRAIT_ORGANIZED")):
			# lRoute = []
			# for iItem in xrange(gc.getNumRouteInfos()):
				# ItemInfo = gc.getRouteInfo(iItem)
				# if ItemInfo.isGraphicalOnly(): continue
				# lRoute.append([ItemInfo.getValue(), iItem])
			# lRoute.sort()
			# lRoute.reverse()

			# for i in xrange(21):
				# pPlot = pCity.getCityIndexPlot(i)
				# if pPlot.isNone(): continue
				# if pPlot.isWater(): continue
				# if pPlot.isImpassable(): continue
				# if pPlot.getOwner() == iNewOwner:
					# for iRoute in lRoute:
						# if pPlayer.canBuild(pPlot, iRoute[1], True, False):
						# pPlot.setRouteType(iRoute[1])
## Invasive Trait ##
		# if pPlayer.hasTrait(gc.getInfoTypeForString("TRAIT_INVASIVE")):
			# (loopUnit, iter) = pPlayer.firstUnit(False)
			# while(loopUnit):
				# loopUnit.changeDamage(-25, False)
				# (loopUnit, iter) = pPlayer.nextUnit(iter, False)
			# if pCity.getPopulation() >= pCity.conscriptMinCityPopulation():
				# pCity.changePopulation(-1)
				# pNewUnit = pPlayer.initUnit(pCity.getConscriptUnit(), pCity.getX(), pCity.getY(), UnitAITypes.NO_UNITAI, DirectionTypes.NO_DIRECTION)
				# pCity.addProductionExperience(pNewUnit, True)
## Protective Trait ##
		# if pPlayer.hasTrait(gc.getInfoTypeForString("TRAIT_PROTECTIVE")):
			# pCity.plot().setImprovementType(gc.getInfoTypeForString("IMPROVEMENT_FORT"))
## Spiritual Trait ##
		# if pPlayer.hasTrait(gc.getInfoTypeForString("TRAIT_SPIRITUAL")):
			# iStateReligion = pPlayer.getStateReligion()
			# if iStateReligion > -1:
				# pCity.setHasReligion(iStateReligion,True,True,True)
## Traditional Trait ##
		# iPalace = gc.getInfoTypeForString("BUILDINGCLASS_PALACE")
		# if pPlayer.hasTrait(gc.getInfoTypeForString("TRAIT_TRADITIONAL")):
			# pCity.setBuildingYieldChange(iPalace, YieldTypes.YIELD_FOOD, (pPlayer.getCurrentEra() + 1) * 2)
			# pCity.setBuildingYieldChange(iPalace, YieldTypes.YIELD_PRODUCTION, (pPlayer.getCurrentEra() + 1) * 2)
		# else:
			# pCity.setBuildingYieldChange(iPalace, YieldTypes.YIELD_FOOD, 0)
			# pCity.setBuildingYieldChange(iPalace, YieldTypes.YIELD_PRODUCTION, 0)
## Ruthless Trait ##
			# if pPlayer.hasTrait(gc.getInfoTypeForString("TRAIT_RUTHLESS")):
				# if pCity.findHighestCulture() != iOwner:
					# pCity.setPopulation(max(1, pCity.getPopulation()/2))
## Ruthless Trait ##
## Cruel Trait ##
			# if pPlayer.hasTrait(gc.getInfoTypeForString("TRAIT_CRUEL")):
				# pCity.changeOccupationTimer(pCity.getOccupationTimer() /2)
## Cruel Trait ##
## Loathsome Trait ##
			# if pPlayer.hasTrait(gc.getInfoTypeForString("TRAIT_LOATHSOME")):
				# if pCity.findHighestCulture() != iOwner:
					# iEvent = CvUtil.findInfoTypeNum(gc.getEventTriggerInfo, gc.getNumEventTriggerInfos(),'EVENTTRIGGER_PARTISANS')
					# if iEvent > -1:
						# triggerData = gc.getPlayer(iPreviousOwner).initTriggeredData(iEvent, True, -1, pCity.getX(), pCity.getY(), iNewOwner, pCity.getID(), -1, -1, -1, -1)
## Loathsome Trait ##
## Platyping's Promotions and Traits - End ##
		
		# <advc.007>
		if (not self.__LOG_CITYACQUIRED):
			return # </advc.007>
		CvUtil.pyPrint('City Acquired and Kept Event: %s' %(pCity.getName()))
	
	def onCityLost(self, argsList):
		'City Lost'
		city = argsList[0]
		player = PyPlayer(city.getOwner())
		if (not self.__LOG_CITYLOST):
			return
		CvUtil.pyPrint('City %s was lost by Player %d Civilization %s' 
			%(city.getName(), player.getID(), player.getCivilizationName()))
	
	def onCultureExpansion(self, argsList):
		'City Culture Expansion'
		pCity = argsList[0]
		iPlayer = argsList[1]
		# <advc.007>
		if (not self.__LOG_CITY_CULTURE):
			return # </advc.007>
		CvUtil.pyPrint("City %s's culture has expanded" %(pCity.getName(),))
	
	def onCityGrowth(self, argsList):
		'City Population Growth'
		pCity = argsList[0]
		iPlayer = argsList[1]
		
## Platyping's Promotions and Traits - Start ##
## Benevolent Trait ##
		# pPlayer = gc.getPlayer(iPlayer)
		# if pPlayer.hasTrait(gc.getInfoTypeForString("TRAIT_BENEVOLENT")):
			# pCity.setFood(pCity.getFood() /2)
## Benevolent Trait ##
## Platyping's Promotions and Traits - End ##
		
		# <advc.007>
		if (not self.__LOG_CITY_GROWTH):
			return # </advc.007>
		CvUtil.pyPrint("%s has grown" %(pCity.getName(),))
	
	def onCityDoTurn(self, argsList):
		'City Production'
		pCity = argsList[0]
		iPlayer = argsList[1]

		CvAdvisorUtils.cityAdvise(pCity, iPlayer)
	
	def onCityBuildingUnit(self, argsList):
		'City begins building a unit'
		pCity = argsList[0]
		iUnitType = argsList[1]
		
# Evening Love Unique Trait ##
		# iPlayer = pCity.getOwner()
		# pPlayer = gc.getPlayer(iPlayer)
		# if pPlayer.getLeaderType() == gc.getInfoTypeForString("LEADER_EVENINGLOVE"):
			# pUnitType = gc.getUnitInfo(iUnitType)
			# pCityPlot = pCity.plot()
			# iUnitsOnPlot = pCityPlot.getNumDefenders(iPlayer)
			# iCityPopulation = pCity.getPopulation()
			# iCityDiscordance = (iUnitsOnPlot - iCityPopulation)
			# if (iCityDiscordance > 0 and pUnitType.getUnitCombatType() > -1):
				# if gc.getTeam(pPlayer.getTeam()).getAtWarCount(True) > 0 or CyGame().getSorenRandNum(iCityDiscordance, "Unique Ability Rand Chance") == 0:
					# bCityHasLake = False
					# iCitySearchRadius = min(2, max(iCityDiscordance, pCity.countNumWaterPlots()))
					# if iCitySearchRadius > 0:
						# iX = pCityPlot.getX()
						# iY = pCityPlot.getY()
						# pMap = CyMap()
						# for iCityPlotX in xrange(iX-iCitySearchRadius, iX+(iCitySearchRadius+1), 1):
							# for iCityPlotY in xrange(iY-iCitySearchRadius, iY+(iCitySearchRadius+1), 1):
								# pLoopPlot = pMap.plot(iCityPlotX,iCityPlotY)
								# if pLoopPlot and not pLoopPlot.isNone() and pLoopPlot.isLake():
									# bCityHasLake = True
									# break
					# if bCityHasLake:
						# iUnitLevelTotal = 0
						# iUnitCount = 0
						# iValue = 0
						# (loopUnit, iter) = pPlayer.firstUnit(True)
						# while(loopUnit):
							# if loopUnit.getUnitType() == iUnitType and loopUnit.atPlot(pCityPlot):
								# iUnitLevelTotal += loopUnit.getLevel()
								# iUnitCount += 1
							# (loopUnit, iter) = pPlayer.nextUnit(iter, True)
						# if (iUnitCount > 0 and iUnitLevelTotal > 0):
							# fPowerMulitplier = float('0.'+str(iUnitCount))
							# iProductionCostTotal = (pUnitType.getProductionCost() * iUnitCount)
							# iPowerDivisor = max(5, (iUnitLevelTotal - iUnitCount), (iUnitCount - iUnitLevelTotal))
							# if iPowerDivisor > 0:
								# iValue = int((abs(pCity.productionLeft() - iProductionCostTotal) * fPowerMulitplier) / iPowerDivisor)
						# if iValue > 0:
							# pCity.changeProduction(iValue)
# Evening Love Unique Trait ##

		if (not self.__LOG_CITYBUILDING):
			return
		CvUtil.pyPrint("%s has begun building a %s" %(pCity.getName(),gc.getUnitInfo(iUnitType).getDescription()))
	
	def onCityBuildingBuilding(self, argsList):
		'City begins building a Building'
		pCity = argsList[0]
		iBuildingType = argsList[1]
		if (not self.__LOG_CITYBUILDING):
			return
		CvUtil.pyPrint("%s has begun building a %s" %(pCity.getName(),gc.getBuildingInfo(iBuildingType).getDescription()))
	
	def onCityRename(self, argsList):
		'City is renamed'
		pCity = argsList[0]
		if (pCity.getOwner() == gc.getGame().getActivePlayer()):
			self.__eventEditCityNameBegin(pCity, True)	
	
	def onCityHurry(self, argsList):
		'City is renamed'
		pCity = argsList[0]
		iHurryType = argsList[1]

	def onVictory(self, argsList):
		'Victory'
		iTeam, iVictory = argsList
		if (iVictory >= 0 and iVictory < gc.getNumVictoryInfos()):
			victoryInfo = gc.getVictoryInfo(int(iVictory))
			CvUtil.pyPrint("Victory!  Team %d achieves a %s victory"
				%(iTeam, victoryInfo.getDescription()))
	
	def onVassalState(self, argsList):
		'Vassal State'
		iMaster, iVassal, bVassal = argsList
		
		if (bVassal):
			CvUtil.pyPrint("Team %d becomes a Vassal State of Team %d"
				%(iVassal, iMaster))
		else:
			CvUtil.pyPrint("Team %d revolts and is no longer a Vassal State of Team %d"
				%(iVassal, iMaster))
	
	def onGameUpdate(self, argsList):
		'sample generic event, called on each game turn slice'
		genericArgs = argsList[0][0]	# tuple of tuple of my args
		turnSlice = genericArgs[0]
	
	def onMouseEvent(self, argsList):
		'mouse handler - returns 1 if the event was consumed'
		eventType,mx,my,px,py,interfaceConsumed,screens = argsList
		if ( px!=-1 and py!=-1 ):
			if ( eventType == self.EventLButtonDown ):
				if (self.bAllowCheats and self.bCtrl and self.bAlt and CyMap().plot(px,py).isCity() and not interfaceConsumed):
					# Launch Edit City Event
					self.beginEvent( CvUtil.EventEditCity, (px,py) )
					return 1
				
				elif (self.bAllowCheats and self.bCtrl and self.bShift and not interfaceConsumed):
					# Launch Place Object Event
					self.beginEvent( CvUtil.EventPlaceObject, (px, py) )
					return 1
			
		if ( eventType == self.EventBack ):
			return CvScreensInterface.handleBack(screens)
		elif ( eventType == self.EventForward ):
			return CvScreensInterface.handleForward(screens)
		
		return 0
		

#################### TRIGGERED EVENTS ##################	
				
	def __eventEditCityNameBegin(self, city, bRename):
		popup = PyPopup.PyPopup(CvUtil.EventEditCityName, EventContextTypes.EVENTCONTEXT_ALL)
		popup.setUserData((city.getID(), bRename))
		popup.setHeaderString(localText.getText("TXT_KEY_NAME_CITY", ()))
		popup.setBodyString(localText.getText("TXT_KEY_SETTLE_NEW_CITY_NAME", ()))
		popup.createEditBox(city.getName())
		popup.setEditBoxMaxCharCount( 15 )
		popup.launch()
	
	def __eventEditCityNameApply(self, playerID, userData, popupReturn):	
		'Edit City Name Event'
		iCityID = userData[0]
		bRename = userData[1]
		player = gc.getPlayer(playerID)
		city = player.getCity(iCityID)
		cityName = popupReturn.getEditBoxString(0)
		if (len(cityName) > 30):
			cityName = cityName[:30]
		city.setName(cityName, not bRename)

	def __eventEditCityBegin(self, argsList):
		'Edit City Event'
		px,py = argsList
		CvWBPopups.CvWBPopups().initEditCity(argsList)
	
	def __eventEditCityApply(self, playerID, userData, popupReturn):
		'Edit City Event Apply'
		if (getChtLvl() > 0):
			CvWBPopups.CvWBPopups().applyEditCity( (popupReturn, userData) )

	def __eventPlaceObjectBegin(self, argsList):
		'Place Object Event'
		CvDebugTools.CvDebugTools().initUnitPicker(argsList)
	
	def __eventPlaceObjectApply(self, playerID, userData, popupReturn):
		'Place Object Event Apply'
		if (getChtLvl() > 0):
			CvDebugTools.CvDebugTools().applyUnitPicker( (popupReturn, userData) )

	def __eventAwardTechsAndGoldBegin(self, argsList):
		'Award Techs & Gold Event'
		CvDebugTools.CvDebugTools().cheatTechs()
	
	def __eventAwardTechsAndGoldApply(self, playerID, netUserData, popupReturn):
		'Award Techs & Gold Event Apply'
		if (getChtLvl() > 0):
			CvDebugTools.CvDebugTools().applyTechCheat( (popupReturn) )
	
	def __eventShowWonderBegin(self, argsList):
		'Show Wonder Event'
		CvDebugTools.CvDebugTools().wonderMovie()
	
	def __eventShowWonderApply(self, playerID, netUserData, popupReturn):
		'Wonder Movie Apply'
		if (getChtLvl() > 0):
			CvDebugTools.CvDebugTools().applyWonderMovie( (popupReturn) )
	
	def __eventEditUnitNameBegin(self, argsList):
		pUnit = argsList
		popup = PyPopup.PyPopup(CvUtil.EventEditUnitName, EventContextTypes.EVENTCONTEXT_ALL)
		popup.setUserData((pUnit.getID(),))
		popup.setBodyString(localText.getText("TXT_KEY_RENAME_UNIT", ()))
		popup.createEditBox(pUnit.getNameNoDesc())
		popup.launch()

	def __eventEditUnitNameApply(self, playerID, userData, popupReturn):	
		'Edit Unit Name Event'
		iUnitID = userData[0]
		unit = gc.getPlayer(playerID).getUnit(iUnitID)
		newName = popupReturn.getEditBoxString(0)
		if (len(newName) > 25):
			newName = newName[:25]			
		unit.setName(newName)

	def __eventWBAllPlotsPopupBegin(self, argsList):
		CvScreensInterface.getWorldBuilderScreen().allPlotsCB()
		return
	def __eventWBAllPlotsPopupApply(self, playerID, userData, popupReturn):
		if (popupReturn.getButtonClicked() >= 0):
			CvScreensInterface.getWorldBuilderScreen().handleAllPlotsCB(popupReturn)
		return

	def __eventWBLandmarkPopupBegin(self, argsList):
		CvScreensInterface.getWorldBuilderScreen().setLandmarkCB("")
		#popup = PyPopup.PyPopup(CvUtil.EventWBLandmarkPopup, EventContextTypes.EVENTCONTEXT_ALL)
		#popup.createEditBox(localText.getText("TXT_KEY_WB_LANDMARK_START", ()))
		#popup.launch()
		return

	def __eventWBLandmarkPopupApply(self, playerID, userData, popupReturn):
		if (popupReturn.getEditBoxString(0)):
			szLandmark = popupReturn.getEditBoxString(0)
			if (len(szLandmark)):
				CvScreensInterface.getWorldBuilderScreen().setLandmarkCB(szLandmark)
		return

	def __eventWBScriptPopupBegin(self, argsList):
		popup = PyPopup.PyPopup(CvUtil.EventWBScriptPopup, EventContextTypes.EVENTCONTEXT_ALL)
		popup.setHeaderString(localText.getText("TXT_KEY_WB_SCRIPT", ()))
		popup.createEditBox(CvScreensInterface.getWorldBuilderScreen().getCurrentScript())
		popup.launch()
		return

	def __eventWBScriptPopupApply(self, playerID, userData, popupReturn):
		if (popupReturn.getEditBoxString(0)):
			szScriptName = popupReturn.getEditBoxString(0)
			CvScreensInterface.getWorldBuilderScreen().setScriptCB(szScriptName)
		return

	def __eventWBStartYearPopupBegin(self, argsList):
		popup = PyPopup.PyPopup(CvUtil.EventWBStartYearPopup, EventContextTypes.EVENTCONTEXT_ALL)
		popup.createSpinBox(0, "", gc.getGame().getStartYear(), 1, 5000, -5000)
		popup.launch()
		return

	def __eventWBStartYearPopupApply(self, playerID, userData, popupReturn):
		iStartYear = popupReturn.getSpinnerWidgetValue(int(0))
		CvScreensInterface.getWorldBuilderScreen().setStartYearCB(iStartYear)
		return
