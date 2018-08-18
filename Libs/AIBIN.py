from utils import *
from fileutils import *
import aibin_orders
import TBL, DAT

import struct, re, os, sys
from math import log, floor
from zlib import compress, decompress

default_ais = {'Protoss':'PMCu','BWProtoss':'PMCx','Terran':'TMCu','BWTerran':'TMCx','Zerg':'ZMCu','BWZerg':'ZMCx'}

types = [
	'byte',
	'word',
	'dword',
	'unit',
	'building',
	'military',
	'gg_military',
	'ag_military',
	'ga_military',
	'aa_military',
	'upgrade',
	'technology',
	'string',
	'compare'
	'compare_trig'
	'order',
	'point',
	'area',
	'unit_group',
]

def convflags(num):
	if isstr(num):
		b = list(num)
		b.reverse()
		return sum([int(x)*(2**n) for n,x in enumerate(b)])
	b = [str(num/(2**n)%2) for n in range(3)]
	b.reverse()
	return ''.join(b)

idle_order_flag_names = {
	0x1: 'NotEnemies',
	0x2: 'Own',
	0x4: 'Allied',
	0x8: 'Unseen',
	0x10: 'Invisible',
	0x20: 'InCombat',
	0x40: 'Deathrattle',
	0x4000: 'RemoveSilentFail',
	0x8000: 'Remove',
}
idle_order_flag_reverse = dict((v.lower(), k) for k, v in idle_order_flag_names.iteritems())
spell_effect_names = {
	0x1: 'Ensnare',
	0x2: 'Plague',
	0x4: 'Lockdown',
	0x8: 'Irradiate',
	0x10: 'Parasite',
	0x20: 'Blind',
	0x40: 'Matrix',
	0x80: 'Maelstrom',
}
spell_effect_names_reverse = (
	dict((v.lower(), k) for k, v in spell_effect_names.iteritems())
)

units_dat_flags = {
	0x1: 'Building',
	0x2: 'Addon',
	0x4: 'Air',
	0x8: 'Worker',
	0x10: 'Turret',
	0x20: 'FlyingBuilding',
	0x40: 'Hero',
	0x80: 'Regeneration',
	0x100: 'AnimatedOverlay',
	0x200: 'Cloakable',
	0x400: 'DualBirth',
	0x800: 'Powerup',
	0x1000: 'ResourceDepot',
	0x2000: 'ResourceContainer',
	0x4000: 'Robotic',
	0x8000: 'Detector',
	0x00010000: 'Organic',
	0x00020000: 'RequiresCreep',
	0x00040000: 'Unk40000',
	0x00080000: 'RequiresPsi',
	0x00100000: 'Burrower',
	0x00200000: 'Spellcaster',
	0x00400000: 'PermamentlyCloaked',
	0x00800000: 'Carryable',
	0x01000000: 'IgnoreSupplyCheck',
	0x02000000: 'MediumOverlays',
	0x04000000: 'LargeOverlays',
	0x08000000: 'CanMove',
	0x10000000: 'FullAutoAttack',
	0x20000000: 'Invincible',
	0x40000000: 'Mechanical',
	0x80000000: 'UnkProducesUnits',
}

units_dat_flags_reverse = (
	dict((v.lower(), k) for k, v in units_dat_flags.iteritems())
)

idle_orders_targeting_flags = {
	0x1: 'OtherUnit',
	0x2: 'Enemy',
	0x4: 'Ally',
	0x8: 'Own',
	0x10: 'Nothing',
}
idle_orders_targeting_flags_reverse = (
	dict((v.lower(), k) for k, v in idle_orders_targeting_flags.iteritems())
)

issue_order_flag_names = {
	0x1: 'Enemies',
	0x2: 'Own',
	0x4: 'Allied',
	0x8: 'SingleUnit',
	0x10: 'EachAtMostOnce',
}
issue_order_flag_reverse = dict((v.lower(), k) for k, v in issue_order_flag_names.iteritems())

aicontrol_names = {
	0x0: 'wait_request_resources',
	0x1: 'dont_wait_request_resources',
}

aicontrol_names_rev = dict((v.lower(), k) for k, v in aicontrol_names.iteritems())

