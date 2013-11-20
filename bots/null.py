from __future__ import division

"""

Essence of this bot:

1. Calculate all proposals for all peers => yield proposals
2. Sort proposals on priority and deterministic algo => yield plan
3. Execute plan for this.robot
4. Profit!

BUGS

* If many bots ATTACK the same location, that's fine! Should fix in 
  _reduce_list_of_dicts, it should require ALL arguments to satisfy 
  (dst=x && action=attack) 

* If a bot is locked AND at spawn point AND can't flee but also can't attack, then it 
  should run!

* self.adjacents is ugly

* If stuck at spawn, go to other spawn

"""

from collections import Counter
import math
import sys
import time
import rg
import os



class Robot():
    def act(self, game):
       return ['suicide']
