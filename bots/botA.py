import rg

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

        self_to_center = rg.wdist(self.location, rg.CENTER_POINT)

        # try to approach the center
        for dst in rg.locs_around(self.location):
            dst_to_center = rg.wdist(dst, rg.CENTER_POINT)
            if dst_to_center < self_to_center:
                return ['move', dst]
        
        # it doesnt matter
        return ['guard']
