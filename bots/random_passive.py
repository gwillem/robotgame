import math
import random
import pprint
import basebot

def distance(loc1, loc2):
  return abs(loc1[0] - loc2[0]) + abs(loc1[1] - loc2[1])

def center_distance(loc):
  return distance(loc, CENTER)

class Robot(basebot.BaseBot):

  def act(self, game):
    robots = game['robots']
    locs = self.adjacents()

    #~ if self.location in basebot.SPAWN_COORDS:
        #~ print "I, Robot, am at a spawn location"
    
    # no squares with our bots. enemy bots are fine, we kill them
    #~ locs = [loc for loc in locs if (not robots.get(loc) or (robots.get(loc)['player_id'] != self.player_id))]
    
    # only squares closer to the center
    #~ locs = [loc for loc in locs if center_distance(loc) < center_distance(self.location)]

    valid_choices = []
    
    for loc in locs:
        
        ## don't go there, as we will be crushed by new spawns
        if loc in basebot.SPAWN_COORDS:
            continue
            
        ## already occupied
        if loc in robots:
            continue

        valid_choices.append(loc)
           
    ## stay put
    if not valid_choices: 
        return ['guard']
            
    loc = random.choice(valid_choices)
    #~ if robots.get(loc):
        #~ return ['attack', loc]
    
    return ['move', loc]
    
    