class AIBIN:
	labels = [
		'Goto',
		'DoesntCommandGoto',
		'Wait',
		'StartTownManagement',
		'StartAreaTownManagement',
		'RunCodeForExpansion',
		'Build',
		'ResearchUpgrade',
		'ResearchTechnology',
		'WaitUntilConstructionFinished',
		'WaitUntilConstructionStarted',
		'ClearAttackData',
		'AddToAttackParty',
		'PrepareAttackParty',
		'AttackWithAttackParty',
		'WaitForSecureUnknown',
		'CaptureExpandUnknown',
		'BuildBunkersUnknown',
		'WaitForBunkersUnknown',
		'BuildGroundToGroundDefenceUnit',
		'BuildAirToGroundDefenceUnit',
		'BuildGroundToAirDefenceUnit',
		'BuildAirToAirDefenceUnit',
		'UseForGroundToGroundDefence',
		'UseForAirToGroundDefence',
		'UseForGroundToAirDefence',
		'UseForAirToAirDefence',
		'ClearGroundToGroundDefence',
		'ClearAirToGroundDefence',
		'ClearGroundToAirDefence',
		'ClearAirToAirDefence',
		'AllUnitsSuicideMission',
		'MakeSelectedPlayerEnemy',
		'MakeSelectedPlayerAlly',
		'DefaultMinUnknown',
		'DefaultBuildOffUnknown',
		'StopCodeSection',
		'SwitchComputerToRescuable',
		'MoveDarkTemplarToLocation',
		'Debug',
		'CauseFatalError',
		'EnterBunker',
		'ValueThisAreaHigher',
		'DontManageOrBuildTransports',
		'UseTransportsUpToMax',
		'BuildNukes',
		'MaxForceUnknown',
		'ClearPreviousCombatData',
		'ChanceGoto',
		'AfterTimeGoto',
		'BuildSupplyOnlyWhenNeeded',
		'BuildSupplyBeforeNeeded',
		'BuildTurretsUnknown',
		'WaitForTurretsUnknown',
		'DefaultBuildUnknown',
		'HarassFactorUnknown',
		'StartCampaignAI',
		'NearestRaceGoto',
		'EnemyInRangeGoto',
		'MoveWorkersToExpansion',
		'EnemyReachableByGroundGoto',
		'GuardTown',
		'WaitUntilCommandAmount',
		'SendUnitsToGuardResources',
		'CallSubroutine',
		'ReturnFromSubroutine',
		'EvalHarrassUnkown',
		'PlaceTowers',
		'AttackedGoto',
		'BuildIfNeeded',
		'DoMorphUnknown',
		'WaitForUpgradesUnknown',
		'RunSimultaneously',
		'PredifinedConditionalGoto',
		'ScoutWithUnknown',
		'MaxAmountOfUnit',
		'Train',
		'TargetExpansionUnknown',
		'WaitUntilCommands',
		'SetAttacksUnknown',
		'SetGeneralCommandTarget',
		'MakeUnitsPatrol',
		'GiveResourcesWhenLow',
		'PrepDownUnknown',
		'ComputerHasResourcesGoto',
		'EnterNearestTransport',
		'ExitTransport',
		'EnableSharedVision',
		'DisableSharedVision',
		'NukeSelectedLocation',
		'HarassSelectedLocation',
		'ImplodeUnknown',
		'GuardAllUnknown',
		'EnemyCommandsGoto',
		'EnemyHasResourcesGoto',
		'IfDifUnknown',
		'EasyAttackUnknown',
		'KillCurrentThread',
		'AllowOtherThreadsToKillCurrent',
		'WaitForAttackGroupToAttack',
		'BigAttackPrepare',
		'JunkyardDog',
		'FakeNukeUnknown',
		'DisruptionWebSelectedLocation',
		'RecallSelectedLocation',
		'SetRandomSeed',
		'IfOwnedUnknown',
		'CreateNuke',
		'CreateUnitAtCoordinates',
		'LaunchNukeAtCoordinates',
		'AskForHelpWhenInTrouble',
		'WatchAlliesUnknown',
		'TryTownpointUnknown',
		'AttackTo',
		'AttackTimeout',
		'IssueOrder',
		'Deaths',
		'IdleOrders',
		'IfAttacking',
		'UnstartCampaign',
		'MaxWorkers',
		'UnderAttack',
		'AiControl',
		'BringJump',
		'CreateScript',
		'PlayerJump',
		'Kills',
		'WaitRand',
		'UpgradeJump',
		'TechJump',
		'RandomCall',
		'AttackRand',
		'Supply',
		'Time',
		'Resources',
		'SetId',
		'RemoveBuild',
		'Guard',
		'BaseLayout',
		'Print',
		'Attacking',
	]
	short_labels = [
		'goto',               #0x00 - 0
		'notowns_jump',       #0x01 - 1
		'wait',               #0x02 - 2
		'start_town',         #0x03 - 3
		'start_areatown',     #0x04 - 4
		'expand',             #0x05 - 5
		'build',              #0x06 - 6
		'upgrade',            #0x07 - 7
		'tech',               #0x08 - 8
		'wait_build',         #0x09 - 9
		'wait_buildstart',    #0x0A - 10
		'attack_clear',       #0x0B - 11
		'attack_add',         #0x0C - 12
		'attack_prepare',     #0x0D - 13
		'attack_do',          #0x0E - 14
		'wait_secure',        #0x0F - 15
		'capt_expand',        #0x10 - 16
		'build_bunkers',      #0x11 - 17
		'wait_bunkers',       #0x12 - 18
		'defensebuild_gg',    #0x13 - 19
		'defensebuild_ag',    #0x14 - 20
		'defensebuild_ga',    #0x15 - 21
		'defensebuild_aa',    #0x16 - 22
		'defenseuse_gg',      #0x17 - 23
		'defenseuse_ag',      #0x18 - 24
		'defenseuse_ga',      #0x19 - 25
		'defenseuse_aa',      #0x1A - 26
		'defenseclear_gg',    #0x1B - 27
		'defenseclear_ag',    #0x1C - 28
		'defenseclear_ga',    #0x1D - 29
		'defenseclear_aa',    #0x1E - 30
		'send_suicide',       #0x1F - 31
		'player_enemy',       #0x20 - 32
		'player_ally',        #0x21 - 33
		'default_min',        #0x22 - 34
		'defaultbuild_off',   #0x23 - 35
		'stop',               #0x24 - 36
		'switch_rescue',      #0x25 - 37
		'move_dt',            #0x26 - 38
		'debug',              #0x27 - 39
		'fatal_error',        #0x28 - 40
		'enter_bunker',       #0x29 - 41
		'value_area',         #0x2A - 42
		'transports_off',     #0x2B - 43
		'check_transports',   #0x2C - 44
		'nuke_rate',          #0x2D - 45
		'max_force',          #0x2E - 46
		'clear_combatdata',   #0x2F - 47
		'random_jump',        #0x30 - 48
		'time_jump',          #0x31 - 49
		'farms_notiming',     #0x32 - 50
		'farms_timing',       #0x33 - 51
		'build_turrets',      #0x34 - 52
		'wait_turrets',       #0x35 - 53
		'default_build',      #0x36 - 54
		'harass_factor',      #0x37 - 55
		'start_campaign',     #0x38 - 56
		'race_jump',          #0x39 - 57
		'region_size',        #0x3A - 58
		'get_oldpeons',       #0x3B - 59
		'groundmap_jump',     #0x3C - 60
		'place_guard',        #0x3D - 61
		'wait_force',         #0x3E - 62
		'guard_resources',    #0x3F - 63
		'call',               #0x40 - 64
		'return',             #0x41 - 65
		'eval_harass',        #0x42 - 66
		'creep',              #0x43 - 67
		'panic',              #0x44 - 68
		'player_need',        #0x45 - 69
		'do_morph',           #0x46 - 70
		'wait_upgrades',      #0x47 - 71
		'multirun',           #0x48 - 72
		'rush',               #0x49 - 73
		'scout_with',         #0x4A - 74
		'define_max',         #0x4B - 75
		'train',              #0x4C - 76
		'target_expansion',   #0x4D - 77
		'wait_train',         #0x4E - 78
		'set_attacks',        #0x4F - 79
		'set_gencmd',         #0x50 - 80
		'make_patrol',        #0x51 - 81
		'give_money',         #0x52 - 82
		'prep_down',          #0x53 - 83
		'resources_jump',     #0x54 - 84
		'enter_transport',    #0x55 - 85
		'exit_transport',     #0x56 - 86
		'sharedvision_on',    #0x57 - 87
		'sharedvision_off',   #0x58 - 88
		'nuke_location',      #0x59 - 89
		'harass_location',    #0x5A - 90
		'implode',            #0x5B - 91
		'guard_all',          #0x5C - 92
		'enemyowns_jump',     #0x5D - 93
		'enemyresources_jump',#0x5E - 94
		'if_dif',             #0x5F - 95
		'easy_attack',        #0x60 - 96
		'kill_thread',        #0x61 - 97
		'killable',           #0x62 - 98
		'wait_finishattack',  #0x63 - 99
		'quick_attack',       #0x64 - 100
		'junkyard_dog',       #0x65 - 101
		'fake_nuke',          #0x66 - 102
		'disruption_web',     #0x67 - 103
		'recall_location',    #0x68 - 104
		'set_randomseed',     #0x69 - 105
		'if_owned',           #0x6A - 106
		'create_nuke',        #0x6B - 107
		'create_unit',        #0x6C - 108
		'nuke_pos',           #0x6D - 109
		'help_iftrouble',     #0x6E - 110
		'allies_watch',       #0x6F - 111
		'try_townpoint',      #0x70 - 112
		'attack_to',          #0x71 - 113
		'attack_timeout',     #0x72 - 114
		'issue_order',        #0x73 - 115
		'deaths',          #0x74 - 116
		'idle_orders',        #0x75 - 117
		'if_attacking',        #0x76 - 118
		'unstart_campaign',        #0x77 - 119
		'max_workers',        #0x78 - 120
		'under_attack',        #0x79 - 121
		'aicontrol',        #0x7a - 122
		'bring_jump',       #0x7b - 123
		'create_script',       #0x7c - 124
		'player_jump', #0x7d
		'kills', #0x7e
		'wait_rand', #0x7f,
		'upgrade_jump', #0x80
		'tech_jump', #0x81
		'random_call', #0x82
		'attack_rand', #0x83
		'supply', #0x84,
		'time', #0x85,
		'resources', #0x86,
		'set_id', #0x87,
		'remove_build', #0x88
		'guard', #0x89,
		'base_layout', #0x8a,
		'print', #0x8b,
		'attacking', #0x8c,
	]

	wait_commands = [
		'wait',
		'wait_rand',
	]

	separate = [
		'goto',
		'debug',
		'race_jump',
		'nearestracegoto',
		'return',
		'returnfromsubroutine',
		'stop',
		'stopcodesection',
	]

	def __init__(self, bwscript=None, units=None, upgrades=None, techs=None, stat_txt=None):
		if bwscript == None:
			bwscript = os.path.join(BASE_DIR, 'Libs', 'MPQ', 'scripts', 'bwscript.bin')
		if units == None:
			units = os.path.join(BASE_DIR, 'Libs', 'MPQ', 'arr', 'units.dat')
		if upgrades == None:
			upgrades = os.path.join(BASE_DIR, 'Libs', 'MPQ', 'arr', 'upgrades.dat')
		if techs == None:
			techs = os.path.join(BASE_DIR, 'Libs', 'MPQ', 'arr', 'techdata.dat')
		if stat_txt == None:
			stat_txt = os.path.join(BASE_DIR, 'Libs', 'MPQ', 'rez', 'stat_txt.tbl')
		self.ais = odict()
		self.aisizes = {}
		self.externaljumps = [[{},{}],[{},{}]]
		self.varinfo = odict()
		self.aiinfo = {}
		self.warnings = None
		self.bwscript = None
		self.warnings = []
		self.order_names = aibin_orders.names
		self.order_name_to_id = aibin_orders.name_to_id
		self.nobw = bwscript == None
		if bwscript != False:
			self.bwscript = BWBIN()
			if bwscript:
				self.warnings = self.bwscript.load_file(bwscript)
				self.externaljumps = self.bwscript.externaljumps
		if isinstance(stat_txt, TBL.TBL):
			self.tbl = stat_txt
		else:
			self.tbl = TBL.TBL()
			self.tbl.load_file(stat_txt)
		if isinstance(units, DAT.UnitsDAT):
			self.unitsdat = units
		else:
			self.unitsdat = DAT.UnitsDAT(self.tbl)
			self.unitsdat.load_file(units)
		if isinstance(upgrades, DAT.UpgradesDAT):
			self.upgradesdat = upgrades
		else:
			self.upgradesdat = DAT.UpgradesDAT(self.tbl)
			self.upgradesdat.load_file(upgrades)
		if isinstance(techs, DAT.TechDAT):
			self.techdat = techs
		else:
			self.techdat = DAT.TechDAT(self.tbl)
			self.techdat.load_file(techs)
		self._casters = None # Used during interpreting
		self.parameters = [
			[self.ai_address], # goto
			[self.ai_unit,self.ai_address], # notowns_jump
			[self.ai_word], # wait
			None, # start_town
			None, # start_areatown
			[self.ai_byte, self.ai_address], # expand
			[self.ai_byte, self.ai_building, self.ai_byte], # build
			[self.ai_byte, self.ai_upgrade, self.ai_byte], # upgrade
			[self.ai_technology,self.ai_byte], # tech
			[self.ai_byte, self.ai_building], # wait_build
			[self.ai_byte, self.ai_unit], # wait_buildstart
			None, # attack_clear
			[self.ai_byte, self.ai_military], # attack_add
			None, # attack_prepare
			None, # attack_do
			None, # wait_secure
			None, # capt_expand
			None, # build_bunkers
			None, # wait_bunkers
			[self.ai_byte, self.ai_ggmilitary], # defensebuild_gg
			[self.ai_byte, self.ai_agmilitary], # defensebuild_ag
			[self.ai_byte, self.ai_gamilitary], # defensebuild_ga
			[self.ai_byte, self.ai_aamilitary], # defensebuild_aa
			[self.ai_byte, self.ai_ggmilitary], # defenseuse_gg
			[self.ai_byte, self.ai_agmilitary], # defenseuse_ag
			[self.ai_byte, self.ai_gamilitary], # defenseuse_ga
			[self.ai_byte, self.ai_aamilitary], # defenseuse_aa
			None, # defenseclear_gg
			None, # defenseclear_ag
			None, # defenseclear_ga
			None, # defenseclear_aa
			[self.ai_byte], # send_suicide
			None, # player_enemy
			None, # player_ally
			[self.ai_byte], # default_min
			None, # defaultbuild_off
			None, # stop
			None, # switch_rescue
			None, # move_dt
			[self.ai_address,self.ai_string], # debug
			None, # fatal_error
			None, # enter_bunker
			None, # value_area
			None, # transports_off
			None, # check_transports
			[self.ai_byte], # nuke_rate
			[self.ai_word], # max_force
			None, # clear_combatdata
			[self.ai_byte, self.ai_address], # random_jump
			[self.ai_byte, self.ai_address], # time_jump
			None, # farms_notiming
			None, # farms_timing
			None, # build_turrets
			None, # wait_turrets
			None, # default_build
			[self.ai_word], # harass_factor
			None, # start_campaign
			[self.ai_address, self.ai_address, self.ai_address], # race_jump
			[self.ai_byte, self.ai_address], # region_size
			[self.ai_byte], # get_oldpeons
			[self.ai_address], # groundmap_jump
			[self.ai_unit, self.ai_byte], # place_guard
			[self.ai_byte, self.ai_military], # wait_force
			[self.ai_military], # guard_resources
			[self.ai_address], # call
			None, # return
			[self.ai_address], # eval_harass
			[self.ai_byte], # creep
			[self.ai_address], # panic
			[self.ai_byte,self.ai_building], # player_need
			[self.ai_byte, self.ai_military], # do_morph
			None, # wait_upgrades
			[self.ai_address], # multirun
			[self.ai_byte, self.ai_address], # rush
			[self.ai_military], # scout_with
			[self.ai_byte, self.ai_unit], # define_max
			[self.ai_byte, self.ai_military], # train
			None, # target_expansion
			[self.ai_byte, self.ai_unit], # wait_train
			[self.ai_byte], # set_attacks
			None, # set_gencmd
			None, # make_patrol
			None, # give_money
			[self.ai_byte, self.ai_byte, self.ai_military], # prep_down
			[self.ai_word, self.ai_word, self.ai_address], # resources_jump
			None, # enter_transport
			None, # exit_transport
			[self.ai_byte], # sharedvision_on
			[self.ai_byte], # sharedvision_off
			None, # nuke_location
			None, # harass_location
			None, # implode
			None, # guard_all
			[self.ai_unit, self.ai_address], # enemyowns_jump
			[self.ai_word, self.ai_word, self.ai_address], # enemyresources_jump
			[self.ai_compare, self.ai_byte, self.ai_address], # if_dif
			[self.ai_byte, self.ai_military], # easy_attack
			None, # kill_thread
			None, # killable
			None, # wait_finishattack
			None, # quick_attack
			None, # junkyard_dog
			None, # fake_nuke
			None, # disruption_web
			None, # recall_location
			[self.ai_dword], # set_randomseed
			[self.ai_unit,self.ai_address], # if_owned
			None, # create_nuke
			[self.ai_unit, self.ai_word, self.ai_word], # create_unit
			[self.ai_word, self.ai_word], # nuke_pos
			None, # help_iftrouble
			[self.ai_byte, self.ai_address], # allies_watch
			[self.ai_byte, self.ai_address], # try_townpoint
			[self.ai_point, self.ai_point], # attack_to
			[self.ai_dword], # attack_timeout
			[self.ai_order, self.ai_word, self.ai_unit_or_group,
				self.ai_area, self.ai_area, self.ai_unit_or_group,
				self.ai_issue_order_flags], # issue_order
			[self.ai_byte, self.ai_compare_trig, self.ai_dword, self.ai_unit_or_group,
				self.ai_address], # deaths
			[self.ai_idle_order, self.ai_word, self.ai_word, self.ai_unit_or_group,
				self.ai_word, self.ai_unit_or_group, self.ai_byte,
				self.ai_idle_order_flags], # idle_orders
			[self.ai_address], # if_attacking
			None, # unstart_campaign
			[self.ai_byte], # max_workers
			[self.ai_byte], # under_attack
			[self.ai_control_type], # aicontrol
			[self.ai_byte, self.ai_compare_trig, self.ai_dword, self.ai_unit_or_group,
				self.ai_area, self.ai_address], #bring_jump
			# create_script
			[self.ai_address, self.ai_byte, self.ai_area, self.ai_byte, self.ai_byte],
		        # player_jump
			[self.ai_string,self.ai_address],
			#kills
			[self.ai_byte, self.ai_byte, self.ai_compare_trig, self.ai_dword, self.ai_unit_or_group,
				self.ai_address],
			#wait_rand
			[self.ai_dword,self.ai_dword],
			#upgrade_jump
			[self.ai_byte, self.ai_compare_trig, self.ai_upgrade, self.ai_byte, self.ai_address],
			#tech_jump
			[self.ai_byte, self.ai_compare_trig, self.ai_technology, self.ai_byte, self.ai_address],
			#random_call
			[self.ai_byte, self.ai_address],
			#attack_rand
			[self.ai_byte, self.ai_byte, self.ai_military],
			#supply
			[self.ai_byte, self.ai_compare_trig, self.ai_word, self.ai_supply,
				self.ai_unit_or_group, self.ai_race, self.ai_address],
			#time
			[self.ai_compare_trig,self.ai_dword,self.ai_time_type,self.ai_address],
			#resources
			[self.ai_byte, self.ai_compare_trig,self.ai_resource_type,self.ai_dword,self.ai_address],
			#set_id
			[self.ai_byte],
			#remove_build
			[self.ai_byte,self.ai_unit_or_group,self.ai_byte],
			#guard
			[self.ai_unit,self.ai_point,self.ai_byte,self.ai_byte,self.ai_byte],
			#base_layout
			[self.ai_unit,self.ai_layout_action,self.ai_area,self.ai_byte,self.ai_byte],
			#print
			[self.ai_string],
			#attacking
			[self.ai_bool_compare,self.ai_address],
		]
		self.builds = []
		for c in [6,19,20,21,22,69]:
			self.builds.append(self.labels[c])
			self.builds.append(self.short_labels[c])
		self.starts = []
		for c in [3,4,56]:
			self.starts.append(self.labels[c])
			self.starts.append(self.short_labels[c])
		self.types = {
			'byte':[self.ai_byte,self.ai_word,self.ai_dword],
			'word':[self.ai_word,self.ai_dword],
			'dword':[self.ai_dword],
			'unit':[self.ai_unit],
			'building':[self.ai_building,self.ai_unit],
			'military':[self.ai_military,self.ai_unit],#,self.ai_ggmilitary,self.ai_agmilitary,self.ai_gamilitary,self.ai_aamilitary
			'gg_military':[self.ai_ggmilitary,self.ai_gamilitary,self.ai_military,self.ai_unit],
			'ag_military':[self.ai_agmilitary,self.ai_aamilitary,self.ai_military,self.ai_unit],
			'ga_military':[self.ai_gamilitary,self.ai_ggmilitary,self.ai_military,self.ai_unit],
			'aa_military':[self.ai_aamilitary,self.ai_agmilitary,self.ai_military,self.ai_unit],
			'upgrade':[self.ai_upgrade],
			'technology':[self.ai_technology],
			'string':[self.ai_string],
			'compare':[self.ai_compare],
			'compare_trig':[self.ai_compare_trig],
			'race':[self.ai_race],
			'layout_action':[self.ai_layout_action],
			'bool_compare''':[self.ai_bool_compare],
			'supply_type':[self.ai_supply],
			'time_type':[self.ai_time_type],
			'resource':[self.ai_resource_type],
			'order':[self.ai_order],
			'area':[self.ai_area],
			'point':[self.ai_point],
			'unit_id':[self.ai_unit_id],
			'unit_group':[self.ai_unit_or_group],
			'issue_order_flags':[self.ai_issue_order_flags],
			'idle_order':[self.ai_idle_order],
			'idle_order_flags':[self.ai_idle_order_flags],
			'aicontrol':[self.ai_control_type],
		}
		self.typescanbe = {
			'byte':[self.ai_byte],
			'word':[self.ai_word,self.ai_byte],
			'dword':[self.ai_dword,self.ai_word,self.ai_byte],
			'unit':[self.ai_unit,self.ai_building,self.ai_military,self.ai_ggmilitary,self.ai_agmilitary,self.ai_gamilitary,self.ai_aamilitary],
			'building':[self.ai_building],
			'military':[self.ai_military,self.ai_ggmilitary,self.ai_agmilitary,self.ai_gamilitary,self.ai_aamilitary],
			'gg_military':[self.ai_ggmilitary,self.ai_gamilitary,self.ai_military],
			'ag_military':[self.ai_agmilitary,self.ai_aamilitary,self.ai_military],
			'ga_military':[self.ai_gamilitary,self.ai_ggmilitary,self.ai_military],
			'aa_military':[self.ai_aamilitary,self.ai_agmilitary,self.ai_military],
			'upgrade':[self.ai_upgrade],
			'technology':[self.ai_technology],
			'string':[self.ai_string],
			'compare':[self.ai_compare],
			'compare_trig':[self.ai_compare_trig],
			'race':[self.ai_race],
			'layout_action':[self.ai_layout_action],
			'bool_compare':[self.ai_bool_compare],
			'supply_type':[self.ai_supply],
			'time_type':[self.ai_time_type],
			'resource':[self.ai_resource_type],
			'order':[self.ai_order],
			'area':[self.ai_area],
			'point':[self.ai_point],
			'unit_group':[self.ai_unit,self.ai_building,self.ai_military,self.ai_ggmilitary,self.ai_agmilitary,self.ai_gamilitary,self.ai_aamilitary],
			'issue_order_flags':[self.ai_issue_order_flags],
			'idle_order':[self.ai_order],
			'idle_order_flags':[self.ai_idle_order_flags],
			'aicontrol':[self.ai_control_type],
		}
		self.script_endings = [0,36,39,57,65,97] #goto, stop, debug, racejump, return, kill_thread

	def load_file(self, file, addstrings=False):
		data = load_file(file, 'aiscript.bin')
		try:
			offset = struct.unpack('<L', data[:4])[0]
			ais = odict()
			aisizes = {}
			varinfo = odict()
			aiinfo = {}
			aioffsets = []
			offsets = [offset]
			warnings = []
			while data[offset:offset+4] != '\x00\x00\x00\x00':
				id,loc,string,flags = struct.unpack('<4s3L', data[offset:offset+16])
				if id in ais:
					raise PyMSError('Load',"Duplicate AI ID '%s'" % id)
				offset += 16
				if loc and not loc in offsets:
					offsets.append(loc)
				elif not loc and not id in self.bwscript.ais:
					if self.nobw:
						warnings.append(PyMSWarning('Load',"The AI with ID '%s' is in bwscript.bin but not bwscript.bin was loaded. The ID has been discarded." % id, level=1))
					else:
						warnings.append(PyMSWarning('Load',"The AI with ID '%s' is supposed to be but is not in bwscript.bin. The ID has been discarded." % id, level=1))
					continue
				if string > len(self.tbl.strings):
					if addstrings:
						if string-len(self.tbl.strings) > 1:
							self.tbl.strings.extend(['Generated by PyAI\x00'] * (string-len(self.tbl.strings)-1))
						self.tbl.strings.append('Custom name generated by PyAI for AI with ID: %s\x00' % id)
						warnings.append(PyMSWarning('Load',"The AI with ID '%s' had a custom string (#%s) not present in the stat_txt.tbl, so PyAI generated one." % (id,string), level=1))
					else:
						raise PyMSError('Load',"String id '%s' is not present in the stat_txt.tbl" % string)
				aioffsets.append([id,loc,string-1,flags])
			offset += 4
			offsets.sort()
			try:
				externaljumps = [[{},{}],[dict(self.bwscript.externaljumps[1][0]),dict(self.bwscript.externaljumps[1][1])]]
			except:
				externaljumps = [[{},{}],[{},{}]]
			totaloffsets = {}
			findtotaloffsets = {}
			checknones = []
			for id,loc,string,flags in aioffsets:
				ais[id] = [loc,string,flags,[],[]]
				if loc:
					curdata = data[loc:offsets[offsets.index(loc)+1]]
					curoffset = 0
					cmdoffsets = []
					findoffset = {}
					while curoffset < len(curdata):
						if curoffset+loc in findtotaloffsets:
							for fo in findtotaloffsets[curoffset+loc]:
								ais[fo[0]][4][fo[1]] = [id,len(cmdoffsets)]
								fo[2][fo[3]] = [id,len(cmdoffsets)]
								ais[id][4].append(len(cmdoffsets))
								if not id in externaljumps[0][0]:
									externaljumps[0][0][id] = {}
								if not len(cmdoffsets) in externaljumps[0][0][id]:
									externaljumps[0][0][id][len(cmdoffsets)] = []
								externaljumps[0][0][id][len(cmdoffsets)].append(fo[0])
								if not fo[0] in externaljumps[0][1]:
									externaljumps[0][1][fo[0]] = []
								if not id in externaljumps[0][1][fo[0]]:
									externaljumps[0][1][fo[0]].append(id)
							del findtotaloffsets[curoffset+loc]
						if curoffset in findoffset:
							for fo in findoffset[curoffset]:
								ais[id][4][fo[0]] = len(cmdoffsets)
								fo[1][fo[2]] = len(cmdoffsets)
							del findoffset[curoffset]
						totaloffsets[curoffset+loc] = [id,len(cmdoffsets)]
						cmdoffsets.append(curoffset)
						cmd,curoffset = ord(curdata[curoffset]),curoffset + 1
						#print id,loc,curoffset,self.short_labels[cmd]
						if not cmd and curoffset == len(curdata):
							break
						if cmd >= len(self.labels):
							raise PyMSError('Load','Invalid command, could possibly be a corrrupt aiscript.bin')
						ai = [cmd]
						if self.parameters[cmd]:
							for p in self.parameters[cmd]:
								d = p(curdata[curoffset:])
								if p == self.ai_address:
									if d[1] < loc:
										if d[1] not in totaloffsets:
											raise PyMSError('Load','Incorrect jump location, it could possibly be a corrupt aiscript.bin')
										tos = totaloffsets[d[1]]
										ais[id][4].append(tos)
										ai.append(tos)
										# print tos
										# print externaljumps
										if not tos[0] in externaljumps[0][0]:
											externaljumps[0][0][tos[0]] = {}
										if not tos[1] in externaljumps[0][0][tos[0]]:
											externaljumps[0][0][tos[0]][tos[1]] = []
										externaljumps[0][0][tos[0]][tos[1]].append(id)
										if not id in externaljumps[0][1]:
											externaljumps[0][1][id] = []
										if not tos[0] in externaljumps[0][1][id]:
											externaljumps[0][1][id].append(tos[0])
									elif d[1] >= offsets[offsets.index(loc)+1]:
										if not d[1] in findtotaloffsets:
											findtotaloffsets[d[1]] = []
										findtotaloffsets[d[1]].append([id,len(ais[id][4]),ai,len(ai)])
										ais[id][4].append(None)
										ai.append(None)
									elif d[1] - loc in cmdoffsets:
										pos = cmdoffsets.index(d[1] - loc)
										ais[id][4].append(pos)
										ai.append(pos)
									else:
										if not d[1] - loc in findoffset:
											findoffset[d[1] - loc] = []
										findoffset[d[1] - loc].append([len(ais[id][4]),ai,len(ai)])
										ais[id][4].append(None)
										ai.append(None)
								else:
									ai.append(d[1])
								curoffset += d[0]
						ais[id][3].append(ai)
					aisizes[id] = curoffset
					if None in ais[id][4]:
						checknones.append(id)
			for c in checknones:
				if None in ais[id][4]:
					raise PyMSError('Load','Incorrect jump location, could possibly be a corrupt aiscript.bin')
