import random
import rg

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

    def find_enemy_neighbours(self, center, own_id=None):
        
        if not own_id:
            own_id = self.player_id
            
        return self.adjacents(center, filter_empty=True, filter_id=own_id)

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

        locs = self.adjacents()

        isolated_suckers = self.isolated_enemies()
        
        if isolated_suckers:
            self.target = self.find_closest(locs=isolated_suckers)
        
        valid_choices = []

        for loc in locs:
            
            ## already occupied by myself
            if loc in self.robots and self.robots[loc]['player_id'] == self.player_id:
                continue

            ## farther away from target
            if self.target and rg.wdist(self.target, loc) > rg.wdist(self.target, self.location):
                continue 

            valid_choices.append(loc)

              
        ## stay put
        if not valid_choices: 
            return ['guard']
                
        loc = random.choice(valid_choices)
        if loc in self.robots:
            return ['attack', loc]

        return ['move', loc]


