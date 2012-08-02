#!/usr/bin/env python
import sys
import time
import argparse 

import sc2reader

import sc2anaylzer.data 

def print_replay_stats(rep):
	print '================'
	print 'Summary'
	print '================'
	stats = [
		('map', rep.map_name),
		('date', rep.date),
		('version', rep.release_string),
		('length', rep.length),
	]
	for title, val in stats:
		print title.capitalize() + ': %s' % val
	for player in rep.players:
		print 'Player %d: %s - %s - %s' % (player.pid, player.name, player.play_race, player.result)

def is_duplicated_events(e1, e2):
	return str(e1) == str(e2)

def get_player_events(player):
	events = [e for e in player.events if isinstance(e, sc2reader.events.AbilityEvent) and e.ability in sc2anaylzer.data.tracked_abilities]
	# for duplicated events, we should only keep the last one
	result = []
	last_evt = None
	for evt in reversed(events):
		if last_evt and not is_duplicated_events(last_evt, evt):
			result.append(last_evt) 
		last_evt = evt
	return result[::-1]

def print_player_stats(player):
	events = get_player_events(player)
	print '================================='
	print '%s - Building Order' % player.name
	print '================================='
	for e in events:
		print e

def main():
	parser = argparse.ArgumentParser(description='Extract game statistics from Starcraft 2 game replay files (.sc2replay)')
	parser.add_argument('FILE', help='Starcraft2 replay file')
	parser.add_argument('--player', type=int, default=0, help="The id of player you'd like to anaylze. 0 for all players.")
	parser.add_argument('--summary', default=False, action='store_true', help="Only print game summary")
	args = parser.parse_args()
	rep = sc2reader.load_replay(args.FILE)
	print_replay_stats(rep)
	if args.summary:
		return 0
	print ''
	for player in rep.players:
		if not args.player or player.pid == args.player:
			print_player_stats(player)
			print ''
	
if __name__ == '__main__':
	sys.exit(main())
