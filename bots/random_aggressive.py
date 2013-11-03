import math
import random
import pprint
import basebot

class Robot(basebot.BaseBot):

  def act(self, game):
    robots = game['robots']
    locs = self.adjacents()
    
    if self.player_id == 0:
        self.color = "RED"
        self.TARGET = (9,3)
    else:
        self.color = "GREEN"
        self.TARGET = (9,15)

    #~ print "%6s %s, possibles: %s" % (self.color, self.location, locs)
    
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
        if loc in robots and robots[loc]['player_id'] == self.player_id:
            continue

        valid_choices.append(loc)
           
    ## stay put
    if not valid_choices: 
        return ['guard']
            
    loc = random.choice(valid_choices)
    if robots.get(loc):
        return ['attack', loc]
    
    #~ print "\tMOVE %s" % (loc,)
    
    return ['move', loc]
    
    
