from __future__ import division

"""

Essence of this bot:

1. Calculate all proposals for all peers => yield proposals
2. Sort proposals on priority and deterministic algo => yield plan
3. Execute plan for this.robot
4. Profit!

BUGS

* Flee: don't go to spawn point

* If a bot is locked AND at spawn point AND can't flee but also can't attack, then it 
  should run!

* self.adjacents is ugly

* If stuck at spawn, go to other spawn

"""

#from collections import Counter
from collections import defaultdict
import math
import sys
import time
import rg
import os

DEBUG=os.getenv('USER') == 'willem'

def log(msg):
    if DEBUG:
        return
        print msg

class ProposedMove(object):
    
    def __init__(self, prio, action, src, dst=None):
        if not dst:
            dst = src
            
        self.prio = prio
        self.action = action
        self.src = src
        self.dst = dst
        
    def __str__(self):
        return "%8s > %8s, %6s, (p:%3d)" % \
            (self.src, self.dst, self.action, self.prio)
        
    def to_action(self):
        action = [ self.action ]
        if self.action in ['move','attack']:
            action.append(self.dst)
        return action
        
class ProposedMoveCollection(list):
    
    def _sort_proposals(self, p):
        prio = 1 / p.prio if p.prio else 0
        dist = rg.dist(p.dst, rg.CENTER_POINT)
        angle = center_angle(p.dst)
    
        return (prio, dist, angle)
       
    def to_plan(self):
        return dict((p.src, p.to_action()) for p in self)
       
    def find_singles(self):
        """Return proposed moves for bots that have only a single proposal"""
        sources = [p.src for p in self]
        bots_with_single_prop = [ x[0] for x in unique_c(sources) if x[1] == 1]
#        bots_with_single_prop = [ x[0] for x in Counter( sources ).items() if x[1] == 1]
        
        return [p for p in self if p.src in bots_with_single_prop]
       
    def add_move(self, *args):
        self.append(ProposedMove(*args))
       
    def sort(self):
        return super(ProposedMoveCollection, self).sort(key=self._sort_proposals)
        
    def __str__(self):
        mystr = ""
        for i, item in enumerate(self):
            mystr += "%3d. %s\n" % (i, item)
            
        return mystr
            
        
    def eliminate(self, **kwargs):
        to_delete = []
    
        ## delete items for which ALL kwargs hold true
        
        for i, item in enumerate(self):
            ## do i need to delete this item?
            rowmatch = all([getattr(item,k) == v for k, v in kwargs.items()])
            if rowmatch:
                to_delete.append(i)

        ## slit into separate code, because its tricky to manipulate a 
        ## list and iterate it at the same time
        for i in sorted(to_delete, reverse=True):
            del self[i]

def is_spawn(loc):
    return 'spawn' in rg.loc_types(loc)

def center_angle(loc, center=None):
    if not center:
        center = rg.CENTER_POINT
    dx = loc[0] - center[0]
    dy = loc[1] - center[1]
    return math.atan2(dy, dx) 

