from __future__ import division

"""

Essence of this bot:

1. Calculate all proposals for all peers => yield proposals
2. Sort proposals on priority and deterministic algo => yield plan
3. Execute plan for this.robot
4. Profit!

Todo:

* Change proposal dict to ProposedMove
* Change list to ProposedCollection

BUGS

* If many bots ATTACK the same location, that's fine! Should fix in 
  _reduce_list_of_dicts, it should require ALL arguments to satisfy 
  (dst=x && action=attack) 


"""

from collections import Counter
from itertools import chain
import math
import sys
import time
import rg
from pprint import pprint

def _prop_to_dict(prio, action, src, dst=None):
    """ Proposal move to dictionary"""
    
    if not dst:
        dst = src
    
    return {
        'prio': prio,
        'action': action,
        'src': src,
        'dst': dst,
    }
    
def _prop_to_action(prop):
    if prop['action'] in ['guard','suicide']:
        return [ prop['action'] ]
    
    return [ prop['action'], prop['dst'] ]

def _sort_proposals(prop):
    """
    Need deterministic sort, so use these keys:
        1. priority
        2. distance to center (for dst)
        3. atan2 radius to center (for dst)
    """
    
    prio = 1 / prop['prio'] if prop['prio'] else 0
    dist = rg.dist(prop['dst'],rg.CENTER_POINT)
    angle = _angle(prop['dst'])
    
    return (prio, dist, angle)

def is_spawn(loc):
    return 'spawn' in rg.loc_types(loc)

def _angle(loc, center=None):
    if not center:
        center = rg.CENTER_POINT
    dx = loc[0] - center[0]
    dy = loc[1] - center[1]
    return math.atan2(dy, dx) 

def _reduce_list_of_dicts(mylist, **kwargs):
    """ Reduces list of dicts inplace by checking for key/value pairs in dicts as given by kwargs 
    
    >>> a = [
            { 'x' : 1 },
            { 'x' : 2 },
            { 'x' : 3 },
    ]

    >>> _reduce_list(a, x=2)
    >>> print a
    [{'x': 1}, {'x': 3}]
    """
    to_delete = []
    
    for i, item in enumerate(mylist):
        ## do i need to delete this item?
        for k, v in kwargs.items():
            if item[k] == v:
                to_delete.append(i)
                break

    ## slit into separate code, because its tricky to manipulate a 
    ## list and iterate it at the same time
    for i in sorted(to_delete, reverse=True):
        del mylist[i]
                
