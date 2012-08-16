#!/usr/bin/env python
# unittest: ../tests/test_search.py
import argparse
import sys
import os
import re
import shutil
import shelve
import msgpack
import bisect
from ConfigParser import ConfigParser
from collections import OrderedDict
import sc2reader

from .data import tracked_building_orders

class InvalidQuantity(Exception):
	pass

class InvalidBuildingOrTechnology(Exception):
	pass

def player_filter(name, win_only):
	return lambda rep: (name in rep['p1_name'] and (not win_only or rep['winner'] == 'p1')) or \
			(name in rep['p2_name'] and (not win_only or rep['winner'] == 'p2'))

def min_length_filter(duration):
	return lambda rep: rep['length'] > duration * 60 

def max_length_filter(duration):
	return lambda rep: rep['length'] < duration * 60

def comp_type_filter(comp_type, win_only):
	def _match(rep):
		if not set((rep['p1_race'][0], rep['p2_race'][0],)) == set(comp_type.upper().split('V')):
			return False
		if win_only:
			first_race = comp_type[0]
			winner = rep['winner']
			return rep[winner + '_race'][0] == comp_type[0]
		return True
	return _match

def strategy_filter(strategy, win_only):
	def _match(rep):
		filters = []
		main_players = strategy.match_comp_type(rep['p1_race'], rep['p2_race'])
		if 1 in main_players and \
			strategy.match_building_order(rep['p1_building_order']) and \
			(not win_only or rep['winner'] == 'p1'):
			return True
		if 2 in main_players and \
			strategy.match_building_order(rep['p2_building_order']) and \
			(not win_only or rep['winner'] == 'p2'):
			return True
		return False
	return _match

def search(replays, args):
	def match(rep):
		for filter in filters:
			if isinstance(filter, list):
				if not any(f(rep) for f in filter):
					return False
			else:
				if not filter(rep):
					return False
		return True
	filters = []
	if args.player:
		filters.append(player_filter(args.player, args.win_only))
	if args.min_length:
		filters.append(min_length_filter(args.min_length))
	if args.max_length:
		filters.append(max_length_filter(args.max_length))
	if args.comp_type:
		print 'args.comp_type', args.comp_type
		filters.append([comp_type_filter(c, args.win_only) for c in args.comp_type])
	if args.strategy:
		filters.append([strategy_filter(Strategy(s), args.win_only) for s in args.strategy])
	return [x for x in replays.itervalues() if match(x)]

class Strategy(object):
	timelimit_ex = re.compile('within ([0-9:]+)$')
	def __init__(self, definition):
		self.compile(definition.strip())

	def compile(self, definition):
		# competition type
		comp_type, definition = definition.split(':', 1)
		self.comp_type = re.compile(comp_type.upper().replace('*', '[TPZ]'))

		# timelimit
		match = self.timelimit_ex.search(definition)
		if match:
			tl = match.groups()[0]
			mins, seconds = map(int, tl.split(':'))
			self.timelimit = mins * 60 + seconds
		else:
			self.timelimit = 0
		definition = self.timelimit_ex.sub('', definition)

		# building order
		self.building_order = re.compile('^' + ''.join(self.process_order_item(x) for x in definition.split(',')))

	def process_order_item(self, item):
		orig_item = item
		item = item.strip()
		if item == '*':
			return '(.*#)*'

		if item[0] == '*' or item[0].isdigit():
			quantity, item = re.split(' +', item, 1)
		else:
			quantity = '1'

		if quantity.isdigit():
			suffix= '{%s}' % quantity
		elif quantity == '*':
			suffix = '*'
		else:
			low, high = map(quantity.split('-'))
			if not low.isdigit() or not high.isdigit():
				raise InvalidQuantity(orig_item)
			suffix = '{%s,%s}' % (low, high)
		
		if item not in tracked_building_orders:
			raise InvalidBuildingOrTechnology(item) 

		return '(%s#)%s' % (item, suffix)

	def match_building_order(self, building_order):
		if self.timelimit > 0 and self.timelimit < building_order[-1][0]:
			index = bisect.bisect_left(building_order, (self.timelimit + 1, ''))
			building_order = building_order[:index]
		return bool(self.building_order.match(''.join(x[1] + '#' for x in building_order)))

	def match_comp_type(self, p1_race, p2_race):
		main_players = []
		# p1 as main player
		comp_type = p1_race[0] + 'V' + p2_race[0]
		if self.comp_type.match(comp_type):
			main_players.append(1)
		# p2 as  main player
		comp_type = p2_race[0] + 'V' + p1_race[0]
		if self.comp_type.match(comp_type):
			main_players.append(2)
		return main_players