def unique_c(mylist):
    c = defaultdict(int)
    for x in mylist:
        c[x] += 1
        
    return c

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

            log( "********** turn %d *********" % game['turn'] )

            self.history_arena[self.turn] = self.robots

            proposals = self.collect_all_proposals()
            
            log( "proposals:\n%s" % proposals )
            
            plan = self.proposals_to_plan(proposals)
        
            log( "plan: %s" % plan )
            
            self.history_plan[self.turn] = plan            

            #~ if hasattr(self,'breakpoint') and self.breakpoint:
                #~ raw_input("Press Enter to continue...")
                #~ self.breakpoint = False
            #~ else:
               #~ raw_input("Press Enter to continue...")


        plan = self.history_plan[self.turn]

        if self.location not in plan:
            print "Ouch! Fatal error! I couldn't find myself %s in the plan" % (self.location,)
            raise Exception("My plan calculation is flawed, as I couldn't find myself")
        
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

    def find_all_bots(self, player_id=None):
        
        if player_id:
            return [loc for loc in self.robots if self.robots[loc]['player_id'] == player_id]
        else:
            return [loc for loc in self.robots]    
        

    def collect_all_proposals(self):
        """ Calculate proposed moves for all of my peers """
        
        proposals = ProposedMoveCollection()
        
        for peer in self.find_all_bots(self.player_id):
            proposals.extend(self.calculate_proposals_for_loc(peer))
        
        return proposals
        
    
    def try_to_flee(self, src):
        locs = self.adjacents(src, only_empty=True)
        
        # find locs with least amount of enemy neighbours
        locs_safe = [loc for loc in locs if self.count_enemy_neighbours_for_loc(loc=loc) == 0 and not is_spawn(loc)]
        
        if locs_safe:
            return ProposedMove(100, 'move', src, locs_safe[0])
            
        # no safe locations.. should i run anyway?
        if is_spawn(src) and locs:
            return ProposedMove(90, 'move', src, locs[0])
            
        # there are no alternatives...
        raise CannotFlee("Can't flee! No safe locations")
        
    def attack_weakest_neighbour(self, src):
        enemies = self.enemy_neighbours_for_loc(loc=src) # already sorted on HP
        
        if not enemies:
            raise NoBotFound
            
        return ProposedMove(100, 'attack', src, enemies[0])
    
    def find_preemptive_strike(self, src):
        ## which neighbour has most enemy neighbours?
        neighbours = self.adjacents(src, only_empty=True)
        neighbours = [(n,self.count_enemy_neighbours_for_loc(loc=n)) for n in neighbours]
        neighbours.sort(key = lambda x: x[1], reverse=True)
        
        #~ print "%s : %s" % (src, neighbours)
        
        if neighbours and neighbours[0][1]: ## does the no 1 have enemy neighbours?
            return ProposedMove(100, 'attack', src, neighbours[0][0]) 
        else:
            return None
    
    def calculate_proposals_for_loc(self, src):
        ## find possible moves
        proposals = ProposedMoveCollection()

        ## stand still is also valid
        proposals.add_move(50, 'guard', src)
        
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
            except CannotFlee:
                #~ print "%s : Can't flee, will attack weakest neighbour" % (src,)
                proposals.append(self.attack_weakest_neighbour(src))
                
        elif preemptive_strike: ## todo: predict enemy movement based on previous steps
            #~ self.breakpoint = True
            proposals.append(preemptive_strike)
                    
        else: ## sort possible moves
            possibles = self.adjacents(src, only_empty=True)
            
            src_peer_neighbours = self.count_peer_neighbours_for_loc(src)
            src_center_distance = rg.dist(src, rg.CENTER_POINT)
            
            
            for dst in possibles:
                score = 49
                
                dst_peer_neighbours = self.count_peer_neighbours_for_loc(dst) - 1 
                dst_center_distance = rg.dist(dst, rg.CENTER_POINT)
                
                
                
                #~ print "%s has %d peer neighbours" % (dst, dst_peer_neighbours)
                
                if is_spawn(dst) and not is_spawn(src):
                    #~ print "%s is not in %s" % (dst, rg.loc_types(dst) )
                    score -= 5
                    
                if is_spawn(src):
                    score += 5
                
                if dst_peer_neighbours < src_peer_neighbours:
                    score += 2 * (9-dst_peer_neighbours) ## dont exceed 100
                    
                if dst_center_distance < src_center_distance:
                    score += 2
                
                if dst_center_distance > src_center_distance:
                    score -= 1

                proposals.add_move(score, 'move', src, dst)
        
        return proposals
        
    def proposals_to_plan(self, proposals):
        """ Sort proposals on priority and fill the projected map 
                
        While there are still items in proposals:
        
        1. Check if there are src bots with only 1 option (there is always one, ie 'guard')
           If yes, execute them and remove from proposals.
           
        2. Pop highest-prio item from proposals:
            a. Check if either source or destination hasn't been processed already (yes > skip)
            b. add to moves[] and new/old_field
        
        Input: proposals = ProposedMoveCollection
        
        Output: plan = {
            (x,y): ['guard'],
            (p,q): ['attack', (y,z)],
        }
        """

        proposals.sort()
        moves = ProposedMoveCollection()
        
        while proposals:
            
            ## 1. check if there are bots with one proposal only
            execute_proposals = proposals.find_singles()
            
            if not execute_proposals: ## if not, then just pick highest prio
                execute_proposals = [ proposals.pop(0) ]
                
            for p in execute_proposals:
                proposals.eliminate(src=p.src)
                proposals.eliminate(dst=p.dst)

                ## maintain master list of final moves
                moves.append(p)

        # moves is a list of proposals, need to transform to api-compatible format
        return moves.to_plan()

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
    
    def test_proposed_move_collection(self):
        
        pmc = ProposedMoveCollection()
        
        for i in range(3):
            pmc.add_move(100, 'move', (1,1), (i,i))
        assert len(pmc) == 3, pmc
        
        pmc.eliminate(dst=(1,1))
        assert len(pmc) == 2, pmc
        
        pmc.eliminate(action='move')
        assert len(pmc) == 0, pmc

class TestHelperFunctions(object):
    def test_unique_c(self):
        mylist = "a b a c b d e c a".split()
        rv = unique_c(mylist)
        assert rv['a'] == 3, rv
        assert rv['d'] == 1, rv

class NoBotFound(Exception):
    pass

class CannotFlee(Exception):
    pass
