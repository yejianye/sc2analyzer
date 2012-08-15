#!/usr/bin/env python
import argparse
import sys
import os
import shutil
import shelve
import msgpack
from ConfigParser import ConfigParser
from collections import OrderedDict
import sc2reader

def player_filter(name):
	return lambda rep: name in rep['p1_name'] or name in rep['p2_name']

def min_length_filter(duration):
	return lambda rep: rep['length'] > duration * 60 

def max_length_filter(duration):
	return lambda rep: rep['length'] < duration * 60

def comp_type_filter(comp_type):
	return lambda rep: set(rep['p1_race'][0], rep['p2_race'][0]) == set(comp_type.upper().split('V'))

def strategy_filter(strategy):
	return lambda rep: BuildingOrder(rep['building_order']).match(strategy)

def search(replays, args):
	def match(rep):
		for filter in filters:
			if isinstance(filter, list):
				if not any(f(rep) for f in filter):
					return False
			else:
				if not filter(map):
					return False
		return True
	filters = []
	if args.player:
		filters.append(player_filter(args.player)
	if args.min_length:
		filters.append(min_length_filter(args.min_length))
	if args.max_length:
		filters.append(min_length_filter(args.max_length))
	if args.comp_type:
		filters.append(map(comp_type_filter, args.comp_type))
	if args.strategy:
		filters.append(map(strategy_filter, args.strategy))
	return match(rep)	

class Strategy(object):
	def __init__(self, definition):
		pass

	def compile(self):
		pass

class BuildingOrder(object):
	def __init__(self, data):
		self.data = data

	def match(strategy):
		return False

	def from_rep_events(self, events):
		pass

	def to_list(self):
		return self.data

class ReplayDB(object):
	_version = '1.0'

	def __init__(self, db_path, rep_path):
		self.db_path = db_path
		self.rep_path = rep_path
		self.data = {}

	def load(self):
		if os.path.exists(self.db_path):
			with open(self.db_path) as f:
				self.data = msgpack.unpack(f)

	def dump(self):
		with open(self.db_path, 'w') as f:
			mspack.pack(self.data, f)

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
	print '\n'.join(rep['filename'] for rep in matched])
	if args.output_dir:
		if not os.path.exists(args.output_dir):
			os.mkdir(args.output_dir)
		[shutil.copy(rep['filename'], args.output_dir) for rep in matched] 

if __name__ == '__main__':
	main()
