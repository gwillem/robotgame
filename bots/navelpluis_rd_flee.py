import rg
import math

RADIUS = 7

def ring_distance(loc, radius):
    """ distance to ring around center """
    return abs(rg.wdist(rg.CENTER_POINT, loc) - radius)

def locs_average(locs):
    if not locs:
        return (rg.CENTER_POINT)
    
    x = sum([loc[0] for loc in locs]) / len(locs)
    y = sum([loc[1] for loc in locs]) / len(locs)
        
    return (x, y)
    
def vector_mply(loc, x):
    return [round(c * x) for c in loc]
#    return (round(loc[0] * x), round(loc[1] * x))
    
def safe_loc_opposite(loc):
    ## calculates opposite loc of rg.CENTER_POINT
    c = rg.CENTER_POINT
    
    vector_loc_to_center = ( c[0] - loc[0], c[1] - loc[1] )
    dist = rg.dist(loc, c)
    
    if dist == 0: ## enemy concentration is exactly in the center
        ## then it doesnt matter, just go to the border
        return (9,3)
    
    mplier = RADIUS / float(dist)
    v = vector_mply(vector_loc_to_center, mplier)
    
    new = (c[0] + v[0], c[1] + v[1])
    
    #~ print "\tSafe opposite of loc is %s, mplier: %s" %\
        #~ (new, mplier)

    return new

def slope(loca, locb):
    """ slope = dy / dx """
    return float(loca[1] - locb[1]) / float(loca[0] - locb[0])

class Robot():

    def adjacents(self, location=None, filter_id=None, only_empty=False, filter_empty=False):
        
        if not location:
            location = self.location
                    
        locs = rg.locs_around(location, filter_out=('invalid', 'obstacle'))
                    
        if only_empty:
            return [loc for loc in locs if loc not in self.robots]
                    
        if filter_empty:
            locs = [loc for loc in locs if loc in self.robots]
            
        if filter_id:
            locs = [loc for loc in locs if loc not in self.robots \
                or self.robots[loc]['player_id'] != filter_id]
            
        return locs

    def find_enemy_neighbours(self, center=None, own_id=None):
        if not center:
            center = self.location
        
        if not own_id:
            own_id = self.player_id
        
        neighbours = self.adjacents(center, filter_empty=True, filter_id=own_id)
        
        ## lowest hitpoint first
        neighbours.sort(key = lambda x: self.robots[x]['hp'])
        
        return neighbours

    def enemies(self):
        return [loc for loc in self.robots if self.robots[loc]['player_id'] != self.player_id]
        
    def player_concentration(self, player_id):
        locs = [loc for loc in self.robots if self.robots[loc]['player_id'] == player_id]
        
        return locs_average(locs)
        
    def isolated_enemies(self):
        return [loc for loc in self.enemies() if not self.find_enemy_neighbours(loc)]

    def find_closest(self, locs, center=None):
        if not locs:
            return None
         
        if not center:
            center = self.location
            
        locs.sort(key = lambda x: rg.wdist(center, x) )
        
        return locs[0]
            
    def flee_loc_sort(self, loc):
        ## how many neighbours? 
        num_neighbours = len(self.find_enemy_neighbours(loc))
        
        ## how far from flee point?
        dist_to_flee = rg.dist(loc, self.get_flee_point())
        
        return (num_neighbours, dist_to_flee)
        
            
    def try_to_flee(self):
        """ 
        Strategy: don't attack, but run!
        Move to an area with the least amount of surrounding enemies
        """
        possible_moves = self.adjacents(only_empty=True)
        possible_moves = [loc for loc in possible_moves if 'spawn' not in rg.loc_types(loc)]
        
        if not possible_moves: ## todo: raise exception
            #~ print "Am fleeing but no possible moves, so guarding instead!"
            return ['guard']
            
        
        possible_moves.sort(key = self.flee_loc_sort)
        #~ print "Am fleeing to %s" % ( possible_moves[0], )
        return ['move', possible_moves[0]]
        
        
    def get_flee_point(self):
        enemy_concentration = self.player_concentration(self.other_player_id)
        return safe_loc_opposite(enemy_concentration)
        
            
    def act(self, game):
        self.robots = game['robots']
        self.turn = game['turn']
        self.target = None
        self.other_player_id = 1 if self.player_id == 0 else 0

        possible_moves = self.adjacents()

        self.color = "RED" if self.player_id == 0 else "GREEN"
        
        #~ if self.hp < 50:
            #~ print "%6s %2d hp %s" % \
                #~ (self.color, self.hp, self.location)
        
        if self.hp <= 20:
            ## fleeing!
            return self.try_to_flee()

        ## enemies nearby? then always hit
        enemy_neighbours = self.find_enemy_neighbours()
        if enemy_neighbours:
            ## sorted on hp, so weakest target first
            return ['attack', enemy_neighbours[0]] 
            
        valid_choices = []

        for loc in possible_moves:
            
            score = 0
            
            ## don't go there, as we will be crushed by new spawns
            if 'spawn' in rg.loc_types(loc):
                score -= 10
                
            ## already occupied by myself
            if loc in self.robots and self.robots[loc]['player_id'] == self.player_id:
                score -= 50

            if self.turn >= 30:
                radius = int(self.turn / 10) - 2 # 90 => 7
            else:
                radius = 0

            radius = 0 # debug

            ## farther away from target
            new_ring_distance = ring_distance(loc, radius)
            old_ring_distance = ring_distance(self.location, radius)

            if new_ring_distance < old_ring_distance:
                score += 30
            elif new_ring_distance > old_ring_distance:
                score -= 50
            else: # equal
                score += 10

            valid_choices.append((loc,score))
             
        ## filter negative moves
        valid_choices = [item for item in valid_choices if item[1] > 0]
        
        ## stay put
        if not valid_choices: 
            return ['guard']

        ## pick highest score 
        valid_choices.sort(key = lambda x: x[1], reverse = True)
        
        loc = valid_choices[0][0]

        return ['move', loc]