class Robot():
        
    def act(self, game):
        
        self.robots = game['robots']
        self.turn   = game['turn']
                
        if not hasattr(self, 'history_arena'):
            self.history_arena = {}

        if not hasattr(self, 'history_plan'):
            self.history_plan = {}

        if self.turn not in self.history_arena:
            """ Only do this for the first bot in a turn.
            They all share the same object, so skip redundant calculations """

            print 
            print 
            print 
            print "********** turn %d *********" % game['turn']

            self.history_arena[self.turn] = self.robots

            proposals = self.collect_all_proposals()
            
            print "proposals:"
            #~ pprint(proposals)
            
            plan = self.proposals_to_plan(proposals)
        
            print "plan:"
            #~ pprint(plan)
            
            self.history_plan[self.turn] = plan
            
            if hasattr(self,'breakpoint') and self.breakpoint:
                raw_input("Press Enter to continue...")
                self.breakpoint = False

        plan = self.history_plan[self.turn]

        if self.location not in plan:
            print "Ouch! Fatal error! I couldn't find myself %s in the plan" % (self.location,)
            raise Exception
        
        return plan[self.location]
        
    def adjacents(self, location=None, filter_id=None, filter_empty=False, only_empty=False, only_id=False):
        if not location:
            location = self.location
            
        locs = rg.locs_around(location, filter_out=('invalid', 'obstacle'))
                    
        if only_empty:
            return [loc for loc in locs if loc not in self.robots]
            
        if only_id:
            return [loc for loc in locs if loc in self.robots and self.robots[loc]['player_id'] == only_id]
                    
        if filter_empty:
            locs = [loc for loc in locs if loc in self.robots]
            
        if filter_id:
            locs = [loc for loc in locs if loc not in self.robots \
                or self.robots[loc]['player_id'] != filter_id]
        
        return locs

    def collect_all_proposals(self):
        """ Calculate proposed moves for all of my peers 
        
        Output: proposals = [
            { 
                'prio': 100,
                'action': 'move',
                'src': (x,y),
                'dst': (x,y)
                
            }
        ]
        """
        peers = [loc for loc in self.robots if self.player_id == self.robots[loc]['player_id']]
        #~ print "I found %d peers" % len(peers)
        
        proposals = []
        for peer in peers:
            proposals.extend(self.calculate_proposals_for_loc(peer))
        
        return proposals
        
    
    def try_to_flee(self, src):
        locs = self.adjacents(src, only_empty=True)
        # find locs with least amound of enemy neighbours
        locs = [loc for loc in locs if self.count_enemy_neighbours_for_loc(loc=loc) == 0]
        
        if locs:
            return _prop_to_dict(100, 'move', src, locs[0])
        
        raise RuntimeError("Can't flee! No safe locations")
        
    def attack_weakest_neighbour(self, src):
        enemies = self.enemy_neighbours_for_loc() # already sorted on HP
        return _prop_to_dict(100, 'attack', src, enemies[0])
    
    def find_preemptive_strike(self, src):
        ## which neighbour has most enemy neighbours?
        neighbours = self.adjacents(src, only_empty=True)
        neighbours = [(n,self.count_enemy_neighbours_for_loc(loc=n)) for n in neighbours]
        neighbours.sort(key = lambda x: x[1], reverse=True)
        
        print "%s : %s" % (src, neighbours)
        
        if neighbours and neighbours[0][1]: ## does the no 1 have enemy neighbours?
            return _prop_to_dict(100, 'attack', src, neighbours[0][0]) 
        else:
            return None
    
    def calculate_proposals_for_loc(self, src):
        ## find possible moves
        proposals = []

        ## stand still is also valid
        proposals.append(_prop_to_dict(50, 'guard', src))
        
        now_surrounded = self.count_enemy_neighbours_for_loc(loc=src)
        preemptive_strike = self.find_preemptive_strike(src)
        
        
        """ Pseudo code:
        
        if i_am_surrounded:
            try:
                return try_to_flee
            except: ## no can do
                return attack_weakest_neighbour
                
        if somebody_will_step_in_my_comfort_zone:
            return attack_likeliest_loc
        else:
            move or guard, depending on position and target location (spawn)
            
        """
        
        #~ print "%s : preemptive strike: %s" % (src,preemptive_strike)
        
        if now_surrounded:
            try:
                #~ print "%s : Trying to flee" % (src,)
                proposals.append(self.try_to_flee(src))
            except RuntimeError:
                #~ print "%s : Can't flee, will attack weakest neighbour" % (src,)
                proposals.append(self.attack_weakest_neighbour(src))
                
        elif preemptive_strike: ## todo: predict enemy movement based on previous steps
            #~ self.breakpoint = True
            proposals.append(preemptive_strike)
                    
        else: ## sort possible moves
            possibles = self.adjacents(src, only_empty=True)
            
            src_peer_neighbours = self.count_peer_neighbours_for_loc(src)
            
            for dst in possibles:
                score = 49
                
                dst_peer_neighbours = self.count_peer_neighbours_for_loc(dst) - 1 
                
                #~ print "%s has %d peer neighbours" % (dst, dst_peer_neighbours)
                
                if is_spawn(dst) and not is_spawn(src):
                    #~ print "%s is not in %s" % (dst, rg.loc_types(dst) )
                    score -= 5
                    
                if is_spawn(src):
                    score += 5
                
                if dst_peer_neighbours < src_peer_neighbours:
                    score += (9-dst_peer_neighbours) ## dont exceed 100

                prop = _prop_to_dict(score, 'move', src, dst)
                proposals.append(prop)
        
        ## TODO, continue here
        
        #~ possibles = self.adjacents(src)        
        #~ for dst in possibles:
            #~ 
            #~ ## 1. Do I have enemy neighbour and can I step back?
            #~ 
            #~ ## 2. 
            #~ 
            #~ score = 50
            #~ 
            #~ src_dist = rg.dist(src, rg.CENTER_POINT)
            #~ dst_dist = rg.dist(dst, rg.CENTER_POINT)
            #~ 
            #~ dst_surrounded = self.count_enemy_neighbours_for_loc(loc=dst)
            #~ 
            #~ if dst_surrounded < now_surrounded:
                #~ score += 10 * (10-dst_surrounded)
            #~ elif dst_surrounded > now_surrounded:
                #~ score -= 30
            #~ 
            #~ if dst_dist < src_dist:
                #~ score += 10
            #~ elif dst_dist == src_dist:
                #~ score -= 1
            #~ else:
                #~ score -= 5
            #~ 
            #~ prop = _prop_to_dict(score, 'move', src, dst)
            #~ proposals.append(prop)
        
        return proposals
        
    def proposals_to_plan(self, proposals):
        """ Sort proposals on priority and fill the projected map 
                
        While there are still items in proposals:
        
        1. Check if there are src bots with only 1 option (there is always one, ie 'guard')
           If yes, execute them and remove from proposals.
           
        2. Pop highest-prio item from proposals:
            a. Check if either source or destination hasn't been processed already (yes > skip)
            b. add to moves[] and new/old_field
        
        Input: proposals = [
            { 
                'prio': 100,
                'action': 'move',
                'src': (x,y),
                'dst': (x,y)
                
            }
        ]
        
        Output: plan = {
            (x,y): ['guard'],
            (p,q): ['attack', (y,z)],
        
        }
        """

        proposals.sort(key=_sort_proposals)
        moves = []
        
        while proposals:
            
            #~ print "i have %d props" % len(proposals)
            #~ pprint(proposals)

            ## 1. check if there are bots with one proposal only
            sources = [p['src'] for p in proposals]
            single_src = [ x[0] for x in Counter( sources ).items() if x[1] == 1]
            singles = [p for p in proposals if p['src'] in single_src]
            #~ print "I found %d singles (%s)" % (len(singles), singles)
                        
            if singles:
                to_execute = singles
            else:
                to_execute = [ proposals.pop(0) ]
                
            for prop in to_execute:

                #~ print "will execute prop %s" % prop
                ## remove bots with these src/dst from the proposals list
                _reduce_list_of_dicts(proposals, src=prop['src'])
                _reduce_list_of_dicts(proposals, dst=prop['dst'])

                ## maintain master list of final moves
                moves.append(prop)

        # here, i have no more items in my proposal list, and everything converted to 
        # a list of unique moves
        
        # moves is a list of proposals, need to transform to api-compatible format
        
        plan = dict((p['src'],_prop_to_action(p)) for p in moves)
        
        return plan

    def count_enemy_neighbours_for_loc(self, **kwargs):
        return len(self.enemy_neighbours_for_loc(**kwargs))
            
    def count_peer_neighbours_for_loc(self, loc, own_id=None):
        if not own_id:
            own_id = self.player_id
        
        return len(self.adjacents(loc, only_id=own_id))

    def enemy_neighbours_for_loc(self, loc=None, own_id=None):
        if not loc:
            loc = self.location
        
        if not own_id:
            own_id = self.player_id
        
        neighbours = self.adjacents(loc, filter_empty=True, filter_id=own_id)
        
        ## lowest hitpoint first
        neighbours.sort(key = lambda x: self.robots[x]['hp'])
        
        #~ print "%s : %s enemy neighbours" % (loc, neighbours)
        
        return neighbours

        
