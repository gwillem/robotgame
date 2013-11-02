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

    print "%6s %s, possibles: %s" % (self.color, self.location, locs)
    
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
    
    print "\tMOVE %s" % (loc,)
    
    return ['move', loc]
    
    
