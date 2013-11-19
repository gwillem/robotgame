import random
import rg

class Robot():

  def act(self, game):
    robots = game['robots']
    locs = rg.locs_around(self.location, filter_out=('invalid', 'obstacle'))
    return ['move',random.choice(locs)]
