import math
import random
import pprint

CENTER = (9, 9)

# TODO avoid collisions
def distance(loc1, loc2):
  return abs(loc1[0] - loc2[0]) + abs(loc1[1] - loc2[1])

def center_distance(loc):
  return distance(loc, CENTER)

class Robot:
  def adjacents(self):
    return ((self.location[0], self.location[1] + 1),
            (self.location[0], self.location[1] - 1),
            (self.location[0] + 1, self.location[1]),
            (self.location[0] - 1, self.location[1]))

  def act(self, game):
    robots = game['robots']
    locs = self.adjacents()
    # no squares with our bots. enemy bots are fine, we kill them
    locs = [loc for loc in locs if (not robots.get(loc) or (robots.get(loc)['player_id'] != self.player_id))]
    #~ locs = [loc for loc in locs if (not game.get(loc)) or (game.get(loc).player_id != self.player_id)]
    # only squares closer to the center
    locs = [loc for loc in locs if center_distance(loc) < center_distance(self.location)]
    if locs:
      loc = random.choice(locs)
      if game.get(loc):
        return ['attack', loc]
      return ['move', loc]
    return ['guard']
