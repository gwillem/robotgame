from __future__ import division

"""

Essence of this bot:

1. Calculate all proposals for all peers => yield proposals
2. Sort proposals on priority and deterministic algo => yield plan
3. Execute plan for this.robot
4. Profit!

TODO

* If enemy neighbour is surrounded by >1 ally, then attack. 

* If surrounded by enemies, flee to square with less enemies

* Only flee spawn point if turn % 10 == 0

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
import unittest

DEBUG=True # os.getenv('USER') == 'willem'

def log(msg):
    if DEBUG:
        print ">> %s" % msg

class ProposedMove(object):
    
    def __init__(self, prio, action, src, dst=None):
        if dst == None:
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
    if center == None:
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

        self.enemy_id = abs(self.player_id-1)

        if self.location not in self.robots:
            raise Exception("self.location %s is not in game['robots']: %s" %\
             (self.location, self.robots))

        if self.robots[self.location]['player_id'] != self.player_id:
            raise Exception("self.player_id (%s) doesn't match game['robots'][loc]['player_id'] (%s)" \
                % (self.player_id, self.robots[self.location]['player_id'] ) )
                
        if not hasattr(self, 'history_arena'):
            self.history_arena = {}

        if not hasattr(self, 'history_plan'):
            self.history_plan = {}

        if self.turn not in self.history_arena:
            """ Only do this for the first bot in a turn.
            They all share the same object, so skip redundant calculations """

            log( "********** turn %d *********" % game['turn'] )
            log ("player_id: %s, hp: %s, location: %s" % (self.player_id, self.hp, self.location,))
            log( "I received game data: %s" % game )

            self.history_arena[self.turn] = self.robots

            proposals = self.collect_all_proposals()
            log( "proposals:\n%s" % proposals )
            
            plan = self.proposals_to_plan(proposals)
            log( "plan: %s" % plan )
            
            self.history_plan[self.turn] = plan            

        plan = self.history_plan[self.turn]
        if self.location not in plan:
            print "Ouch! Fatal error! I couldn't find myself %s in the plan: %s" % (self.location, game)
            raise Exception("My plan calculation is flawed, as I couldn't find myself")
        
        return plan[self.location]
        
        
    def count_neighbours(self, **kwargs):
        return len(self.find_neighbours(**kwargs))
        
    def find_neighbours(self, src=None, player_id=None):
        """ Give me non-empty adjacent squares for 'src' """
        
        if src == None:
            src = self.location
            
        locs = rg.locs_around(src, filter_out=('invalid', 'obstacle'))
            
        if player_id == None:
            neighbours = [loc for loc in locs if loc in self.robots]
        else:
            neighbours = [loc for loc in locs \
                if loc in self.robots \
                and self.robots[loc]['player_id'] == player_id]
    
        if neighbours:
            neighbours.sort(key = lambda x: self.robots[x]['hp'])
            
        return neighbours
        
    ## todo: fix me!
    def adjacents(self, location=None, filter_id=None, filter_empty=False, only_empty=False, only_id=False):
        if location == None:
            location = self.location
            
        locs = rg.locs_around(location, filter_out=('invalid', 'obstacle'))
                    
        if only_empty != None:
            return [loc for loc in locs if loc not in self.robots]
            
        if only_id != None:
            return [loc for loc in locs if loc in self.robots and self.robots[loc]['player_id'] == only_id]
                    
        if filter_empty != None:
            locs = [loc for loc in locs if loc in self.robots]
            
        if filter_id != None:
            locs = [loc for loc in locs if loc not in self.robots \
                or self.robots[loc]['player_id'] != filter_id]
        
        return locs

    def find_all_bots(self, player_id=None):

        #~ print "player id is %s" % player_id
    
        if player_id != None:
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
        locs_safe = [loc for loc in locs \
            if self.count_neighbours(src=loc,player_id=self.enemy_id) == 0 \
            and not is_spawn(loc)]
        
        if locs_safe:
            return ProposedMove(100, 'move', src, locs_safe[0])
            
        # no safe locations.. should i run anyway?
        if is_spawn(src) and locs:
            return ProposedMove(90, 'move', src, locs[0])
            
        # there are no alternatives...
        raise CannotFlee("Can't flee! No safe locations")
        
    def attack_weakest_neighbour(self, src):
        enemies = self.find_neighbours(src=src,player_id=self.enemy_id) # already sorted on HP
        
        if not enemies:
            raise NoBotFound
            
        return ProposedMove(100, 'attack', src, enemies[0])
    
    def find_preemptive_strike(self, src):
        
        ## which neighbour has most enemy neighbours?
        neighbours = self.adjacents(src, only_empty=True)
        
        neighbours = [(n,self.count_neighbours(src=n,player_id=self.enemy_id)) for n in neighbours]
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
        
        now_surrounded = self.count_neighbours(src=src, player_id=self.enemy_id)
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
            
            src_peer_neighbours = self.count_neighbours(src=src,player_id=self.player_id)
            src_center_distance = rg.dist(src, rg.CENTER_POINT)
            
            
            for dst in possibles:
                score = 49
                
                dst_peer_neighbours = self.count_neighbours(src=dst,player_id=self.player_id) - 1 
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
                
                ## if moving, we should block this dst from happening again
                proposals.eliminate(dst=p.dst, action='move')

                ## maintain master list of final moves
                moves.append(p)

        # moves is a list of proposals, need to transform to api-compatible format
        return moves.to_plan()  
        
class TestRobot(unittest.TestCase):

    @staticmethod
    def create_fake_game(allies,enemies):
        
        robots = {}
        for x in allies:
            y = {'player_id': 0, 'hp': 50, 'location': x}
            robots[x] = y

        for x in enemies:
            y = {'player_id': 1, 'hp': 50, 'location': x}
            robots[x] = y

        return { 'turn' : 1, 'robots' : robots }
    
    def setUp(self):
        import game
        game.init_settings('maps/default.py')
        robot = Robot()
        robot.hp = 50
        robot.player_id = 0
        robot.enemy_id = 1
        robot.location = (3,4)
        self.robot = robot
    
    def test_attack_weakest_neighbour(self):
        a = [(9,9),]
        e = [(8,9),(10,9),]
        
        game = self.create_fake_game(a,e)
        game['robots'][(8,9)]['hp'] = 10
        
        self.robot.robots = game['robots']

      
        assert self.robot.attack_weakest_neighbour(src=(9,9)).dst == (8,9)
        
        game['robots'][(8,9)]['hp'] = 50
        game['robots'][(10,9)]['hp'] = 10

        assert self.robot.attack_weakest_neighbour(src=(9,9)).dst == (10,9)       
    
    def test_proposed_move_collection(self):
        
        pmc = ProposedMoveCollection()
        
        for i in range(3):
            pmc.add_move(100, 'move', (1,1), (i,i))
        assert len(pmc) == 3, pmc
        
        pmc.eliminate(dst=(1,1))
        assert len(pmc) == 2, pmc
        
        pmc.eliminate(action='move')
        assert len(pmc) == 0, pmc
        
    def test_act_guard(self):
              
        game = {'turn': 12, 'robots': {(15, 12): {'player_id': 1, 'hp': 50, 'location': (15, 12)}, (15, 13): {'player_id': 1, 'hp': 41, 'location': (15, 13)}, (13, 2): {'player_id': 0, 'hp': 50, 'location': (13, 2)}, (8, 2): {'player_id': 1, 'hp': 50, 'location': (8, 2)}, (12, 12): {'player_id': 1, 'hp': 50, 'location': (12, 12)}, (12, 6): {'player_id': 1, 'hp': 50, 'location': (12, 6)}, (12, 5): {'player_id': 1, 'hp': 50, 'location': (12, 5)}, (13, 7): {'player_id': 1, 'hp': 50, 'location': (13, 7)}, (7, 16): {'player_id': 0, 'hp': 50, 'location': (7, 16)}, (2, 12): {'player_id': 0, 'hp': 50, 'location': (2, 12)}, (3, 6): {'player_id': 1, 'hp': 50, 'location': (3, 6)}, (6, 12): {'player_id': 1, 'hp': 50, 'location': (6, 12)}, (15, 14): {'player_id': 0, 'hp': 50, 'location': (15, 14)}, (3, 4): {'player_id': 0, 'hp': 50, 'location': (3, 4)}, (4, 4): {'player_id': 1, 'hp': 50, 'location': (4, 4)}, (9, 17): {'player_id': 0, 'hp': 50, 'location': (9, 17)}}}
        
        rv = self.robot.act(game)
        assert rv == ['move',(3,5)], rv
        
    def test_find_neighbours(self):
        
        a = [(9,9),(9,8),(9,10),]
        e = [(8,9),]
        
        game = self.create_fake_game(a,e)
        self.robot.robots = game['robots']
        
        assert len(self.robot.find_neighbours(src=(9,9), player_id=0) ) == 2, \
            self.robot.find_neighbours(src=(9,9), player_id=0)
            
        assert len(self.robot.find_neighbours(src=(9,9), player_id=1) ) == 1, \
            self.robot.find_neighbours(src=(9,9), player_id=1)
        
    def test_count_find_neighbours(self):
        a = [(9,9),(9,8),(9,10),]
        e = [(8,9),]
        
        game = self.create_fake_game(a,e)
        self.robot.robots = game['robots']

        assert self.robot.count_neighbours(src=(9,9), player_id=0) == 2
        assert self.robot.count_neighbours(src=(9,9), player_id=1) == 1
        
    def test_find_all_bots(self):

        game = {'turn': 1, 'robots': {(13, 2): {'player_id': 1, 'hp': 50, 'location': (13, 2)}, (17, 7): {'player_id': 0, 'hp': 50, 'location': (17, 7)}, (12, 16): {'player_id': 0, 'hp': 50, 'location': (12, 16)}, (13, 16): {'player_id': 0, 'hp': 50, 'location': (13, 16)}, (1, 10): {'player_id': 1, 'hp': 50, 'location': (1, 10)}, (1, 8): {'player_id': 1, 'hp': 50, 'location': (1, 8)}, (8, 17): {'player_id': 0, 'hp': 50, 'location': (8, 17)}, (15, 4): {'player_id': 1, 'hp': 50, 'location': (15, 4)}, (14, 3): {'player_id': 1, 'hp': 50, 'location': (14, 3)}, (3, 14): {'player_id': 0, 'hp': 50, 'location': (3, 14)}}}
        #~ rv = robot.act(game)

        self.robot.robots = game['robots']
        
        #~ print self.robot.find_all_bots(0)
        
        assert len(self.robot.find_all_bots(0)) == 5
        assert len(self.robot.find_all_bots(1)) == 5
        assert len(self.robot.find_all_bots(2)) == 0

class TestHelperFunctions(unittest.TestCase):
    def test_unique_c(self):
        mylist = "a b a c b d e c a".split()
        rv = unique_c(mylist)
        assert rv['a'] == 3, rv
        assert rv['d'] == 1, rv

class NoBotFound(Exception):
    pass

class CannotFlee(Exception):
    pass