#tName<0>v[description]<0>E
#AIID[description]<0>
  #label<0>[description]<0>
  #<0>
  #LN
  #<0>
#<0>
			if offset < len(data):
				def getstr(dat,o):
					i = dat[o:].index('\x00')
					return [dat[o:o+i],o+i+1]
				try:
					info = decompress(data[offset:])
					offset = 0
					t = ord(info[offset])-1
					while t > -1:
						offset += 1
						name,offset = getstr(info,offset)
						o,val = self.types[types[t]][0](info[offset:])
						offset += o
						desc,offset = getstr(info,offset)
						varinfo[name] = [t,val[1],desc]
						t = ord(info[offset])-1
					offset += 1
					while info[offset] != '\x00':
						id = info[offset:offset+4]
						offset += 4
						desc,offset = getstr(info,offset)
						aiinfo[id] = [desc,odict(),[]]
						while info[offset] != '\x00':
							label,offset = getstr(info,offset)
							desc,offset = getstr(info,offset)
							aiinfo[id][1][label] = desc
						offset += 1
						p = int(floor(log(len(aiinfo[id][1]),256)))
						s,n = '<' + ['B','H','L','L'][p],[1,2,4,4][p]
						while info[offset:offset+n].replace('\x00',''):
							aiinfo[id][2].append(aiinfo[id][1].getkey(struct.unpack(s,info[offset:offset+n])[0]-1))
							offset += n
						offset += 1
				except:
					aiinfo = {}
					warnings.append(PyMSWarning('Load','Unsupported extra script information section in aiscript.bin, could possibly be corrupt. Continuing without extra script information'))
			self.ais = ais
			self.aisizes = aisizes
			self.externaljumps = externaljumps
			self.varinfo = varinfo
			self.aiinfo = aiinfo
			def pprint(obj, depth=0, max=2):
				depth += 1
				string = ''
				if isinstance(obj, dict) and max:
					if obj:
						string += '{\\\n'
						for key in obj:
							string += '%s%s:' % ('\t'*depth, repr(key))
							string += pprint(obj[key], depth, max-1)
						string += '%s},\\\n' % ('\t'*(depth-1))
					else:
						string += '{},\\\n'
				elif isinstance(obj, list) and max:
					if obj:
						string += '[\\\n'
						for item in obj:
							string += ('%s' % ('\t'*depth))
							string += pprint(item, depth, max-1)
						string += '%s],\\\n' % ('\t'*(depth-1))
					else:
						string += '[],\\\n'
				else:
					string += '%s,\\\n' % (repr(obj),)
				if depth == 1:
					return string[:-3]
				return string
			# print pprint(self.externaljumps)
			return warnings
		except PyMSError:
			raise
		except:
			raise PyMSError('Load',"Unsupported aiscript.bin '%s', could possibly be invalid or corrupt" % file,exception=sys.exc_info())

	#Stages:
	# 0 - Load file
	# 1 - Decompile
	# 2 - Compile
	# 3 - Interpret
	def ai_byte(self, data, stage=0):
		"""byte        - A number in the range 0 to 255"""
		if not stage:
			v = ord(data[0])
		elif stage == 1:
			v = str(data)
		elif stage == 2:
			v = chr(data)
		else:
			try:
				v = int(data)
				if v < 0 or v > 255:
					raise
			except:
				raise PyMSError('Parameter',"Invalid byte value '%s', it must be a number in the range 0 to 255" % data)
		return [1,v]

	def ai_word(self, data, stage=0):
		"""word        - A number in the range 0 to 65535"""
		if not stage:
			v = struct.unpack('<H', data[:2])[0]
		elif stage == 1:
			v = str(data)
		elif stage == 2:
			v = struct.pack('<H', int(data))
		else:
			try:
				v = int(data)
				if v < 0 or v > 65535:
					raise
			except:
				raise PyMSError('Parameter',"Invalid word value '%s', it must be a number in the range 0 to 65535" % data)
		return [2,v]

	def ai_dword(self, data, stage=0):
		"""dword       - A number in the range 0 to 4294967295"""
		if not stage:
			v = struct.unpack('<L', data[:4])[0]
		elif stage == 1:
			v = str(data)
		elif stage == 2:
			v = struct.pack('<L', int(data))
		else:
			try:
				v = int(data)
				if v < 0 or v > 4294967295:
					raise
			except:
				raise PyMSError('Parameter',"Invalid dword value '%s', it must be a number in the range 0 to 4294967295" % data)
		return [4,v]

	def ai_address(self, data, stage=0):
		"""block       - The block label name (Can not be used as a variable type!)"""
		if stage == 1:
			return [2,data]
		return self.ai_word(data, stage)

	def ai_unit(self, data, stage=0):
		"""unit        - A unit ID from 0 to 227, or a full unit name from stat_txt.tbl"""
		if not stage:
			v = ord(data[0])
		elif stage == 1:
			s = self.tbl.strings[data].split('\x00')
			if s[1] != '*':
				v = TBL.decompile_string('\x00'.join(s[:2]), '\x0A\x28\x29\x2C')
			else:
				v = TBL.decompile_string(s[0], '\x0A\x28\x29\x2C')
		elif stage == 2:
			v = chr(data) + '\x00'
		else:
			try:
				v = int(data)
				if -1 > v or v > DAT.UnitsDAT.count:
					raise
			except:
				for i,name in enumerate(self.tbl.strings[:DAT.UnitsDAT.count]):
					n = name.split('\x00')[:2]
					if TBL.compile_string(data) == n[0] or (n[1] != '*' and TBL.compile_string(data) == '\x00'.join(n)):
						v = i
						break
				else:
					raise PyMSError('Parameter',"Unit '%s' was not found" % data)
		return [2,v]

	def ai_unit_id(self, data, stage=0):
		"""unit_id        - Same as unit type, but also accepts 228/None and 229/Any"""
		if stage == 0:
			return self.ai_unit(data, stage)
		elif stage == 1:
			if data == 228:
				v = 'None'
			elif data == 229:
				v = 'Any'
			elif data == 230:
				v = 'Group_Men'
			elif data == 231:
				v = 'Group_Buildings'
			elif data == 232:
				v = 'Group_Factories'
			else:
				return self.ai_unit(data, stage)
		elif stage == 2:
			return self.ai_unit(data, stage)
		elif stage == 3:
			if data.lower() == 'none':
				v = 228
			elif data.lower() == 'any':
				v = 229
			elif data.lower() == 'group_men':
				v = 230
			elif data.lower() == 'group_buildings':
				v = 231
			elif data.lower() == 'group_factories':
				v = 232
			else:
				return self.ai_unit(data, stage)
		return [2,v]

	def ai_unit_or_group(self, data, stage=0):
		"""unit_group        - Same as unit_id, but allows multiple with '|'"""
		if stage == 0:
			v, = struct.unpack('<H', data[:2])
			if v > 0xff00:
				amt = v & 0xff
				sum = 2
				val = []
				for i in range(amt):
					sz, v = self.ai_unit_id(data[sum:], stage)
					sum += sz
					val.append(v)
				return [sum, tuple(val)]
			else:
				sz, v = self.ai_unit_id(data, stage)
				return [sz, (v,)]
		elif stage == 1:
			result = ''
			sum = 0
			for x in data:
				sz, text = self.ai_unit_id(x, stage)
				sum += sz
				if result != '':
					result += ' | '
				result += text
			if len(data) == 1:
				return [sum, result]
			else:
				return [2 + sum, result]
		elif stage == 2:
			result = ''
			if len(data) > 1:
				assert(len(data) <= 0xff)
				result += struct.pack('<H', 0xff00 | len(data))
			for id in data:
				sz, val = self.ai_unit_id(id, stage)
				result += val
			return [len(result), result]
		elif stage == 3:
			tokens = data.split('|')
			result = []
			sum = 0
			for tok in tokens:
				sz, val = self.ai_unit_id(tok.strip(), stage)
				sum += sz
				result.append(val)
			if len(result) == 1:
				return [sum, tuple(result)]
			else:
				return [2 + sum, tuple(result)]

	def ai_order(self, data, stage=0):
		"""order        - An order ID from 0 to 188, or a [hardcoded] order name"""
		if stage == 0:
			v = ord(data[0])
		elif stage == 1:
			v = self.order_names[data]
		elif stage == 2:
			v = chr(data)
		else:
			try:
				v = int(data)
				if -1 > v or v > 188:
					raise
			except:
				data = data.lower()
				if data in self.order_name_to_id:
					v = self.order_name_to_id[data]
				else:
					raise PyMSError('Parameter',"Order '%s' was not found" % data)
		return [1,v]

	def ai_idle_order(self, data, stage=0):
		"""idle_order        - An order ID from 0 to 188, or a [hardcoded] order name,
						or DisableBuiltin or EnableBuiltin"""
		if stage == 1:
			if data == 254:
				v = 'EnableBuiltin'
			elif data == 255:
				v = 'DisableBuiltin'
			else:
				return self.ai_order(data, stage)
		elif stage == 3:
			try:
				v = int(data)
			except:
				data = data.lower()
				if data == 'enablebuiltin':
					v = 254
				if data == 'disablebuiltin':
					v = 255
				else:
					return self.ai_order(data, stage)
		else:
			return self.ai_order(data, stage)
		return [1,v]

	def ai_idle_order_flags(self, data, stage=0):
		"""idle_order_flags        - Any of the following:
			NotEnemies
			Own
			Allied
			Unseen
			Invisible
			RemoveSilentFail
			Remove
		"""
		if stage == 0:
			pos = 0
			current = []
			stack = []
			depth = 0
			while True:
				v, = struct.unpack('<H', data[pos:pos + 2])
				if (v & 0x2f00) >> 8 == 3:
					# i32 amount
					amt, = struct.unpack('<I', data[pos + 2:pos + 6])
					current += [(v, amt)]
					pos += 6
				elif (v & 0x2f00) >> 8 == 4:
					depth += 1
					current += [(v,)]
					stack.append(current)
					current = []
					pos += 2
				elif (v & 0x2f00) >> 8 == 6:
					# u32 units.dat flags
					amt, = struct.unpack('<I', data[pos + 2:pos + 6])
					current += [(v, amt)]
					pos += 6
				elif (v & 0x2f00) >> 8 == 8:
					# u16 low, u16 high
					vars = struct.unpack('<HH', data[pos + 2:pos + 6])
					current += [(v, vars)]
					pos += 6
				else:
					current += [(v,)]
					pos += 2
				if v & 0x2f00 == 0:
					if depth == 0:
						result = current
						return [pos, result]
					else:
						depth -= 1
						finished = current
						current = stack.pop()
						current[-1] = (current[-1][0], finished)
		elif stage == 1:
			size, basic_flags = (
				self.flags(data[-1][0], stage, idle_order_flag_names, idle_order_flag_reverse)
			)
			result = '' if basic_flags == '0' else basic_flags
			for extended in data[:-1]:
				if result != '':
					result += ' | '
				ty = (extended[0] & 0x2f00) >> 8
				val = extended[0] & 0xff
				if ty == 1:
					result += 'SpellEffects(%s)' % flags_to_str(val, spell_effect_names)
				elif ty == 2:
					result += 'WithoutSpellEffects(%s)' % flags_to_str(val, spell_effect_names)
				elif ty == 3:
					# Maybe it's actually fine to just show BROKEN if the script is broken
					# instead of erroring? Users can give better error reports =)
					ty = 'BROKEN'
					compare = 'BROKEN'
					c_id = val & 0xf
					ty_id = (val >> 4) & 0xf
					amount = float(extended[1])
					if c_id == 0:
						compare = 'LessThan'
						amount = str(amount / 256)
					elif c_id == 1:
						compare = 'GreaterThan'
						amount = str(amount / 256)
					elif c_id == 2:
						compare = 'LessThanPercent'
						amount = str(int(amount))
					elif c_id == 3:
						compare = 'GreaterThanPercent'
						amount = str(int(amount))
					if ty_id == 0:
						ty = 'Hp'
					elif ty_id == 1:
						ty = 'Shields'
					elif ty_id == 2:
						ty = 'Health'
					elif ty_id == 3:
						ty = 'Energy'
					elif ty_id == 4:
						ty = 'Hangar'
					result += '%s(%s, %s)' % (ty, compare, amount)
					size += 4
				elif ty == 4:
					subgroup = extended[1]
					sz, self_flags = self.ai_idle_order_flags(subgroup, 1)
					result += 'Self(' + self_flags + ')'
					size += sz
				elif ty == 5:
					_, order_name = self.ai_order(val, 1)
					result += 'Order(%s)' % order_name
				elif ty == 6:
					flags = extended[1]
					if val == 0:
						result += 'UnitFlags(%s)' % flags_to_str(flags, units_dat_flags)
					elif val == 1:
						result += 'WithoutUnitFlags(%s)' % flags_to_str(flags, units_dat_flags)
					size += 4
				elif ty == 7:
					result += 'Targeting(%s)' % flags_to_str(val, idle_orders_targeting_flags)
				elif ty == 8:
					result += "RandomRate(%s, %s)" % (extended[1][0],extended[1][1])
					size += 4
				else:
					raise PyMSError('Parameter', 'Invalid idle_orders encoding')
				size += 2
			if result == '':
				result = '0'
			return [size, result]
		elif stage == 2:
			result = ''
			size = 0
			for x in data:
				result += struct.pack('<H', x[0])
				size += 2
				if (x[0] & 0x2f00) >> 8 == 3:
					result += struct.pack('<I', x[1])
					size += 4
				if (x[0] & 0x2f00) >> 8 == 4:
					sz, res = self.ai_idle_order_flags(x[1], 2)
					size += sz
					result += res
				if (x[0] & 0x2f00) >> 8 == 6:
					result += struct.pack('<I', x[1])
					size += 4
				if (x[0] & 0x2f00) >> 8 == 8:
					result += struct.pack('<HH', x[1][0], x[1][1])
					size += 4
			return [size, result]
		elif stage == 3:
			result = []
			size = 0

			data = data.lower()
			# Finds a subgroup and returns the text with the subgroup removed and subgroup
			# not including the name/parens
			def find_subgroup(text, match):
				assert match.isalpha()
				match = re.search(match + r'\s*[([{]', text)
				if match is None:
					return (text, '')

				pos = match.end()
				open_char = text[pos - 1]
				if open_char == '(':
				    end_char = ')'
				elif open_char == '[':
				    end_char = ']'
				elif open_char == '{':
				    end_char = '}'
				depth = 0
				while pos < len(text):
					if text[pos] == end_char:
						if depth == 0:
							rest = text[:match.start()] + text[pos + 1:]
							subgroup = text[match.end():pos]
							return (rest, subgroup)
						else:
							depth -= 1
					if text[pos] == open_char:
						depth += 1
					pos += 1
				return (text, '')

			while True:
				data, self_flags = find_subgroup(data, 'self')
				if self_flags != '':
					sz, self_flags_bin = self.ai_idle_order_flags(self_flags, 3)
					size += sz + 2
					result += [(0x400, self_flags_bin)]
				else:
					break
			parts = [x.lower().strip() for x in data.split('|')]
			parts = [x for x in parts if x != '']
			parts = [x for x in parts if not x.isspace()]
			simple = []
			extended = []
			depth = 0
			for x in parts:
				old_depth = depth
				depth += x.count('(')
				depth += x.count('[')
				depth += x.count('{')
				depth -= x.count(')')
				depth -= x.count(']')
				depth -= x.count('}')
				if old_depth == 0 and not ('(' in x or '[' in x or '{' in x):
					simple.append(x)
				else:
					if old_depth == 0:
						extended.append(x)
					else:
						extended[-1] = extended[-1] + '|' + x

			for e in extended:
				match = re.match(r'(\w*)\((.*)\)', e)
				if match:
					name = match.group(1)
					if name == 'spelleffects' or name == 'withoutspelleffects':
						flags = match.group(2)
						val = flags_from_str(flags, spell_effect_names_reverse)
						if val >= 0x100:
							raise PyMSError('Parameter', 'Invalid idle_orders flag %s' % e)
						if name == 'spelleffects':
							result += [(0x100 | val,)]
						else:
							result += [(0x200 | val,)]
					elif name in ('hp', 'shields', 'health', 'energy', 'hangar'):
						params = match.group(2).split(',')
						if len(params) != 2:
							raise PyMSError('Parameter', 'Invalid idle_orders flag %s' % e)
						compare = params[0]
						amount = float(params[1])
						val = 0
						if name == 'hp':
							pass
						elif name == 'shields':
							val |= 0x10
						elif name == 'health':
							val |= 0x20
						elif name == 'energy':
							val |= 0x30
						elif name == 'hangar':
							val |= 0x40
						else:
							raise PyMSError('Parameter', 'Invalid idle_orders flag %s' % e)
						if compare == 'lessthan':
							val |= 0x0
							amount *= 256
						elif compare == 'greaterthan':
							val |= 0x1
							amount *= 256
						elif compare == 'lessthanpercent':
							val |= 0x2
						elif compare == 'greaterthanpercent':
							val |= 0x3
						else:
							raise PyMSError('Parameter', 'Invalid idle_orders flag %s' % e)
						result += [(0x300 | val, int(amount))]
						size += 4
					elif name == 'order':
						_, val = self.ai_order(match.group(2).strip(), 3)
						result += [(0x500 | val,)]
					elif name == 'unitflags' or name == 'withoutunitflags':
						flags = match.group(2)
						val = flags_from_str(flags, units_dat_flags_reverse)
						if name == 'unitflags':
							result += [(0x600, val)]
						else:
							result += [(0x601, val)]
						size += 4
					elif name == 'targeting':
						flags = match.group(2)
						val = flags_from_str(flags, idle_orders_targeting_flags_reverse)
						if val >= 0x100:
							raise PyMSError('Parameter', 'Invalid idle_orders targeting flag %s' % e)
						result += [(0x700 | val,)]
					elif name == 'randomrate':
						params = match.group(2).split(',')
						arg1 = int(params[0])
						arg2 = int(params[1])
						result += [(0x800, (arg1,arg2))]
						size += 4
					else:
						raise PyMSError('Parameter', 'Invalid idle_orders flag %s' % e)
					size += 2
				else:
					raise PyMSError('Parameter', 'Invalid idle_orders flag %s' % e)
			basic_size, basic_result = (
				self.flags('|'.join(simple), stage, idle_order_flag_names, idle_order_flag_reverse)
			)
			if basic_result & 0x2f00 != 0:
				raise PyMSError('Parameter', 'Invalid idle_orders flag %s' % str(simple))
			size += basic_size
			result += [(basic_result,)]
			return [size, result]


	def flags(self, data, stage, names, reverse):
		if stage == 0:
			v, = struct.unpack('<H', data[:2])
		elif stage == 1:
			v = flags_to_str(data, names)
		elif stage == 2:
			v = struct.pack('<H', data)
		elif stage == 3:
			v = flags_from_str(data, reverse)
		return [2,v]

	def ai_issue_order_flags(self, data, stage=0):
		"""issue_order_flags        - Any of the following:
			Enemies
			Own
			Allied
			SingleUnit
			EachAtMostOnce
		"""
		return self.flags(data, stage, issue_order_flag_names, issue_order_flag_reverse)

	def ai_point(self, data, stage=0):
		"""point        - A point, either '(x, y)' or 'Loc.{location id}'"""
		if stage == 0:
			v = struct.unpack('<HH', data[:4])
		elif stage == 1:
			if data[0] == 65535:
				v = 'Loc.%d' % data[1]
			else:
				v = '(%d, %d)' % (data[0], data[1])
		elif stage == 2:
			v = struct.pack('<HH', data[0], data[1])
		elif stage == 3:
			try:
				data = data.strip()
				v = None
				if data.lower().startswith('loc.'):
					location_id = int(data[4:])
					v = (65535, location_id)
				elif data[0] == '(' and data[-1] == ')':
					tokens = [x.strip() for x in data[1:-1].split(',')]
					if len(tokens) == 2:
						v = (int(tokens[0]), int(tokens[1]))
				if v is None:
					raise PyMSError('Parameter', 'Invalid syntax for point')
			except PyMSError, e:
				raise e
			except Exception, e:
				raise PyMSError('Parameter', 'Invalid syntax for point (%s)' % e)

		return [4, v]

	def ai_area(self, data, stage=0):
		"""area        - An area in form 'Point [~ radius]'"""
		if stage == 0:
			offset, pos = self.ai_point(data, stage)
			radius, = struct.unpack('<H', data[offset:offset + 2])
			v = (pos, radius)
		elif stage == 1:
			pos, radius = data
			offset, pos_str = self.ai_point(pos, stage)
			if radius != 0:
				v = '%s ~ %d' % (pos_str, radius)
			else:
				v = '%s' % pos_str
		elif stage == 2:
			pos, radius = data
			offset, pos_bytes = self.ai_point(pos, stage)
			v = pos_bytes + struct.pack('<H', radius)
		else:
			halves = [x.strip() for x in data.split('~')]
			if len(halves) > 2:
				raise PyMSError('Parameter','Invalid area syntax')
			offset, pos = self.ai_point(halves[0], stage)
			if len(halves) > 1:
				radius = int(halves[1])
			else:
				radius = 0
			v = (pos, radius)
		return [offset + 2, v]

	def ai_control_type(self, data, stage=0):
		"""aicontrol        - values'"""
		if stage == 0:
			v = ord(data[0])
		elif stage == 1:
			v = aicontrol_names[data]
		elif stage == 2:
			v = struct.pack('<B', data)
		else:
			v = aicontrol_names_rev[data.lower()]
		return [1, v]

	def ai_building(self, data, stage=0):
		"""building    - Same as unit type, but only units that are Buildings, Resource Miners, and Overlords"""
		v = self.ai_unit(data, stage)
		if stage == 3:
			flags = self.unitsdat.get_value(v[1],'SpecialAbilityFlags')
			if not flags & 8 and not flags & 1 and v[1] != 42:
				raise PyMSWarning('Parameter','Unit is not a building, worker, or Overlord', extra=v, level=1, id='building')
		return v

	def ai_military(self, data, stage=0):
		"""military    - Same as unit type, but only military units (not Buildings)"""
		v = self.ai_unit(data, stage)
		if stage == 3:
			flags = self.unitsdat.get_value(v[1],'SpecialAbilityFlags')
			if flags & 1:
				raise PyMSWarning('Parameter','Unit is a building', extra=v, level=1, id='military')
		return v

	def ai_ggmilitary(self, data, stage=0):
		"""gg_military - Same as Military type, but only for defending against an enemy Ground unit attacking your Ground unit"""
		v = self.ai_military(data, stage)
		if stage == 3:
			subunit = self.unitsdat.get_value(v[1],'Subunit1')
			if self.unitsdat.get_value(v[1],'GroundWeapon') == 130 and not self.unitsdat.get_value(v[1],'AttackUnit') in [53,59] \
					and (subunit in [None,228] or (self.unitsdat.get_value(subunit,'GroundWeapon') == 130 and not self.unitsdat.get_value(subunit,'AttackUnit') in [53,59])) \
					and (not self._casters or not v[1] in self._casters):
				raise PyMSWarning('Parameter','Unit has no ground weapon, and is not marked as a @spellcaster', extra=v, level=1, id='gg_military')
		return v

	def ai_agmilitary(self, data, stage=0):
		"""ag_military - Same as Military type, but only for defending against an enemy Air unit attacking your Ground unit"""
		v = self.ai_military(data, stage)
		if stage == 3:
			subunit = self.unitsdat.get_value(v[1],'Subunit1')
			if self.unitsdat.get_value(v[1],'AirWeapon') == 130 and self.unitsdat.get_value(v[1],'AttackUnit') != 53 \
					and (subunit in [None,228] or (self.unitsdat.get_value(subunit,'AirWeapon') == 130 and self.unitsdat.get_value(subunit,'AttackUnit') != 53)) \
					and (not self._casters or not v[1] in self._casters):
				raise PyMSWarning('Parameter','Unit has no air weapon, and is not marked as a @spellcaster', extra=v, level=1, id='ag_military')
		return v

	def ai_gamilitary(self, data, stage=0):
		"""ga_military - Same as Military type, but only for defending against an enemy Ground unit attacking your Air unit"""
		v = self.ai_military(data, stage)
		if stage == 3:
			subunit = self.unitsdat.get_value(v[1],'Subunit1')
			if self.unitsdat.get_value(v[1],'GroundWeapon') == 130 and not self.unitsdat.get_value(v[1],'AttackUnit') in [53,59] \
					and (subunit in [None,228] or (self.unitsdat.get_value(subunit,'GroundWeapon') == 130 and not self.unitsdat.get_value(subunit,'AttackUnit') in [53,59])) \
					and (not self._casters or not v[1] in self._casters):
				raise PyMSWarning('Parameter','Unit has no ground weapon, and is not marked as a @spellcaster', extra=v, level=1, id='ga_military')
		return v

	def ai_aamilitary(self, data, stage=0):
		"""aa_military - Same as Military type, but only for defending against an enemy Air unit attacking your Air unit"""
		v = self.ai_military(data, stage)
		if stage == 3:
			subunit = self.unitsdat.get_value(v[1],'Subunit1')
			if self.unitsdat.get_value(v[1],'AirWeapon') == 130 and self.unitsdat.get_value(v[1],'AttackUnit') != 53 \
					and (subunit in [None,228] or (self.unitsdat.get_value(subunit,'AirWeapon') == 130 and not self.unitsdat.get_value(subunit,'AttackUnit') != 53)) \
					and (not self._casters or not v[1] in self._casters):
				raise PyMSWarning('Parameter','Unit has no air weapon, and is not marked as a @spellcaster', extra=v, level=1, id='aa_military')
		return v

	def ai_upgrade(self, data, stage=0):
		"""upgrade     - An upgrade ID from 0 to 60, or a full upgrade name from stat_txt.tbl"""
		if not stage:
			v = ord(data[0])
		elif stage == 1:
			v = TBL.decompile_string(self.tbl.strings[self.upgradesdat.get_value(data,'Label') - 1].split('\x00',1)[0].strip(), '\x0A\x28\x29\x2C')
		elif stage == 2:
			v = chr(data) + '\x00'
		else:
			try:
				v = int(data)
				if -1 > v or v > DAT.UpgradesDAT.count:
					raise
			except:
				for i in range(len(self.upgradesdat.entries)):
					if TBL.compile_string(data) == self.tbl.strings[self.upgradesdat.get_value(i,'Label') - 1].split('\x00', 1)[0].strip():
						v = i
						break
				else:
					raise PyMSError('Parameter',"Upgrade '%s' was not found" % data)
		return [2,v]

	def ai_technology(self, data, stage=0):
		"""technology  - An technology ID from 0 to 43, or a full technology name from stat_txt.tbl"""
		if not stage:
			v = ord(data[0])
		elif stage == 1:
			v = TBL.decompile_string(self.tbl.strings[self.techdat.get_value(data,'Label') - 1].split('\x00',1)[0].strip(), '\x0A\x28\x29\x2C')
		elif stage == 2:
			v = chr(data) + '\x00'
		else:
			try:
				v = int(data)
				if -1 > v or v > DAT.TechDAT.count:
					raise
			except:
				for i in range(len(self.techdat.entries)):
					if TBL.compile_string(data) == self.tbl.strings[self.techdat.get_value(i,'Label') - 1].split('\x00', 1)[0].strip():
						v = i
						break
				else:
					raise PyMSError('Parameter',"Technology '%s' was not found" % data)
		return [2,v]

	def ai_string(self, data, stage=0):
		"""string      - A string of any characters (except for nulls: <0>) in TBL string formatting (use <40> for an open parenthesis '(', <41> for a close parenthesis ')', and <44> for a comma ',')"""
		if not stage:
			e = data.index('\x00')
			return [e+1,TBL.decompile_string(data[:e], '\x0A\x28\x29\x2C')]
		elif stage == 1:
			return [len(data)+1,data]
		elif stage == 2:
			s = TBL.compile_string(data).encode('utf8')
			if '\x00' in s:
				raise PyMSError('Parameter',"String '%s' contains a null (<0>)" % data)
			return [len(s) + 1,s + '\x00']
		return [len(data),data]

	def ai_compare(self, data, stage=0):
		"""compare        - Either LessThan or GreaterThan"""
		if not stage:
			v = ord(data[0])
		elif stage == 1:
			v = 'GreaterThan' if data else 'LessThan'
		elif stage == 2:
			v = chr(data)
		else:
			if data not in ('LessThan','GreaterThan'):
				raise PyMSError('Parameter','Compare must be either LessThan or GreaterThan, got %s instead' % data)
			v = 1 if data == 'GreaterThan' else 0
		return [1,v]

	trig_compare_modes = [
		('AtLeast', 0),
		('AtMost', 1),
		('Set', 7),
		('Add', 8),
		('Subtract', 9),
		('Exactly', 10),
		('Randomize', 11),
		('AtLeast_Call',128),
		('AtMost_Call',129),
		('Exactly_Call',138),
	]

	def ai_compare_trig(self, data, stage=0):
		"""compare_trig        - One of AtLeast, AtMost, Exactly, Set, Add or Subtract"""
		if not stage:
			v = ord(data[0])
		elif stage == 1:
			pair = next((x for x in self.trig_compare_modes if x[1] == data), None)
			if pair is None:
				raise PyMSError('Decompile', 'Unexpected value %d for compare_trig' % data)
			v = pair[0]
		elif stage == 2:
			v = chr(data)
		else:
			pair = next((x for x in self.trig_compare_modes if x[0] == data), None)
			if pair is None:
				raise PyMSError('Parameter', 'Unknown compare %s' % data)
			v = pair[1]
		return [1,v]

	bool_comparisons = [
		('False', 0),
		('True', 1),
		('False_Wait', 64),
		('True_Wait', 65),
		('False_Call', 128),
		('True_Call', 129),
	]

	def ai_bool_compare(self, data, stage=0):
		"""bool_compare        - True or False"""
		if not stage:
			v = ord(data[0])
		elif stage == 1:
			pair = next((x for x in self.bool_comparisons if x[1] == data), None)
			if pair is None:
				raise PyMSError('Decompile', 'Unexpected modifier %d for attacking' % data)
			v = pair[0]
		elif stage == 2:
			v = chr(data)
		else:
			pair = next((x for x in self.bool_comparisons if x[0] == data), None)
			if pair is None:
				raise PyMSError('Parameter', 'Unknown modifier %s' % data)
			v = pair[1]
		return [1,v]

	layout_actions = [
		('Set', 0),
		('Remove', 1),
	]

	def ai_layout_action(self, data, stage=0):
		"""layout_action        - Set or Remove"""
		if not stage:
			v = ord(data[0])
		elif stage == 1:
			pair = next((x for x in self.layout_actions if x[1] == data), None)
			if pair is None:
				raise PyMSError('Decompile', 'Unexpected value %d for layout action' % data)
			v = pair[0]
		elif stage == 2:
			v = chr(data)
		else:
			pair = next((x for x in self.layout_actions if x[0] == data), None)
			if pair is None:
				raise PyMSError('Parameter', 'Unknown action %s' % data)
			v = pair[1]
		return [1,v]

	races = [
		('Zerg', 0),
		('Terran', 1),
		('Protoss', 2),
		('Any_Total', 16),
		('Any_Max', 17),
	]

	def ai_race(self, data, stage=0):
		"""race        - One of Zerg, Terran or Protoss"""
		if not stage:
			v = ord(data[0])
		elif stage == 1:
			pair = next((x for x in self.races if x[1] == data), None)
			if pair is None:
				raise PyMSError('Decompile', 'Unexpected value %d for race' % data)
			v = pair[0]
		elif stage == 2:
			v = chr(data)
		else:
			pair = next((x for x in self.races if x[0] == data), None)
			if pair is None:
				raise PyMSError('Parameter', 'Unknown race %s' % data)
			v = pair[1]
		return [1,v]

	supply_types = [
		('Provided', 0),
		('Used', 1),
		('Max', 2),
		('InUnits', 3),
	]

	def ai_supply(self, data, stage=0):
		"""supply_type        - One of Provided, Used, Max or InUnits"""
		if not stage:
			v = ord(data[0])
		elif stage == 1:
			pair = next((x for x in self.supply_types if x[1] == data), None)
			if pair is None:
				raise PyMSError('Decompile', 'Unexpected value %d for supply type' % data)
			v = pair[0]
		elif stage == 2:
			v = chr(data)
		else:
			pair = next((x for x in self.supply_types if x[0] == data), None)
			if pair is None:
				raise PyMSError('Parameter', 'Unknown supply type %s' % data)
			v = pair[1]
		return [1,v]

	time_types = [
		('Frames', 0),
		('Minutes', 1),
	]

	def ai_time_type(self, data, stage=0):
		"""time_type        - Frames or MInutes"""
		if not stage:
			v = ord(data[0])
		elif stage == 1:
			pair = next((x for x in self.time_types if x[1] == data), None)
			if pair is None:
				raise PyMSError('Decompile', 'Unexpected value %d for time type' % data)
			v = pair[0]
		elif stage == 2:
			v = chr(data)
		else:
			pair = next((x for x in self.time_types if x[0] == data), None)
			if pair is None:
				raise PyMSError('Parameter', 'Unknown  time type %s' % data)
			v = pair[1]
		return [1,v]

	res_types = [
		('Ore', 0),
		('Gas', 1),
		('Any', 2),
	]

	def ai_resource_type(self, data, stage=0):
		"""resource        - Ore, Gas, or Any"""
		if not stage:
			v = ord(data[0])
		elif stage == 1:
			pair = next((x for x in self.res_types if x[1] == data), None)
			if pair is None:
				raise PyMSError('Decompile', 'Unexpected value %d for resource type' % data)
			v = pair[0]
		elif stage == 2:
			v = chr(data)
		else:
			pair = next((x for x in self.res_types if x[0] == data), None)
			if pair is None:
				raise PyMSError('Parameter', 'Unknown  resource type %s' % data)
			v = pair[1]
		return [1,v]

	def interpret(self, files, defs=None, extra=False):
		if not isinstance(files, list):
			files = [files]
		alldata = []
		for file in files:
			try:
				if isstr(file):
					f = open(file,'r')
					alldata.append(f.readlines())
					f.close()
				else:
					alldata.append(file.readlines())
					file.close()
			except:
				raise PyMSError('Interpreting',"Could not load file '%s'" % file)
		ais = odict()
		aisizes = dict(self.aisizes)
		bwsizes = dict(self.bwscript.aisizes)
		aisize = 0
		externaljumps = [[{},{}],[{},{}]]
		bwais = odict()
		varinfo = odict(self.varinfo)
		aiinfo = dict(self.aiinfo)
		bwinfo = dict(self.bwscript.aiinfo)
		curinfo = None
		ai = []
		cmdn = 0
		jumps = {}
		curlabel = []
		warnings = []
		variables = {}
		notused = False
		town = False
		totaljumps = {}
		findtotaljumps = odict()
		findgoto = odict()
		unused = {}
		scriptids = [[],[]]
		nextinfo = None
		multiline = False
		lastmulti = [None,None]
		loaded = []
		self._casters = []
		suppress_warnings = []
		suppress_next_line = []
		suppress_next_line_new = False
		def add_warning(warning):
			if warning.id in suppress_next_line:
				return
			warnings.append(warning)
		def parse_param(parse_fn,d,n=None,line=None):
			try:
				var = None
				var_error = None
				def try_substitute(name):
					result = name
					lower = name.lower()
					if lower in variables:
						for pt in self.typescanbe[parse_fn.__doc__.split(' ',1)[0]]:
							if pt in variables[lower][0]:
								result = variables[lower][1]
								break
						else:
							# Don't immediatly raise type error if the variable alias is valid builtin
							# name (lockdown is a tech alias in the default unitdef.txt, but also
							# an order name)
							var_error = PyMSError(
								'Variable',
								"Incorrect type on variable '%s'. Excpected '%s' but got '%s'" % (
									lower,
									parse_fn.__doc__.split(' ',1)[0],
									variables[lower][0][0].__doc__.split(' ',1)[0]
								),
								n,
								line,
								warnings=warnings
							)
						var = PyMSWarning(
							'Variable',"The variable '%s' of type '%s' was set to '%s'" % (
								name,
								variables[lower][0][0].__doc__.split(' ',1)[0],
								variables[lower][1]
							)
						)
					return result
				if '|' in d:
					# Try substituting the parts
					tokens = d.split('|')
					for i in range(len(tokens)):
						tokens[i] = try_substitute(tokens[i].strip())
					da = '|'.join(tokens)
				else:
					da = try_substitute(d)
				return parse_fn(da,3)
			except PyMSWarning, w:
				w.line = n + 1
				w.code = line
				if var:
					var.warning += ' when the above warning happened'
					w.sub_warnings.append(var)
				add_warning(w)
				return w.extra
			except PyMSError, e:
				if var_error:
					raise var_error
				e.line = n + 1
				e.code = line
				e.warnings = warnings
				if var:
					var.warning += ' when the above error happened'
					e.warnings.append(var)
				raise e
			except Exception, e:
				raise PyMSError('Parameter',"Invalid parameter data '%s', looking for type '%s'.\nDetails: %s" %
						(d,parse_fn.__doc__.split(' ',1)[0], e),n,line, warnings=warnings)
		def load_defs(defname):
			try:
				deffile = os.path.join(os.path.dirname(files[0]),defname)
			except:
				deffile = os.path.abspath(defname)
			if deffile in loaded:
				return
			try:
				d = open(deffile,'r')
				ddata = d.readlines()
				d.close()
			except:
				raise PyMSError('External Definition',"External definition file '%s' was not found" % defname, warnings=warnings)
			for n,l in enumerate(ddata):
				if len(l) > 1:
					line = l.strip().split('#',1)[0]
					if line:
						match = re.match(r'\A@spellcaster\(\s*(\S+?)\s*\)\s*\Z', line)
						if match:
							v = parse_param(self.ai_military, match.group(1))
							self._casters.append(v[1])
							continue
						match = re.match('\\A(\\S+)\\s+(.+)\\s+=\\s+(.+?)(?:\\s*\\{(.+)\\})?\\Z', line)
						if match:
							t,name,dat,vinfo = match.groups()
							if re.match('[\x00,(){}]',name):
								raise PyMSError('External Definition',"The variable name '%s' in external definition file '%s' is invalid, it must not contain a null, or the characters: , ( ) { }" % (name,defname),n,line, warnings=warnings)
							t = t.lower()
							if t == 'label' or t not in self.types:
								raise PyMSError('External Definition',"Invalid variable type '%s' for variable '%s' in external definition file '%s', consult the reference" % (t, name, defname),n,line, warnings=warnings)
							if name.lower() in variables:
								raise PyMSError('External Definition',"The variable name '%s' in external definition file '%s' is already in use" % (name, defname),n,line, warnings=warnings)
							if vinfo:
								add_warning(PyMSWarning('External Definition',"External definition files do not support Information Comments, information is discarded",n,line))
							try:
								v = self.types[t][0](dat,3)[1]
							except PyMSWarning, w:
								w.line = n + 1
								w.code = line
								add_warning(w)
								v = w.extra[1]
							except PyMSError, e:
								e.line = n + 1
								e.code = line
								e.warnings = warnings
								raise e
							except:
								raise PyMSError('External Definition',"Invalid value '%s' for variable '%s' of type '%s' in external definition file '%s'" % (dat, name, t, defname),n,line, warnings=warnings)
							variables[name.lower()] = [self.types[t],dat]
							varinfo[name] = [types.index(t),v,None]
						else:
							raise PyMSError('External Definition','Invalid syntax, unknown line format',n,l, warnings=warnings)
			loaded.append(deffile)
		if defs:
			if isstr(defs):
				defs = defs.split(',')

			for deffile in defs:
				load_defs(deffile)
		for data in alldata:
			for n,l in enumerate(data):
				if len(l) > 1:
					line = l.split('#',1)[0].strip()
					if line:
						if multiline:
							if line.strip() == '}':
								if len(nextinfo) == 3:
									if not nextinfo[0][nextinfo[1]][1][nextinfo[2]].replace('\n',''):
										raise PyMSError('Interpreting','The Information Comment has no text',n,line, warnings=warnings)
									nextinfo[0][nextinfo[1]][1][nextinfo[2]] = nextinfo[0][nextinfo[1]][1][nextinfo[2]][:-1]
								else:
									if not nextinfo[0][nextinfo[1]][0].replace('\n',''):
										raise PyMSError('Interpreting','The Information Comment has no text',n,line, warnings=warnings)
									nextinfo[0][nextinfo[1]][0] = nextinfo[0][nextinfo[1]][0][:-1]
								nextinfo = None
								multiline = False
							elif len(nextinfo) == 3:
								nextinfo[0][nextinfo[1]][1][nextinfo[2]] += line + '\n'
							else:
								nextinfo[0][nextinfo[1]][0] += line + '\n'
						else:
							match = re.match(r'\A\s*@suppress_all\(\s*(\S+?)\s*\)\Z', line)
							if match:
								suppress_warnings.append(match.group(1))
								continue
							match = re.match(r'\A\s*@suppress_next_line\(\s*(\S+?)\s*\)\Z', line)
							if match:
								suppress_next_line.append(match.group(1))
								suppress_next_line_new = True
								continue
							if suppress_next_line:
								if suppress_next_line_new:
									suppress_next_line_new = False
								else:
									suppress_next_line = []
							match = re.match('\\Aextdef\\s*(.+)\\Z',line)
							if match:
								load_defs(match.group(1))
								continue
							match = re.match('\\A(\\S+)\\s+(\\S+)\\s+=\\s+(.+?)(?:\\s*\\{(.+)\\})?\\Z', line)
							if match:
								t,name,dat,vinfo = match.groups()
								if re.match('[\x00,(){}]',name):
									raise PyMSError('Interpreting',"The variable name '%s' is invalid, it must not contain a null, or the characters: , ( ) { }",n,line, warnings=warnings)
								t = t.lower()
								if t == 'label' or t not in self.types:
									raise PyMSError('Interpreting',"Invalid variable type '%s', consult the reference" % t,n,line, warnings=warnings)
								if name.lower() in variables:
									raise PyMSError('Interpreting',"The variable name '%s' is already in use" % name,n,line, warnings=warnings)
								try:
									self.types[t][0](dat,3)
								except PyMSWarning, w:
									w.line = n
									w.code = line
									add_warning(w)
								except PyMSError, e:
									e.line = n + 1
									e.code = line
									e.warnings = warnings
									raise e
								except:
									raise PyMSError('Interpreting',"Invalid variable value '%s' for type '%s'" % (dat, t),n,line, warnings=warnings)
								variables[name.lower()] = [self.types[t],dat]
								varinfo[name] = [types.index(t),self.types[t][0](dat,3)[1],'']
								if vinfo:
									if '\x00' in vinfo:
										raise PyMSError('Interpreting','Information Comments can not contain null bytes',n,line, warnings=warnings)
									varinfo[name][2] = vinfo
									nextinfo = None
								else:
									nextinfo = [2,varinfo[name]]
								continue
							if re.match('\\A[^(]+\\([^)]+\\):\\s*(?:\\{.+\\})?\\Z', line):
								newai = re.match('\\A(.+)\\(\s*(.+)\s*,\s*(.+)\s*,\s*(\w+)\s*\\):\\s*(?:\\{(.+)\\})?\\Z', line)
								if not newai:
									raise PyMSError('Interpreting','Invalid syntax, expected a new script header',n,line, warnings=warnings)
								id = newai.group(1).encode('ascii', 'ignore')
								if id in default_ais:
									id = default_ais[id]
								elif len(id) != 4:
									raise PyMSError('Interpreting',"Invalid AI ID '%s' (must be 4 ascii characeters long, or one of the keywords: Protoss, BWProtoss, Terran, BWTerran, Zerg, BWZerg)" % id,n,line, warnings=warnings)
								elif re.match('[,\x00:()]', id):
									raise PyMSError('Interpreting',"Invalid AI ID '%s', it can not contain a null byte, or the characters: , ( ) :" % id,n,line, warnings=warnings)
								try:
									string = int(newai.group(2))
								except:
									raise PyMSError('Interpreting','Invalid stat_txt.tbl entry (must be an integer)',n,line, warnings=warnings)
								if string < 0 or string >= len(self.tbl.strings):
									raise PyMSError('Interpreting','Invalid stat_txt.tbl entry (must be between 0 and %s)' % (len(self.tbl.strings)-1),n,line, warnings=warnings)
								if not re.match('[01]{3}', newai.group(3)):
									raise PyMSError('Interpreting',"Invalid AI flags '%s' (must be three 0's and/or 1's, see readme for more info)" % newai.group(3),n,line, warnings=warnings)
								if not newai.group(4) in ['bwscript','aiscript']:
									raise PyMSError('Interpreting',"Invalid script file '%s', it must be either 'aiscript' or 'bwscript'" % newai.group(4),n,line, warnings=warnings)
								if ai:
									if not ai[4]:
										raise PyMSError('Interpreting',"AI with ID '%s' has no commands" % ai[0], warnings=warnings)
									if None in ai[5]:
										dat = blocknames[ai[5].index(None)]
										if isstr(dat):
											raise PyMSError('Interpreting',"There is no block with name '%s' in AI with ID '%s'" % (dat,ai[0]), warnings=warnings)
									if ai[0] in findtotaljumps and findtotaljumps[ai[0]]:
										n = findtotaljumps[ai[0]].keys()[0]
										raise PyMSError('Interpreting',"There is no block with name '%s' in AI with ID '%s'" % (n,ai[0]), warnings=warnings)
									if ai[4][-1][0] not in self.script_endings:
										add_warning(PyMSWarning('Interpreting', "The AI with ID '%s' does not end with a stop or definite loop. To ensure your script doesn't run into the next script, it must end with one of: goto(), stop(), debug(), time_jump(), or race_jump()" % ai[0], level=1, id='end'))
									if ai[0] in findgoto:
										for l,f in findgoto[ai[0]].iteritems():
											if f[0]:
												del findgoto[ai[0]][l]
										if not findgoto[ai[0]]:
											del findgoto[ai[0]]
									if ai[1]:
										ais[ai[0]] = ai[1:]
										aisizes[ai[0]] = aisize
									else:
										ais[ai[0]] = ai[1:4] + [[],[]]
										bwais[ai[0]] = [1] + ai[4:]
										bwsizes[ai[0]] = aisize
									for l in curinfo[ai[0]][2]:
										if not l in curinfo[ai[0]][1]:
											curinfo[ai[0]][1][l] = ''
								notused = False
								if newai.group(4) == 'aiscript':
									curinfo = aiinfo
									scriptids[0].append(id)
									loc = 1
								else:
									curinfo = bwinfo
									scriptids[1].append(id)
									loc = 0
								ai = [id,loc,string,convflags(newai.group(3)),[],[]]
								aisize = 0
								curinfo[id] = ['',odict(),[]]
								if newai.group(5):
									if '\x00' in newai.group(5):
										raise PyMSError('Interpreting','Information Comments can not contain null bytes',n,line, warnings=warnings)
									aiinfo[id][0] = newai.group(5)
									nextinfo = None
								else:
									nextinfo = [curinfo,id]
								totaljumps[id] = {}
								curlabel = []
								blocknames = []
								if not id in findgoto:
									findgoto[id] = odict()
								jumps = {}
								town = False
								if ai[0] in ais:
									raise PyMSError('Interpreting',"Duplicate AI ID '%s'" % ai[0],n,line, warnings=warnings)
								cmdn = 0
								continue
							if ai:
								match = re.match('\\A(.+?)\\(\\s*(.+)?\\s*\\)\\Z', line)
								if match:
									cmd = match.group(1).lower()
									if cmd in self.labels:
										ai[4].append([self.labels.index(cmd)])
									elif cmd in self.short_labels:
										ai[4].append([self.short_labels.index(cmd)])
									else:
										raise PyMSError('Interpreting',"Invalid command name '%s'" % cmd,n,line, warnings=warnings)
									if cmd in self.builds and not town:
										add_warning(PyMSWarning('Interpreting',"You may not have initiated a town in the script '%s' with one of the start_* commands before building units" % ai[0],n,line,level=1, id='town'))
									elif cmd in self.starts:
										town = True
									if notused:
										add_warning(PyMSWarning('Interpreting',"Everything after this command and up to the next script or block will never be run",*notused, id='inaccessible'))
										notused = False
									dat = []
									if match.group(2):
										# Should split 'a, (b, c), d' as ['a', '(b, c)', 'd']
										def split_params(text):
											token_start = 0
											pos = 0
											tokens = []
											parens = 0
											while pos < len(text):
												if text[pos] == '(':
													parens += 1
												elif text[pos] == ')':
													parens -= 1
												elif text[pos] == ',' and parens == 0:
													tokens += [text[token_start:pos].strip()]
													token_start = pos + 1
												pos += 1
											last = text[token_start:pos].strip()
											if len(last):
												tokens += [last]
											return tokens
										dat = split_params(match.group(2))
									params = self.parameters[ai[4][-1][0]]
									if params and len(dat) != len(params):
										raise PyMSError('Interpreting','Incorrect amount of parameters (got %s, needed %s)' % (len(dat), len(params)),n,line, warnings=warnings)
									if not params and dat:
										raise PyMSError('Interpreting','Command requires no parameters, but got %s' % len(dat),n,line, warnings=warnings)
									aisize += 1
									if params and dat:
										for d,p in zip(dat,params):
											if p == self.ai_address:
												# Parse script parameter which jumps to a label
												aisize += 2
												match = re.match('\\A(.+):(.+)\\Z', d)
												if match:
													# Full label
													cid,label = match.group(1),match.group(2)
													if cid in default_ais:
														cid = default_ais[cid]
													elif len(cid) != 4:
														raise PyMSError('Interpreting',"Invalid AI ID '%s' (must be 4 characeters long, or one of the keywords: Protoss, BWProtoss, Terran, BWTerran, Zerg, BWZerg)" % cid,n,line, warnings=warnings)
													elif re.match('[\x00:(),]',cid):
														raise PyMSError('Interpreting',"Invalid AI ID '%s', it can not contain a null byte, or the characters: , ( ) :" % cid,n,line, warnings=warnings)
													if re.match('[\x00:(),]',label):
														raise PyMSError('Interpreting',"Invalid label name '%s', it can not contain a null byte, or the characters: , ( ) :" % label,n,line, warnings=warnings)
													if cid in totaljumps:
														if curlabel:
															if label in curlabel:
																add_warning(PyMSWarning('Interpreting',"All loops require at least 1 wait statement. Block '%s' seems to not have one" % label, 'loop'))
															curlabel = []
														if id in scriptids[0]:
															a = 'aiscript'
														else:
															a = 'bwscript'
														if cid in scriptids[0]:
															b = 'aiscript'
														else:
															b = 'bwscript'
														if a != b:
															raise PyMSError('Interpreting',"You can't jump to an external script in '%s.bin' from a script in '%s.bin'" % (b,a),n,line, warnings=warnings)
														if not label in totaljumps[cid]:
															raise PyMSError('Interpreting',"The AI with ID '%s' has no label '%s'" % (cid,label), warnings=warnings)
														tjs = totaljumps[cid][label]
														ai[4][-1].append(tjs)
														ai[5].append(tjs)
														bw = id in scriptids[0]
														if not tjs[0] in externaljumps[bw][0]:
															externaljumps[bw][0][tjs[0]] = {}
														if not tjs[1] in externaljumps[bw][0][tjs[0]]:
															externaljumps[bw][0][tjs[0]][tjs[1]] = []
														externaljumps[bw][0][tjs[0]][tjs[1]].append(id)
														if not id in externaljumps[bw][1]:
															externaljumps[bw][1][id] = []
														if not tjs[0] in externaljumps[bw][1][id]:
															externaljumps[bw][1][id].append(tjs[0])
														if not notused and (cid,label) in unused:
															unused[(cid,label)] = False
													else:
														if not cid in findtotaljumps:
															findtotaljumps[cid] = odict()
														if not label in findtotaljumps[cid]:
															findtotaljumps[cid][label] = []
														findtotaljumps[cid][label].append([ai[4][-1],len(ai[4][-1]),ai[5],len(ai[5]),ai[0]])
														ai[4][-1].append(None)
														ai[5].append(None)
													blocknames.append([cid,label])
													if not cid in findgoto:
														findgoto[cid] = odict()
													findgoto[cid][label] = [True,len(ai[5])-1]
												else:
													# ..else `d` is a simple label
													if curlabel:
														if d in curlabel:
															add_warning(PyMSWarning('Interpreting',"All loops require at least 1 wait statement. Block '%s' seems to not have one" % d, id='loop'))
														curlabel = []
													if type(jumps.get(d)) == int:
														ai[4][-1].append(jumps[d])
														ai[5].append(jumps[d])
													else:
														if not d in jumps:
															jumps[d] = []
														jumps[d].append([ai[4][-1],len(ai[4][-1]),ai[5],len(ai[5])])
														ai[4][-1].append(None)
														ai[5].append(None)
													blocknames.append(d)
													findgoto[id][d] = [True,len(ai[5])-1]
													if not notused and (id,d) in unused:
														unused[(id,d)] = False
												curinfo[id][2].append(d)
											else:
												cs = parse_param(p, d, n, line)
												ai[4][-1].append(cs[1])
												aisize += cs[0]
									if cmd in self.separate:
										notused = (n,line)
									if cmd in self.separate or cmd in self.wait_commands:
										curlabel = []
									cmdn += 1
									nextinfo = None
									continue
								# Match if the line is a label
								match = re.match('\\A--\s*(.+)\s*--\\s*(?:\\{(.+)\\})?\\Z', line)
								if match:
									notused = False
									label = match.group(1)
									if re.match('[\x00:(),]',label):
										raise PyMSError('Interpreting',"Invalid label name '%s', it can not contain a null byte, or the characters: , ( ) :" % label,n,line, warnings=warnings)
									if type(jumps.get(label)) == int:
										raise PyMSError('Interpreting',"There is already a block with the name '%s'" % label,n,line, warnings=warnings)
									curlabel.append(label)
									if ai[0] in findtotaljumps and label in findtotaljumps[ai[0]]:
										if ai[0] in scriptids[0]:
											a = 'aiscript'
										else:
											a = 'bwscript'
										for fj in findtotaljumps[ai[0]][label]:
											if fj[4] in scriptids[0]:
												b = 'aiscript'
											else:
												b = 'bwscript'
											if a != b:
												raise PyMSError('Interpreting',"You can't jump to an external script in '%s.bin' from a script in '%s.bin'" % (a,b),n,line, warnings=warnings)
										for a,y,j,x,i in findtotaljumps[id][label]:
											a[y] = [id,cmdn]
											j[x] = [id,cmdn]
											bw = not ai[0] in scriptids[0]
											if not id in externaljumps[bw][0]:
												externaljumps[bw][0][id] = {}
											if not cmdn in externaljumps[bw][0][id]:
												externaljumps[bw][0][id][cmdn] = []
											externaljumps[bw][0][id][cmdn].append(i)
											if not i in externaljumps[bw][1]:
												externaljumps[bw][1][i] = []
											if not id in externaljumps[bw][1][i]:
												externaljumps[bw][1][i].append(id)
										del findtotaljumps[id][label]
										if not findtotaljumps[id]:
											del findtotaljumps[id]
									if label in jumps:
										for a,y,j,x in jumps[label]:
											a[y] = cmdn
											j[x] = cmdn
										jumps[label] = cmdn
									else:
										jumps[label] = cmdn
										if not label in findgoto[id]:
											findgoto[id][label] = [False,len(ai[5])]
											if not (id,label) in unused:
												unused[(id,label)] = True
									ai[5].append(cmdn)
									totaljumps[id][label] = [id,cmdn]
									curinfo[id][1][label] = ''
									blocknames.append(label)
									if match.group(2):
										if '\x00' in match.group(2):
											raise PyMSError('Interpreting','Information Comments can not contain null bytes',n,line, warnings=warnings)
										curinfo[id][1][label] = match.group(2)
										nextinfo = None
									else:
										nextinfo = [curinfo,id,label]
									continue
							if line.startswith('{'):
								if not nextinfo:
									raise PyMSError('Interpreting','An Information Comment must be afer a variable, a script header, or a block label',n,line, warnings=warnings)
								match = re.match('\\A\\{(?:(.+)\\})?\\Z', line)
								if match.group(1):
									if len(nextinfo) == 3:
										nextinfo[0][curinfo[1]][1][curinfo[2]] = match.group(1)
									else:
										nextinfo[0][curinfo[1]][0] = match.group(1)
									nextinfo = None
								else:
									multiline = True
									lastmulti = [n,line]
								continue
							raise PyMSError('Interpreting','Invalid syntax, unknown line format',n,line, warnings=warnings)
		if multiline:
			raise PyMSError('Interpreting',"There is an unclosed Information Comment in the AI with ID '%s'" % ai[0],lastmulti[0],lastmulti[1], warnings=warnings)
		if ai:
			if not ai[4]:
				raise PyMSError('Interpreting',"AI with ID '%s' has no commands" % ai[0], warnings=warnings)
			if None in ai[5]:
				dat = blocknames[ai[5].index(None)]
				if isstr(dat):
					raise PyMSError('Interpreting',"There is no block with name '%s' in AI with ID '%s'" % (dat,ai[0]), warnings=warnings)
			if ai[0] in findtotaljumps and findtotaljumps[ai[0]]:
				n = findtotaljumps[ai[0]].keys()[0]
				raise PyMSError('Interpreting',"There is no block with name '%s' in AI with ID '%s'" % (n,ai[0]), warnings=warnings)
			if ai[4][-1][0] not in self.script_endings:
				add_warning(PyMSWarning('Interpreting', "The AI with ID '%s' does not end with a stop or definite loop. To ensure your script doesn't run into the next script, it must end with one of: goto(), stop(), debug(), time_jump(), or race_jump()" % ai[0], level=1, id='end'))
			if ai[0] in findgoto:
				for l,f in findgoto[ai[0]].iteritems():
					if f[0]:
						del findgoto[ai[0]][l]
				if not findgoto[ai[0]]:
					del findgoto[ai[0]]
			if ai[1]:
				ais[ai[0]] = ai[1:]
				aisizes[ai[0]] = aisize
			else:
				ais[ai[0]] = ai[1:4] + [[],[]]
				bwais[ai[0]] = [1] + ai[4:]
				bwsizes[ai[0]] = aisize
			for l in curinfo[ai[0]][2]:
				if not l in curinfo[ai[0]][1]:
					curinfo[ai[0]][1][l] = ''
		if findtotaljumps:
			i = findtotaljumps.peek()
			l = i[1].peek()
			raise PyMSError('Interpreting',"The external jump '%s:%s' in AI script '%s' jumps to an AI script that was not found while interpreting (you must include the scripts for all external jumps)" % (i[0],l[0],l[1][0][4]), warnings=warnings)
		s = 2+sum(aisizes.values())
		if s > 65535:
			raise PyMSError('Interpreting',"There is not enough room in your aiscript.bin to compile these changes. The current file is %sB out of the max 65535B, these changes would make the file %sB." % (2+sum(self.aisizes.values()),s))
		s = 2+sum(bwsizes.values())
		if s > 65535:
			raise PyMSError('Interpreting',"There is not enough room in your bwscript.bin to compile these changes. The current file is %sB out of the max 65535B, these changes would make the file %sB." % (2+sum(self.bwsizes.values()),s))
		if findgoto:
			remove = [{},{}]
			for i in findgoto.iteritems():
				if not i[0] in remove:
					remove[i[0] not in aiinfo][i[0]] = []
				for l,f in i[1].iteritems():
					if not f[0]:
						add_warning(PyMSWarning('Interpeting',"The label '%s' in AI script '%s' is unused, label is discarded" % (l,i[0])))
						remove[i[0] not in aiinfo][i[0]].append(f[1])
						if i[0] in aiinfo:
							aiinfo[i[0]][1].remove(l)
						else:
							bwinfo[i[0]][1].remove(l)
			# print remove
			for b,r in enumerate(remove):
				for i in r.iterkeys():
					if r[i]:
						r[i].sort()
						n = 0
						for x in r[i]:
							if b:
								del bwais[i][1][x-n]
							else:
								del ais[i][4][x-n]
							n += 1
		for id,u in unused.iteritems():
			if u and (not id[0] in findgoto or not id[1] in findgoto[id[0]]):
				add_warning(PyMSWarning('Interpeting',"The label '%s' in AI script '%s' is only referenced by commands that cannot be reached and is therefore unused" % (id[1],id[0])))
		if self.ais:
			for id,dat in ais.iteritems():
				self.ais[id] = dat
		else:
			self.ais = ais
		self.aisizes = aisizes
		for a,b in ((0,0),(0,1),(1,0),(1,1)):
			if self.externaljumps[a][b]:
				for id,dat in externaljumps[a][b].iteritems():
					self.externaljumps[a][b][id] = dat
			else:
				self.externaljumps[a][b] = externaljumps[a][b]
		if self.bwscript.ais:
			for id,dat in bwais.iteritems():
				self.bwscript.ais[id] = dat
		else:
			self.bwscript.ais = bwais
		self.bwsizes = bwsizes
		if extra:
			self.varinfo = varinfo
			self.aiinfo = aiinfo
			self.bwscript.aiinfo = bwinfo
		warnings = [w for w in warnings if not w.id in suppress_warnings]
		return warnings

	def reference(self, file):
		file.write('#----------------------------------------------------\n# Parameter Types:\n')
		done = []
		for p in self.parameters:
			if p:
				for t in p:
					if t:
						n = t.__doc__.split(' ',1)[0]
						if not n in done:
							file.write('#    %s\n' % t.__doc__)
							done.append(n)
		file.write('#\n# Commands:\n')
		for c,ps in zip(self.short_labels,self.parameters):
			if c:
				file.write('#    %s(' % c)
				if ps:
					comma = False
					for p in ps:
						if comma:
							file.write(', ')
						else:
							comma = True
						file.write(p.__doc__.split(' ',1)[0])
				file.write(')\n')
		# file.write('#\n# Descriptive Commands:\n')
		# for c,ps in zip(self.labels,self.parameters):
			# if c:
				# file.write('#    %s(' % c)
				# if ps:
					# comma = False
					# for p in ps:
						# if comma:
							# file.write(', ')
						# else:
							# comma = True
						# file.write(p.__doc__.split(' ',1)[0])
				# file.write(')\n')
		file.write('#----------------------------------------------------\n\n')

	def decompile(self, file, defs=None, ref=False, shortlabel=True, scripts=None):
		if isstr(file):
			try:
				f = AtomicWriter(file, 'w')
			except:
				raise PyMSError('Decompile',"Could not load file '%s'" % file, warnings=warnings)
		else:
			f = file
		if scripts == None:
			scripts = self.ais.keys()
		if shortlabel:
			labels = self.short_labels
		else:
			labels = self.labels
		if ref:
			self.reference(f)
		warnings = []
		extjumps = {}
		if defs:
			variables = {}
			if isstr(defs):
				defs = defs.split(',')
			loaded = []
			for dname in defs:
				try:
					deffile = os.path.join(os.path.dirname(file),dname)
				except:
					deffile = os.path.abspath(dname)
				if dname in loaded:
					continue
				try:
					d = open(deffile,'r')
					ddata = d.readlines()
					d.close()
				except:
					raise PyMSError('External Definition',"External definition file '%s' was not found" % dname, warnings=warnings)
				for n,l in enumerate(ddata):
					if len(l) > 1:
						line = l.strip().split('#',1)[0]
						if line:
							match = re.match(r'\A@spellcaster\(\s*(\S+?)\s*\)\s*\Z', line)
							if match:
								continue
							match = re.match('\\A(\\S+)\\s+(.+)\\s+=\\s+(.+?)(?:\\s*\\{(.+)\\})?\\Z', line)
							if match:
								t,name,dat,vinfo = match.groups()
								if re.match('[\x00,(){}]',name):
									raise PyMSError('External Definition',"The variable name '%s' in external definition file '%s' is invalid, it must not contain a null, or the characters: , ( ) { }" % (name,dname),n,line, warnings=warnings)
								t = t.lower()
								if t == 'label' or t not in self.types:
									raise PyMSError('External Definition',"Invalid variable type '%s' for variable '%s' in external definition file '%s', consult the reference" % (t, name, dname),n,line, warnings=warnings)
								if name.lower() in variables:
									raise PyMSError('External Definition',"The variable name '%s' in external definition file '%s' is already in use" % (name, dname),n,line, warnings=warnings)
								if vinfo:
									warnings.append(PyMSWarning('External Definition',"External definition files do not support Information Comments, information is discarded",n,line))
								try:
									v = self.types[t][0](dat,3)[1]
								except PyMSWarning, w:
									w.line = n
									w.code = line
									warnings.append(w)
									v = w.extra[1]
								except PyMSError, e:
									e.line = n + 1
									e.code = line
									e.warnings = warnings
									raise e
								except:
									raise PyMSError('External Definition',"Invalid value '%s' for variable '%s' of type '%s' in external definition file '%s'" % (dat, name, t, dname),n,line, warnings=warnings)
								variables[name.lower()] = [self.types[t],dat]
								self.varinfo[name] = [types.index(t),v,None]
							else:
								raise PyMSError('External Definition','Invalid syntax, unknown line format',n,l, warnings=warnings)
				f.write('extdef %s\n' % dname)
				loaded.append(dname)
			f.write('\n')
		values = {}
		for name,dat in self.varinfo.iteritems():
			vtype = types[dat[0]]
			if dat[2] != None:
				f.write('%s %s = %s' % (vtype,name,dat[1]))
				if dat[2] and not '\n' in dat[2]:
					f.write(' {%s}' % dat[2])
				t = self.types[vtype][0](dat[1],1)[1]
				if t != str(dat[1]):
					f.write(' # Translated Value: %s' % t)
				f.write('\n')
				if dat[2] and '\n' in dat[2]:
					f.write('{\n%s\n}\n' % dat[2])
			if not vtype in values:
				values[vtype] = {}
			values[vtype][dat[1]] = name
		f.write('\n')
		for id in scripts:
			if id not in self.ais:
				raise PyMSError('Decompile',"There is no AI Script with ID '%s'" % id, warnings=warnings)
			loc,string,flags,ai,jumps = self.ais[id]
			if loc:
				cmdn = 0
				if id in extjumps:
					j = len(extjumps[id])
					jump = dict(extjumps[id])
				else:
					j = 0
					jump = {}
				f.write('# stat_txt.tbl entry %s: %s\n%s(%s, %s, aiscript):' % (string,TBL.decompile_string(self.tbl.strings[string]),id,string,convflags(flags)))
				labelnames = None
				if id in self.aiinfo:
					labelnames = self.aiinfo[id][1].copy()
					namenum = 0
					gotonum = 0
					i = self.aiinfo[id][0]
					if '\n' in i:
						f.write('\n\t{\n\t%s\n\t}' % i.replace('\n','\n\t'))
					elif i:
						f.write(' {%s}' % i)
				f.write('\n')
				for cmd in ai:
					if cmdn in jump:
						if cmdn:
							f.write('\n')
						if id in self.externaljumps[0][0] and cmdn in self.externaljumps[0][0][id]:
							s = ''
							if len(self.externaljumps[0][0][id][cmdn]) > 1:
								s = 's'
							f.write('\t\t# Referenced externally by script%s: %s\n' % (s, ', '.join(self.externaljumps[0][0][id][cmdn])))
						f.write('\t\t--%s--' % jump[cmdn])
						if labelnames and jump[cmdn] in labelnames:
							i = labelnames.get(jump[cmdn],'')
							if '\n' in i:
								f.write('\n\t{\n\t%s\n\t}' % i.replace('\n','\n\t'))
							elif i:
								f.write(' {%s}' % i)
						f.write('\n')
					elif cmdn in jumps:
						if labelnames:
							jump[cmdn] = labelnames.getkey(namenum)
						else:
							jump[cmdn] = '%s %04d' % (id,j)
						if cmdn:
							f.write('\n')
						if id in self.externaljumps[0][0] and cmdn in self.externaljumps[0][0][id]:
							s = ''
							if len(self.externaljumps[0][0][id][cmdn]) > 1:
								s = 's'
							f.write('\t\t# Referenced externally by script%s: %s\n' % (s, ', '.join(self.externaljumps[0][0][id][cmdn])))
						f.write('\t\t--%s--' % jump[cmdn])
						if labelnames and jump[cmdn] in labelnames:
							i = labelnames.get(jump[cmdn],'')
							if '\n' in i:
								f.write('\n\t{\n\t%s\n\t}' % i.replace('\n','\n\t'))
							elif i:
								f.write(' {%s}' % i)
						f.write('\n')
						j += 1
					f.write('\t%s(' % labels[cmd[0]])
					if len(cmd) > 1:
						comma = False
						for p,t in zip(cmd[1:],self.parameters[cmd[0]]):
							if comma:
								f.write(', ')
							else:
								comma = True
							temp = t(p,1)
							if t == self.ai_address:
								if type(temp[1]) == list:
									if temp[1][0] in extjumps and temp[1][1] in extjumps[temp[1][0]]:
										f.write('%s:%s' % (temp[1][0],extjumps[temp[1][0]][temp[1][1]]))
									else:
										if not temp[1][0] in extjumps:
											extjumps[temp[1][0]] = {}
										if labelnames:
											t = self.aiinfo[id][2][gotonum]
											n = t.split(':',1)
											f.write(t)
											extjumps[n[0]][temp[1][1]] = n[1]
										else:
											n = '%s %04d' % (temp[1][0],len(extjumps[temp[1][0]]))
											f.write('%s:%s' % (temp[1][0],n))
											extjumps[temp[1][0]][temp[1][1]] = n
								elif temp[1] in jump:
									f.write(jump[temp[1]])
								else:
									if labelnames:
										jump[temp[1]] = self.aiinfo[id][2][gotonum]
									else:
										jump[temp[1]] = '%s %04d' % (id,j)
									f.write(jump[temp[1]])
									j += 1
								if labelnames:
									gotonum += 1
							else:
								for vt in self.typescanbe[t.__doc__.split(' ',1)[0]]:
									vtype = vt.__doc__.split(' ',1)[0]
									if vtype in values and p in values[vtype]:
										f.write(values[vtype][p])
										break
								else:
									f.write(temp[1])
					f.write(')\n')
					if labels[cmd[0]].lower() in self.separate:
						f.write('\n')
					cmdn += 1
				f.write('\n')
			else:
				f.write('# stat_txt.tbl entry %s: %s\n%s(%s, %s, bwscript):' % (string,TBL.decompile_string(self.tbl.strings[string]),id,string,convflags(flags)))
				labelnames = None
				w = self.bwscript.decompile(f, (self.externaljumps,extjumps), values, shortlabel, [id], False)
				if w:
					warnings.extend(w)
		f.close()
		return warnings

	def compile(self, file, bwscript=None, extra=False):
		if isstr(file):
			try:
				f = AtomicWriter(file, 'wb')
			except:
				raise PyMSError('Compile',"Could not load file '%s'" % file)
		else:
			f = file
		warnings = []
		ais = ''
		table = ''
		offset = 4
		totaloffsets = {}
		for id in self.ais.keys():
			loc,string,flags,ai,jumps = self.ais[id]
			if loc:
				cmdn = 0
				totaloffsets[id] = {}
				for cmd in ai:
					if cmdn in jumps:
						totaloffsets[id][cmdn] = offset
					if self.parameters[cmd[0]]:
						for p,t in zip(cmd[1:],self.parameters[cmd[0]]):
							try:
								if t == self.ai_address:
									offset += t(0,2)[0]
								else:
									offset += t(p,2)[0]
							except PyMSWarning, e:
								if not warnings:
									warnings.append(e)
								offset += e.extra[0]
					cmdn += 1
					offset += 1
		offset = 4
		for id in self.ais.keys():
			loc,string,flags,ai,jumps = self.ais[id]
			if loc:
				table += struct.pack('<4s3L', id, offset, string+1, flags)
				for cmd in ai:
					ais += chr(cmd[0])
					if self.parameters[cmd[0]]:
						for p,t in zip(cmd[1:],self.parameters[cmd[0]]):
							try:
								if t == self.ai_address:
									if type(p) == list:
										d = t(totaloffsets[p[0]][p[1]],2)
									else:
										d = t(totaloffsets[id][p],2)
								else:
									d = t(p,2)
							except PyMSWarning, e:
								if not warnings:
									warnings.append(e)
								offset += e.extra[0]
								ais += e.extra[1]
							else:
								ais += d[1]
								offset += d[0]
					offset += 1
			else:
				table += struct.pack('<4s3L', id, 0, string+1, flags)
		f.write('%s%s%s\x00\x00\x00\x00' % (struct.pack('<L', offset),ais,table))
		if extra and (self.varinfo or self.aiinfo):
			info = ''
			for var,dat in self.varinfo.iteritems():
				if dat[2] != None:
					info += '%s%s\x00%s%s\x00' % (chr(dat[0]+1),var,self.types[types[dat[0]]][0](dat[1],2)[1],dat[2])
			info += '\x00'
			for ai,dat in self.aiinfo.iteritems():
				info += '%s%s\x00' % (ai,dat[0])
				for label,desc in dat[1].iteritems():
					info += '%s\x00%s\x00' % (label,desc)
				info += '\x00'
				if dat[2]:
					s = '<' + ['B','H','L','L'][int(floor(log(len(dat[2]),256)))]
					for label in dat[2]:
						if len(dat[2]) < 255:
							info += chr(dat[1].index(label)+1)
						else:
							info += struct.pack(s,dat[1].index(label)+1)
				info += '\x00'
			f.write(compress(info + '\x00',9))
		f.close()
		if bwscript:
			self.bwscript.compile(bwscript, extra)
		return warnings

