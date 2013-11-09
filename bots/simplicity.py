import math
import random
import pprint
import basebot

pp = pprint.PrettyPrinter(indent=4)

CENTER = (9, 9)

def distance(loc1, loc2):
	return abs(loc1[0] - loc2[0]) + abs(loc1[1] - loc2[1])

def center_distance(loc):
	return distance(loc, CENTER)


class Robot(basebot.BaseBot):

	def act(self, game):
		locs = self.adjacents()
		robots = game['robots']

		valid_choices = []
		# create list of valid choices
		for loc in locs:
			# Skip spawn locations
			if loc in basebot.SPAWN_COORDS:
				continue

			# Attack everything that's not me
			if loc in robots and robots[loc]['player_id'] != self.player_id:
				return ['attack',loc]

			# Find another spot if i'm already there,
			# and don't klit together, devide and conquer
			if loc in robots and robots[loc]['player_id'] == self.player_id:
				continue

			valid_choices.append(loc)

			if not valid_choices:
				return ['guard']

		# Run around the board, with a preference to the center
		loc1 = random.choice(valid_choices)
		loc2 = random.choice(valid_choices)

		# But with some randomness to throw opponent logic offguard :)
		if center_distance(loc1) < center_distance(loc2) and random.choice[1,2] == 1:
			loc = loc1
		else:
			loc = loc2
			
		return ['move',loc]

			
