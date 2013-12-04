import rg
import random

class Robot:
    def act(self, game):
        # if we're in the center, stay put
        if self.location == rg.CENTER_POINT:
            return ['guard']

        # if there are enemies around, attack them
        for loc, bot in game.robots.iteritems():
            if bot.player_id != self.player_id:
                if rg.dist(loc, self.location) <= 1:
                    return ['attack', loc]

        # otherwise, move randomly but prefer non-spawn points
        adj = [x for x in rg.locs_around(self.location) \
                if 'obstacle' not in rg.loc_types(x)]
        
        non_spawn = [x for x in adj if 'spawn' not in rg.loc_types(x)]
        
        possibles = non_spawn or adj
        if possibles:
            return ['move', random.choice(possibles)]
        
        return ['guard']
            