class BWBIN(AIBIN):
	def __init__(self, units=None, upgrades=None, techs=None, stat_txt=None):
		AIBIN.__init__(self, False, units, upgrades, techs, stat_txt)

	def load_file(self, file):
		data = load_file(file, 'bwscript.bin')
		try:
			offset = struct.unpack('<L', data[:4])[0]
			ais = odict()
			aisizes = {}
			aiinfo = {}
			aioffsets = []
			offsets = [offset]
			while data[offset:offset+4] != '\x00\x00\x00\x00':
				id,loc = struct.unpack('<4sL', data[offset:offset+8])
				if id in ais:
					raise PyMSError('Load',"Duplicate AI ID '%s'" % id)
				if loc and not loc in offsets:
					offsets.append(loc)
				aioffsets.append([id,loc])
				offset += 8
			offset += 4
			offsets.sort()
			warnings = []
			externaljumps = [[{},{}],[{},{}]]
			totaloffsets = {}
			findtotaloffsets = {}
			checknones = []
			for id,loc in aioffsets:
				ais[id] = [loc,[],[]]
				if loc:
					curdata = data[loc:offsets[offsets.index(loc)+1]]
					curoffset = 0
					cmdoffsets = []
					findoffset = {}
					while curoffset < len(curdata):
						if curoffset+loc in findtotaloffsets:
							for fo in findtotaloffsets[curoffset+loc]:
								ais[fo[0]][2][fo[1]] = [id,len(cmdoffsets)]
								fo[2][fo[3]] = [id,len(cmdoffsets)]
								ais[id][2].append(len(cmdoffsets))
								if not id in externaljumps[1][0]:
									externaljumps[1][0][id] = {}
								if not len(cmdoffsets) in externaljumps[1][0][id]:
									externaljumps[1][0][id][len(cmdoffsets)] = []
								externaljumps[1][0][id][len(cmdoffsets)].append(fo[0])
								if not fo[0] in externaljumps[1][1]:
									externaljumps[1][1][fo[0]] = []
								if not id in externaljumps[1][1][fo[0]]:
									externaljumps[1][1][fo[0]].append(id)
							del findtotaloffsets[curoffset+loc]
						if curoffset in findoffset:
							for fo in findoffset[curoffset]:
								ais[id][2][fo[0]] = len(cmdoffsets)
								fo[1][fo[2]] = len(cmdoffsets)
							del findoffset[curoffset]
						totaloffsets[curoffset+loc] = [id,len(cmdoffsets)]
						cmdoffsets.append(curoffset)
						cmd,curoffset = ord(curdata[curoffset]),curoffset + 1
						if not cmd and curoffset == len(curdata):
							break
						if cmd > len(self.labels):
							raise PyMSError('Load','Invalid command, could possibly be a corrrupt bwscript.bin')
						ai = [cmd]
						if self.parameters[cmd]:
							for p in self.parameters[cmd]:
								d = p(curdata[curoffset:])
								if p == self.ai_address:
									if d[1] < loc:
										if d[1] not in totaloffsets:
											raise PyMSError('Load','Incorrect jump location, could possibly be a corrupt bwscript.bin')
										tos = totaloffsets[d[1]]
										ais[id][2].append(tos)
										ai.append(tos)
										if not tos[0] in externaljumps[1][0]:
											externaljumps[1][0][tos[0]] = {}
										if not len(cmdoffsets) in externaljumps[1][0][tos[0]]:
											externaljumps[1][0][tos[0]][tos[1]] = []
										externaljumps[1][0][tos[0]][tos[1]].append(id)
										if not id in externaljumps[1][1]:
											externaljumps[1][1][id] = []
										if not tos[0] in externaljumps[1][1][id]:
											externaljumps[1][1][id].append(tos[0])
									elif d[1] >= offsets[offsets.index(loc)+1]:
										if not d[1] in findtotaloffsets:
											findtotaloffsets[d[1]] = []
										findtotaloffsets[d[1]].append([id,len(ais[id][2]),ai,len(ai)])
										ais[id][2].append(None)
										ai.append(None)
									elif d[1] - loc in cmdoffsets:
										pos = cmdoffsets.index(d[1] - loc)
										ais[id][2].append(pos)
										ai.append(pos)
									else:
										if not d[1] - loc in findoffset:
											findoffset[d[1] - loc] = []
										findoffset[d[1] - loc].append([len(ais[id][2]),ai,len(ai)])
										ais[id][2].append(None)
										ai.append(None)
								else:
									ai.append(d[1])
								curoffset += d[0]
						ais[id][1].append(ai)
					aisizes[id] = curoffset
					if None in ais[id][2]:
						checknones.append(id)
			for c in checknones:
				if None in ais[id][2]:
					raise PyMSError('Load','Incorrect jump location, could possibly be a corrupt bwscript.bin')
			if offset < len(data):
				def getstr(dat,o):
					i = dat[o:].index('\x00')
					return [dat[o:o+i],o+i+1]
				try:
					info = decompress(data[offset:])
					offset = 0
					while info[offset] != '\x00':
						id = info[offset:offset+4]
						offset += 4
						desc,offset = getstr(info,offset)
						aiinfo[id] = [desc,odict(),[]]
						while info[offset] != '\x00':
							label,offset = getstr(info,offset)
							desc,offset = getstr(info,offset)
							aiinfo[id][1][label] = desc
						offset += 1
						p = int(floor(log(len(aiinfo),256)))
						s,n = '<' + ['B','H','L','L'][p],[1,2,4,4][p]
						while info[offset] != '\x00':
							aiinfo[id][2].append(aiinfo[id][1].getkey(struct.unpack(s,info[offset:offset+n])[0]-1))
							offset += n
						offset += 1
				except:
					warnings.append(PyMSWarning('Load','Unsupported extra script information section in bwscript.bin, could possibly be corrupt. Continuing without extra script information'))
			self.ais = ais
			self.aisizes = aisizes
			self.externaljumps = externaljumps
			self.aiinfo = aiinfo
			return warnings
		except PyMSError:
			raise
		except:
			raise PyMSError('Load',"Unsupported bwscript.bin '%s', could possibly be invalid or corrupt" % file,exception=sys.exc_info())

	def decompile(self, filename, extjumps, values, shortlabel=True, scripts=None, close=True):
		if isstr(filename):
			try:
				f = AtomicWriter(filename, 'w')
			except:
				raise PyMSError('Decompile',"Could not load file '%s'" % filename)
		else:
			f = filename
		if scripts == None:
			scripts = self.ais.keys()
		if shortlabel:
			labels = self.short_labels
		else:
			labels = self.labels
		externaljumps = extjumps[0]
		extjumps = extjumps[1]
		warnings = []
		for id in scripts:
			if not id in self.ais:
				raise PyMSError('Decompile',"There is no AI Script with ID '%s'" % id)
			loc,ai,jumps = self.ais[id]
			cmdn = 0
			if id in extjumps:
				j = len(extjumps[id])
				jump = dict(extjumps[id])
			else:
				j = 0
				jump = {}
			labelnames = None
			if id in self.aiinfo:
				labelnames = self.aiinfo[id][1].copy()
				namenum = 0
				gotonum = 0
				i = self.aiinfo[id][0]
				if '\n' in i:
					f.write('\n\t{\n\t%s\n\t}' % i.replace('\n','\n\t'))
				elif i:
					f.write(' {%s}' % i)
			f.write('\n')
			for cmd in ai:
				if cmdn in jump:
					if cmdn:
						f.write('\n')
					if id in self.externaljumps[1][0] and cmdn in self.externaljumps[1][0][id]:
						s = ''
						if len(self.externaljumps[1][0][id][cmdn]) > 1:
							s = 's'
						f.write('\t\t# Referenced externally by script%s: %s\n' % (s, ', '.join(self.externaljumps[1][0][id][cmdn])))
					f.write('\t\t--%s--' % jump[cmdn])
					if labelnames:
						i = labelnames.get(jump[cmdn],'')
						if '\n' in i:
							f.write('\n\t{\n\t%s\n\t}' % i.replace('\n','\n\t'))
						elif i:
							f.write(' {%s}' % i)
						namenum += 1
					f.write('\n')
				elif cmdn in jumps:
					if labelnames:
						jump[cmdn] = labelnames.getkey(namenum)
						namenum += 1
					else:
						jump[cmdn] = '%s %04d' % (id,j)
					if cmdn:
						f.write('\n')
					if id in self.externaljumps[1][0] and cmdn in self.externaljumps[1][0][id]:
						s = ''
						if len(self.externaljumps[1][0][id][cmdn]) > 1:
							s = 's'
						f.write('\t\t# Referenced externally by script%s: %s\n' % (s, ', '.join(self.externaljumps[1][0][id][cmdn])))
					f.write('\t\t--%s--' % jump[cmdn])
					if labelnames and jump[cmdn] in labelnames:
						i = labelnames.get(jump[cmdn],'')
						if '\n' in i:
							f.write('\n\t{\n\t%s\n\t}' % i.replace('\n','\n\t'))
						elif i:
							f.write(' {%s}' % i)
					f.write('\n')
					j += 1
				f.write('\t%s(' % labels[cmd[0]])
				if len(cmd) > 1:
					comma = False
					for p,t in zip(cmd[1:],self.parameters[cmd[0]]):
						if comma:
							f.write(', ')
						else:
							comma = True
						temp = t(p,1)
						if t == self.ai_address:
							if type(temp[1]) == list:
								if temp[1][0] in extjumps and temp[1][1] in extjumps[temp[1][0]]:
									f.write('%s:%s' % (temp[1][0],extjumps[temp[1][0]][temp[1][1]]))
								else:
									if not temp[1][0] in extjumps:
										extjumps[temp[1][0]] = {}
									if labelnames:
										t = self.aiinfo[id][2][gotonum]
										n = t.split(':',1)
										f.write(t)
										extjumps[n[0]][temp[1][1]] = n[1]
									else:
										n = '%s %04d' % (temp[1][0],len(extjumps[temp[1][0]]))
										f.write('%s:%s' % (temp[1][0],n))
										extjumps[temp[1][0]][temp[1][1]] = n
							elif temp[1] in jump:
								f.write(jump[temp[1]])
							else:
								if labelnames:
									jump[temp[1]] = self.aiinfo[id][2][gotonum]
								else:
									jump[temp[1]] = '%s %04d' % (id,j)
								f.write(jump[temp[1]])
								j += 1
							if labelnames:
								gotonum += 1
						else:
							for vt in self.typescanbe[t.__doc__.split(' ',1)[0]]:
								vtype = vt.__doc__.split(' ',1)[0]
								if vtype in values and p in values[vtype]:
									f.write(values[vtype][p])
									break
							else:
								f.write(temp[1])
				f.write(')\n')
				cmdn += 1
			f.write('\n')
		if close:
			f.close()
		return warnings

	def compile(self, file, extra=False):
		if isstr(file):
			try:
				f = AtomicWriter(file, 'wb')
			except:
				raise PyMSError('Compile',"Could not load file '%s'" % file)
		else:
			f = file
		ais = ''
		table = ''
		offset = 4
		totaloffsets = {}
		for id in self.ais.keys():
			loc,ai,jumps = self.ais[id]
			if loc:
				cmdn = 0
				totaloffsets[id] = {}
				for cmd in ai:
					totaloffsets[id][cmdn] = offset
					if self.parameters[cmd[0]]:
						for p,t in zip(cmd[1:],self.parameters[cmd[0]]):
							try:
								if t == self.ai_address:
									offset += t(0,1)[0]
								else:
									offset += t(p,1)[0]
							except PyMSWarning, e:
								if not warnings:
									warnings.append(e)
					cmdn += 1
					offset += 1
		offset = 4
		for id in self.ais.keys():
			loc,ai,jumps = self.ais[id]
			table += struct.pack('<4sL', id, offset)
			for cmd in ai:
				ais += chr(cmd[0])
				if self.parameters[cmd[0]]:
					for p,t in zip(cmd[1:],self.parameters[cmd[0]]):
						try:
							if t == self.ai_address:
								if type(p) == list:
									d = t(totaloffsets[p[0]][p[1]],2)
								else:
									d = t(totaloffsets[id][p],2)
							else:
								d = t(p,2)
							ais += d[1]
							offset += d[0]
						except PyMSWarning, e:
							if not warnings:
								warnings.append(e)
				offset += 1
		f.write('%s%s%s\x00\x00\x00\x00' % (struct.pack('<L', offset),ais,table))
		if extra and self.aiinfo:
			info = ''
			for ai,dat in self.aiinfo.iteritems():
				info += '%s%s\x00' % (ai,dat[0])
				for label,desc in dat[1].iteritems():
					info += '%s\x00%s\x00' % (label,desc)
				info += '\x00'
				for label in dat[2]:
					if len(dat[2]) < 255:
						info += chr(dat[1].index(label)+1)
					else:
						info += struct.pack('<H',dat[1].index(label)+1)
				info += '\x00'
			f.write(compress(info + '\x00',9))
		f.close()
		return []

