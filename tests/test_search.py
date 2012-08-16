from sc2analyzer import search

replays = {
	'1.sc2replay' : {
		'filename' : '1.sc2replay',
		'p1_name' : 'Sarge',
		'p1_race' : 'Terran',
		'p1_building_order' : [
			(40, 'Supply Depot'),
			(80, 'Barracks'),
			(170, 'Commend Center'),
			(200, 'Supply Depot'),
			(220, 'Barracks'),
			(225, 'Barracks'),
			(240, 'Refinery'),
			(243, 'Refinery'),
			(270, 'Supply Depot'),
			(300, 'Engineering Bay'),
			(310, 'Engineering Bay'),
			(330, 'Supply Depot'),
			(360, 'Factory'),
			(370, 'Supply Depot'),
			(420, 'Starport'),
			(430, 'Supply Depot'),
			(460, 'Barracks'),
			(464, 'Barracks'),
		],
		'p2_name' : 'Anarki',
		'p2_race' : 'Zerg',
		'p2_building_order' : [],
		'length' : 900,
		'winner' : 'p1',
	},
	'2.sc2replay' : {
		'filename' : '2.sc2replay',
		'p1_name' : 'Orbit',
		'p1_race' : 'Protoss',
		'p1_building_order' : [
			(35, 'Pylon'),
			(80, 'Gateway'),
			(90, 'Assimilator'),
			(135, 'Pylon'),
			(150, 'Cybernetics Core'),
			(210, 'Warp Gate'),
		],
		'p2_name' : 'Sarge',
		'p2_race' : 'Terran',
		'p2_building_order' : [
			(40, 'Supply Depot'),
			(80, 'Barracks'),
			(170, 'Refinery'),
			(200, 'Barracks'),
			(220, 'Supply Depot'),
			(225, 'Commend Center'),
		],
		'length' : 1500,
		'winner' : 'p1',
	},
	'3.sc2replay' : {
		'filename' : '3.sc2replay',
		'p1_name' : 'Orbit',
		'p1_race' : 'Protoss',
		'p1_building_order' : [
			(35, 'Pylon'),
			(80, 'Gateway'),
			(90, 'Assimilator'),
			(135, 'Pylon'),
			(150, 'Cybernetics Core'),
			(210, 'Warp Gate'),
		],
		'p2_name' : 'Hunter',
		'p2_race' : 'Protoss',
		'p2_building_order' : [
			(35, 'Pylon'),
			(80, 'Forge'),
			(200, 'Pylon'),
			(180, 'Photon Cannon'),
		],
		'length' : 1400,
		'winner' : 'p2',
	}
}

class ArgsMock(object):
	def __init__(self, **args):
		self.player = ''
		self.max_length = 0
		self.min_length = 0
		self.strategy = []
		self.comp_type = []
		self.win_only = False
		for key,val in args.iteritems():
			setattr(self, key, val)

def test_player_name():
	reps = search.search(replays, ArgsMock(player='Sarge'))
	assert len(reps) == 2 and set(x['filename'] for x in reps) == set(['1.sc2replay', '2.sc2replay'])
	reps = search.search(replays, ArgsMock(player='Anarki'))
	assert len(reps) == 1 and reps[0]['filename'] == '1.sc2replay'
	reps = search.search(replays, ArgsMock(player='Sarge', win_only=True))
	assert len(reps) == 1 and reps[0]['filename'] == '1.sc2replay'

def test_length():
	reps = search.search(replays, ArgsMock(min_length=20))
	assert len(reps) == 2 and set(x['filename'] for x in reps) == set(['2.sc2replay', '3.sc2replay'])
	reps = search.search(replays, ArgsMock(max_length=20))
	assert len(reps) == 1 and reps[0]['filename'] == '1.sc2replay'

def test_comp_type():
	reps = search.search(replays, ArgsMock(comp_type=['TVP']))
	assert len(reps) == 1 and reps[0]['filename'] == '2.sc2replay'
	reps = search.search(replays, ArgsMock(comp_type=['PVP']))
	assert len(reps) == 1 and reps[0]['filename'] == '3.sc2replay'
	reps = search.search(replays, ArgsMock(comp_type=['TVZ','TVP']))
	assert len(reps) == 2 and set(x['filename'] for x in reps) == set(['1.sc2replay', '2.sc2replay'])

def test_strategy():
	reps = search.search(replays, ArgsMock(strategy=['PV*: Pylon, Forge, Pylon']))
	assert len(reps) == 1 and reps[0]['filename'] == '3.sc2replay'
	reps = search.search(replays, ArgsMock(strategy=['TVZ: *, Starport within 8:00']))
	assert len(reps) == 1 and reps[0]['filename'] == '1.sc2replay'
	reps = search.search(replays, ArgsMock(strategy=['TVZ: *, Starport within 6:30']))
	assert len(reps) == 0 
	reps = search.search(replays, ArgsMock(strategy=['TVZ: *, 2 Engineering Bay, * Supply Depot, Factory']))
	assert len(reps) == 1 and reps[0]['filename'] == '1.sc2replay'