class TestRobot(object):
    
    def test_reduce_list_of_dicts(self):
        
        a = [{'x':2},{'x':2},{'x':2}]
        _reduce_list_of_dicts(a, x=2)
        assert len(a) == 0, a

        a = [{'action': 'move', 'dst': (5, 15), 'prio': 60, 'src': (5, 16)},
             {'action': 'move', 'dst': (6, 16), 'prio': 60, 'src': (5, 16)},
             {'action': 'guard', 'dst': (5, 16), 'prio': 30, 'src': (5, 16)}]
             
        _reduce_list_of_dicts(a, dst=(5,15))
        assert len(a) == 2, a
             
        _reduce_list_of_dicts(a, src=(5,16))
        assert len(a) == 0, a
             
        a = [
            { 'x' : 1 },
            { 'x' : 2 },
            { 'x' : 3 },
        ]
        
        _reduce_list_of_dicts(a, x=2)
        assert a == [{'x': 1}, {'x': 3}]
        
        
    def test_preemptive_strike(self):
        robot = Robot()
        robot.robots = {
                (5,5): { 'location': (5, 5), 'hp': 50, 'player_id': 0,  },
                (5,7): { 'location': (5, 7), 'hp': 50, 'player_id': 1,  },
        }
        robot.player_id = 0
        robot.hp = 50
        
        print robot.find_preemptive_strike((5,5))
        