""" Formats an integer to a flag string, e.g. 'a | b | c | 0x40' """
def flags_to_str(data, names):
	v = ''
	for i in range(32):
		mask = 1 << i
		if data & mask != 0:
			if v != '':
				v += ' | '
			if mask in names:
				v += names[mask]
			else:
				v += hex(mask)
	if v == '':
		v = '0'
	return v

def flags_from_str(data, reverse):
	v = 0
	if data == '':
		return v
	for part in data.split('|'):
		part = part.lower().strip()
		if part in reverse:
			v |= reverse[part]
		else:
			if part.startswith('0x'):
				v |= int(part, 16)
			else:
				v |= int(part, 10)
	return v

# gwarnings = []
# try:
	# import time
	# t = time.time()
#import sys
#sys.stdout = open('debug2.txt','w')
#a = AIBIN()#'bwtest.bin')
#a.load_file('ai.bin')
	# b = AIBIN('')
	# gwarnings.extend(a.warnings)
	# print a.interpret('test.txt')
	# gwarnings.extend(a.load_file('Default\\aiscript.bin'))#'aitest.bin'))
	# for n in a.ais.keys():
		# if n not in ['ZB3C','ZB3E']:
			# del a.ais[n]
	# for n in a.bwscript.ais.keys():
		# if n not in ['ZB3C','ZB3E']:
			# del a.bwscript.ais[n]
	# gwarnings.extend(a.decompile('test.txt'))#, False, True, ['ZB3C','ZB3E']))
	# gwarnings.extend(b.interpret('test.txt'))
	# a.compile('aitest.bin','bwtest.bin')
	# print time.time() - t

	# a = AIBIN('bw.bin')
	# gwarnings.extend(a.load_file('ai.bin'))
	# gwarnings.extend(a.decompile('aitestd.txt'))
	# gwarnings.extend(a.interpret('aitest.txt'))
	# gwarnings.extend(a.compile('ai.bin','bw.bin',True))
# except PyMSError, e:
	# if gwarnings:
		# for warning in gwarnings:
			# print repr(warning)
	# print repr(e)
# except:
	# raise
# else:
	# if gwarnings:
		# for warning in gwarnings:
			# print repr(warning)
