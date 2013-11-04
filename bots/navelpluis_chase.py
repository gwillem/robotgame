import math
import random
import pprint
import basebot

def all(iterable):
    for element in iterable:
        if not element:
            return False
    return True

class Robot(basebot.BaseBot):

    def find_enemy_neighbours(self, center, own_id=None):
        
        if not own_id:
            own_id = self.player_id
            
        neighbours = self.adjacents(center, filter_empty=True, filter_id=own_id)
            
        #~ print "\tFor loc %s, found enemy neighbours (! %s): %s" % (center, own_id, neighbours) 
            
        return neighbours

    def enemies(self):
        return [loc for loc in self.robots if self.robots[loc]['player_id'] != self.player_id]
        
    def isolated_enemies(self):
        return [loc for loc in self.enemies() if not self.find_enemy_neighbours(loc)]

    def find_closest(self, locs, center=None):
        
        if not locs:
            return None
         
        if not center:
            center = self.location
            
        #~ print "\tWill calculate distance from %s to %s" % (center, locs)
             #~ 
        #~ for loc in locs:
            #~ print "\t%s -> %s == %s" % (center, loc, basebot.distance(center,loc) )
             
        locs.sort(key = lambda x: basebot.distance(center, x) )
        
        return locs[0]
            

    def act(self, game):
        self.robots = game['robots']
        self.turn = game['turn']
        self.target = None

        locs = self.adjacents()

        if self.player_id == 0:
            self.color = "RED"
            self.TARGET = (9,3)
        else:
            self.color = "GREEN"
            self.TARGET = (9,15)

        print "%6s %s, possibles: %s" % (self.color, self.location, locs)


            
            

        #~ print "\tMy enemies are          %s" % self.enemies()

        isolated_suckers = self.isolated_enemies()
        #~ print "\tMy isolated enemies are %s" % isolated_suckers
        
        if isolated_suckers:
            self.target = self.find_closest(locs=isolated_suckers)
            #~ print "\tThere are isolated suckers, I found %s to be the closest " % (self.target,)
        
        
        valid_choices = []

        for loc in locs:
            
            ## don't go there, as we will be crushed by new spawns
            if loc in basebot.SPAWN_COORDS:
                continue
                
            ## already occupied by myself
            if loc in self.robots and self.robots[loc]['player_id'] == self.player_id:
                continue

            ## farther away from target
            if self.target and basebot.distance(self.target, loc) > basebot.distance(self.target, self.location):
                #~ print "\tDiscarding %s as it is farther away from target %s than my current location %s" % \
                    #~ (loc, self.TARGET, self.location)
                continue 

            valid_choices.append(loc)

        ## figure out if i'm at a spawn corner, if yes, then move
        all_my_options_are_spawn_coords = all([loc in basebot.SPAWN_COORDS for loc in loc])
        if self.location in basebot.SPAWN_COORDS and all_my_options_are_spawn_coords:
            print "\tWARNING I'm in the corner so i need to move to another spawn coord"
            valid_choices = locs
               
        ## stay put
        if not valid_choices: 
            return ['guard']
                
        loc = random.choice(valid_choices)
        if loc in self.robots:
            print "\tATTACK %s" % (loc,)
            return ['attack', loc]

        print "\tMOVE %s" % (loc,)
        return ['move', loc]