class ReplayDB(object):
	_version = '1.0'

	def __init__(self, db_path, rep_path):
		self.db_path = db_path
		self.rep_path = rep_path
		self.load()

	def load(self):
		self.data = {'version' : _version}
		if os.path.exists(self.db_path):
			with open(self.db_path) as f:
				self.data = msgpack.unpack(f)

	def dump(self):
		with open(self.db_path, 'w') as f:
			msgpack.pack(self.data, f)

	@property
	def version(self):
		return self.data.get('version', self._version)
	
	@property
	def replays(self):
		return self.data.get('replays', {})
		
	def update(self):
		modified = False
		for root, dirs, filenames in os.walk(self.rep_path):
			root = os.path.relpath(root, self.rep_path)
			for fname in filenames:
				fname = os.path.join(root, fname)
				if fname.endswith('.sc2replay') and not self.replays.has_key(fname):
					modified = True
					self.replays[fname] = self.parse_replay(fname)
		if modified:
			self.dump()

	def parse_replay(self, filename):
		rep = sc2reader.load_replay(filename)
		assert len(rep.players) == 2, 'Invalid number of players, only 1v1 game is supported'
		info = {
			'map': rep.map_name,
			'date': rep.date,
			'version': rep.release_string,
			'length': rep.length.total_seconds(),
			'winner': 'p%d' % (rep.winner.players[0].pid)
		}
		for player in rep.players:
			info['p%d_name' % player.pid] = player.name
			info['p%d_race' % player.pid] = player.play_race
			info['p%d_building_order'] = self.get_building_order(player.events) 
		return info

	def get_building_order(self, events):
		events = [e for e in events if isinstance(e, sc2reader.events.AbilityEvent) and e.ability in tracked_building_orders]
		# for duplicated events, we should only keep the last one
		result = []
		is_duplicated_events = lambda e1, e2: str(e1) == str(e2)
		last_evt = None
		for evt in reversed(events):
			if last_evt and not is_duplicated_events(last_evt, evt):
				result.append(last_evt) 
			last_evt = evt
		return [(e.second, e.ability) for e in result[::-1]]

class Config(object):
	default_path = os.path.join(os.path.expanduser('~'), 'sc2search.ini')

	def parse(self, filename):
		parser = ConfigParser()
		assert parser.read(filename), "Failed to read configuration file at %s" % filename
		self.rep_path = parser.get('replay', 'rep_path')
		self.db_path = parser.get('replay', 'db_path')
		self.strategies = OrderedDict((sname, parser.get('strategy', sname)) for sname in parser.options('strategy'))

	@classmethod
	def init_default_cfg(cls):
		if not os.path.exists(cls.default_path):
			src = os.path.join(os.path.dirname(__file__), 'sc2search.ini')
			assert os.path.exists(src), "Can't find default configuration file at %s" % src
			shutil.copy(src, cls.default_path)	

def parse_config(filename):
	Config.init_default_cfg()
	cfg = Config()
	cfg.parse(filename)
	return cfg

def print_strategies(strategies):
	for sname, building_order in strategies.iteritems():
		print sname + ':'
		print '    ' + building_order
		print

def main():
	parser = argparse.ArgumentParser(
		formatter_class=argparse.RawDescriptionHelpFormatter,
		description='Search Starcraft2 replays that match specific criteria.',
		epilog="""Examples:
	# Search TVP, TVZ games playered by MarineKing, which duration is longer than 8 mins
	sc2search --player=MarineKing --comp-type=TVP,TVZ --min-length=8

	# Search PVT games in which Protoss player uses Dark Templar rush
	sc2search --strategy=pvt_dt_rush

	# List all strategies and their definition
	sc2search --list-strategies
""")
	parser.add_argument('--player', type=str, help='Find partial match in player names')
	parser.add_argument('--min-length', type=int, help='Find games which duration is longer than specific value (mins)')
	parser.add_argument('--max-length', type=int, help='Find games which duration is shorter than specific value (mins)')
	parser.add_argument('--comp-type', type=str, help='Specify competition type, separated by comma.')
	parser.add_argument('--strategy', type=str, help='Find games in which player uses a specific strategy, separated by comma.') 
	parser.add_argument('--win-only', action='store_true', help="""
		When used along with '--player', only find games in which the specified player won.
		When used along with '--comp-type', only find games in which the first race won. 
		When used along with '--strategy', only find games in which the player using the specified stratey won""") 
	parser.add_argument('--list-strategies', action='store_true', help='List all strategies and their definition.') 
	parser.add_argument('--output-dir', type=str, help='If specified, copy all replays that matched search critiera to a directory.') 
	parser.add_argument('--config', type=str, default=Config.default_path, help='Specify configuration filename. Default config is at %s' % Config.default_path) 
	args = parser.parse_args()

	cfg = parse_config(args.config)
	if args.list_strategies:
		print_strategies(cfg.strategies)
		sys.exit(0)
	if args.strategy:
		try:
			args.strategy = map(cfg.strategies.get, args.strategy.split(','))
		except KeyError as e:
			print "Strategy %s is not defined in configuration file" % e.args
			sys.exit(1)
	if args.comp_type:
		args.comp_type = args.comp_type.split(',')

	db = ReplayDB(cfg.db_path, cfg.rep_path)
	db.update()
	matched = search(db.replays, args)
	print '\n'.join(rep['filename'] for rep in matched)
	if args.output_dir:
		if not os.path.exists(args.output_dir):
			os.mkdir(args.output_dir)
		[shutil.copy(rep['filename'], args.output_dir) for rep in matched] 

if __name__ == '__main__':
	main()
