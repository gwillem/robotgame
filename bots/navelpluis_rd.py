import rg

def ring_distance(loc, radius=7):
    """ distance to ring around center """
    return abs(rg.wdist(rg.CENTER_POINT, loc) - radius)

class Robot():

    def adjacents(self, location=None, filter_id=None, filter_empty=False):
        
        if not location:
            location = self.location
                    
        locs = rg.locs_around(location, filter_out=('invalid', 'obstacle'))
                    
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
        
    def isolated_enemies(self):
        return [loc for loc in self.enemies() if not self.find_enemy_neighbours(loc)]

    def find_closest(self, locs, center=None):
        if not locs:
            return None
         
        if not center:
            center = self.location
            
        locs.sort(key = lambda x: rg.wdist(center, x) )
        
        return locs[0]
            
    def act(self, game):
        self.robots = game['robots']
        self.turn = game['turn']
        self.target = None

        possible_moves = self.adjacents()

        self.color = "RED" if self.player_id == 0 else "GREEN"
        #~ print "%6s %s, possibles: %s" % (self.color, self.location, possible_moves)

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

            if self.turn >= 60:
                radius = int(self.turn / 10) - 2 # 90 => 7
            else:
                radius = 3

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

