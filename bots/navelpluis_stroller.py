""" This bot walks around randomly. If it encounters an enemy bot, it attacks """

import random
import rg

class Robot():

  def act(self, game):
    robots = game['robots']
    locs = rg.locs_around(self.location, filter_out=('invalid', 'obstacle'))
    
    enemies = [loc for loc in locs if loc in robots and robots[loc]['player_id'] != self.player_id]
    if enemies: ## attack weakest
        loc = sorted(enemies, key=lambda x: robots[x]['hp'])[0]
        return ['attack', loc]
    
    ## so no enemy nearby, walk around randomly but prefer non-spawn points
    
    ## filter out my own occupied spots
    locs = [loc for loc in locs if loc not in robots]
    
    ## empty non spawn points?
    non_spawn = [loc for loc in locs if 'spawn' not in rg.loc_types(loc)]
    if non_spawn:
        loc = random.choice(non_spawn)
        return ['move', loc]
        
    spawn = [loc for loc in locs if 'spawn' in rg.loc_types(loc)]
    if spawn:
        loc = random.choice(spawn)
        return ['move', loc]
        
    ## no more options
    return ['guard']
    
    
