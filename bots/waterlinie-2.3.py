from __future__ import division
from collections import defaultdict
import math
import rg

"""
See waterlinie.md for strategy elaboration 
"""

DEBUG = True

SCORE = {
    'suicide' : 12800,
    'panic' : 6400,
    'attack_overwhelmed_enemy' : 3200,
    'move_to_best_attack_spot' : 1600,
    'move_to_safer_location' : 800,
    'attack_normal_enemy': 400,
    'preemptive_strike' : 200,
    'guard' : 100,
}

SPAWN_POINTS = ((7,1),(8,1),(9,1),(10,1),(11,1),(5,2),(6,2),(12,2),(13,2),(3,3),(4,3),(14,3),(15,3),(3,4),(15,4),(2,5),(16,5),(2,6),(16,6),(1,7),(17,7),(1,8),(17,8),(1,9),(17,9),(1,10),(17,10),(1,11),(17,11),(2,12),(16,12),(2,13),(16,13),(3,14),(15,14),(3,15),(4,15),(14,15),(15,15),(5,16),(6,16),(12,16),(13,16),(7,17),(8,17),(9,17),(10,17),(11,17))

CENTER_POINT = (9,9)

import time
def print_timing(func):
    def wrapper(*arg):
        t1 = time.time()
        res = func(*arg)
        t2 = time.time()
        delta =  int ( (t2-t1)*1000.0 )
        if delta > 0: print '%-15.15s %6d ms' % (func.func_name, delta)
        return res
    return wrapper

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
        """Sort based on priority, distance to center, angle to 
        center (deterministic)""" 
#        dist = rg.dist(p.dst, CENTER_POINT)
#        angle = center_angle(p.dst)
        return (-p.prio)
       
    def to_plan(self):
        return dict((p.src, p.to_action()) for p in self)
       
    def find_singles(self):
        """Return proposed moves for bots that have only a single proposal"""
        sources = [p.src for p in self]
        ## todo: should sort so that moves have higher priority to prevent collisions
        bots_with_single_prop = [ x[0] for x in unique_c(sources) if x[1] == 1]
        return [p for p in self if p.src in bots_with_single_prop]
       
    def add_move(self, *args):
        self.append(ProposedMove(*args))
        return self
       
    def add_prio(self, prio, src):
        """ Add prio upon altering list, so we can move up 
        conflicting positions higher in the prio list""" 
        
        for p in self:
            if p.src == src:
                p.prio += prio
        #~ self.sort()
    
    def sort(self, *args, **kwargs):
        return super(ProposedMoveCollection, self).sort(key=self._sort_proposals, *args, **kwargs)
        
    def __str__(self):
        self.sort()
        mystr = ""
        for i, item in enumerate(self):
            mystr += "%3d. %s\n" % (i, item)
        return mystr
            
    def eliminate(self, **kwargs):
        """ delete items for which ALL kwargs hold true 
        http://stackoverflow.com/questions/6022764/python-removing-list-element-while-iterating-over-list
        """
        for item in list(self):
            if all([getattr(item,k) == v for k, v in kwargs.items()]):
                self.remove(item)

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

def other_player_id(player_id):
    return 1 if player_id == 0 else 0

class Robot():
    
    #~ @print_timing
    def find_friends_nearby(self, src, wdist=3):
        pid = self.robots[src]['player_id']
        locs = self.ring_search(src, wdist=wdist, inclusive=True)
        
        print "Src:", src
        print locs
        locs.remove(src)
        friends = [x for x in locs if x in self.robots and self.robots[x]['player_id'] == pid]
        return friends
    
    def turns_to_spawn(self):
        return (10 - (self.turn % 10)) % 10
    
    def is_spawn_imminent(self, within=0):
        return self.turns_to_spawn() <= within
    
    #~ @print_timing
    def act_sanity_check(self):

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
    
    @print_timing
    def act(self, game):
        
        self.robots   = game['robots']
        self.turn     = game['turn']
        self.enemy_id = other_player_id(self.player_id)
        
        self.act_sanity_check() # initializes history dicts

        if self.turn not in self.history_plan:
            """ Only do this for the first bot in a turn.
            They all share the same object, so skip redundant calculations """

            #~ log( "********** turn %d *********" % game['turn'] )
            #~ log ("player_id: %s, hp: %s, location: %s" % (self.player_id, self.hp, self.location,))
            #~ log( "I received game data: %s" % game )

            self.history_arena[self.turn] = self.robots

            #self.vuln_enemies = self.find_vuln_enemies()
            self.enemy_next_moves = self.find_enemy_next_moves()
            self.best_attack_spots = self.find_best_attack_spots()
            
            self.enemies_assigned, self.ally_assignments = self.assign_enemies()
            
            #~ log( "enemies assigned: %s" % self.enemies_assigned)
            #~ log( "ally_assignments: %s" % self.ally_assignments)
            #~ log( "best attack spots: %s" % self.best_attack_spots )
            
            proposals = self.collect_all_proposals()
            #~ log( "proposals:\n%s" % proposals )
            
            plan = self.proposals_to_plan(proposals)
            #~ log( "plan: %s" % plan )
            self.history_plan[self.turn] = plan            

        plan = self.history_plan[self.turn]
        
        if self.location not in plan:
            print "Ouch! Fatal error! I couldn't find myself %s in the plan: %s and the game info was %s" % (self.location, plan, game)
            return ['guard']
            raise Exception("My plan calculation is flawed, as I couldn't find myself")
        
        return plan[self.location]
        
    def assign_enemies(self):
        """Create 2 dicts of assignments, one mapped by enemy, one by ally
        
        Yields:
        
        enemies_assigned = {
            enemy1 : [ ally1, ally2 ],
            etc
        }
        
        ally_assignments = {
            ally1 : enemyX
        }
        
        """
        enemies = self.find_vuln_enemies()
        available_for_duty = self.find_all_bots(player_id=self.player_id)
        
        enemies_assigned = defaultdict(list)

        #~ log( "available for duty: %s" % available_for_duty )
        #~ log( "enemies: %s" % enemies )

        # search 1 and 2 wdist deep
        for wdist in [1, 2, 3]:
            for enemy in enemies:
                ## whom of my trusty soldiers are nearby?
                for soldier in self.find_neighbours(src=enemy, player_id=self.player_id, wdist=wdist):
                    if soldier in available_for_duty:
                        #~ print "Stage %d: I'm assigning my bot %s to enemy %s" % (wdist, soldier, enemy)
                        enemies_assigned[enemy].append(soldier)
                        available_for_duty.remove(soldier)
        
        # then remove all enemies that are assigned less than 1 soldier
        # todo: optimization, these bots could be reassigned another enemy!
        
        for enemy, soldiers in enemies_assigned.items():
            if len(soldiers) < 3:
                del enemies_assigned[enemy]

        ## and build ally_assignments based on enemies_assigned
        ally_assignments = {}
        for enemy, soldiers in enemies_assigned.items():
            for soldier in soldiers:
                ally_assignments[soldier] = enemy
            
        return enemies_assigned, ally_assignments
        
    def is_static(self,src):
        """Has given bot moved in the last turn?
        Its a estimate, as there is no id of enemy bots, only location"""
                   
        if not hasattr(self,'turn'):
            return True
                   
        if not hasattr(self,'history_arena'):
            return True if self.turn > 1 else False
                   
        pid = self.history_arena[self.turn][src]['player_id']
        last_turn = self.turn - 1
    
        if last_turn not in self.history_arena:
            return True
            
        if src not in self.history_arena[last_turn]:
            return False
            
        if self.history_arena[last_turn][src]['player_id'] != pid:
            return False
                    
        return True
        
    def is_vulnerable(self, src):
        """Does this bot have at least 2 safe attack neighbours?
        and is it static?"""
        
        if not self.is_static(src):
            return False
        
        this_id = self.robots[src]['player_id']
        other_id = other_player_id(this_id)
        
        ## neighbours that are either empty or other player
        adj = self.adjacents(location=src, filter_id=this_id)
        
        ## are these neighbours safe attack points?
        adj = [x for x in adj if self.count_neighbours(src=x, player_id=this_id) <= 1]
        
        if len(adj) <= 1:
            return False
        
        return True
        
    def count_neighbours(self, **kwargs):
        return len(self.find_neighbours(**kwargs))
        
    def find_neighbours(self, src=None, player_id=None, wdist=1, inclusive=False):
        """ Give me non-empty adjacent squares for 'src' """
        src = src or self.location
        locs = self.ring_search(src,wdist=wdist, inclusive=inclusive)
            
        if player_id == None:
            neighbours = [loc for loc in locs if loc in self.robots]
        else:
            neighbours = [loc for loc in locs \
                if loc in self.robots \
                and self.robots[loc]['player_id'] == player_id]
    
        if neighbours:
            neighbours.sort(key = lambda x: self.robots[x]['hp'])
            
        return neighbours
              
    def filter_locs(self, locs, filter_id=None, filter_empty=False, only_empty=False, only_id=None):

        if only_empty == True:
            return set([loc for loc in locs if loc not in self.robots])
            
        if only_id != None:
            return set([loc for loc in locs if loc in self.robots and self.robots[loc]['player_id'] == only_id])
                    
        if filter_empty == True:
            locs = [loc for loc in locs if loc in self.robots]
            
        if filter_id != None:
            locs = [loc for loc in locs if loc not in self.robots \
                or self.robots[loc]['player_id'] != filter_id]
        
        return set(locs)
        
    ## todo: fix me!
    def adjacents(self, location=None, wdist=1, **kwargs):
        if location == None:
            location = self.location
            
        locs = self.ring_search(location, wdist=wdist, inclusive=False)
        return self.filter_locs(locs, **kwargs)
                    
    def find_all_bots(self, player_id=None):
        if player_id != None:
            return [loc for loc in self.robots if self.robots[loc]['player_id'] == player_id]
        else:
            return [loc for loc in self.robots]    
        
    #~ @print_timing
    def collect_all_proposals(self):
        """ Calculate proposed moves for all of my peers """
        proposals = ProposedMoveCollection()
        for peer in self.find_all_bots(self.player_id):
            proposals.extend(self.calculate_proposals_for_loc(peer))
        return proposals
        
    def ring_search(self, src, wdist=1, inclusive=False):
        """Give me all locations that are within wdist of src excluding src"""
        result = []
        try:
            for x in range(src[0]-wdist, src[0]+wdist+1):
                for y in range(src[1]-wdist, src[1]+wdist+1):
                    xy = (x,y)

                    if 'obstacle' in rg.loc_types(xy): continue
                    if 'invalid'  in rg.loc_types(xy): continue

                    if inclusive:
                        if rg.wdist(src,xy) <= wdist: result.append(xy)
                    if not inclusive:
                        if rg.wdist(src,xy) == wdist: result.append(xy)
        except TypeError, e:
            raise Exception("Typeerror %s, src = %s and wdist = %s" % (e,src,wdist))
        
        return set(result)
            
    def find_enemy_next_moves(self):
        """Return dict of moves that enemy /could/ move to next turn, 
        with the value == num of enemies that could move here 
        (increasing chance that it will happen)"""
        
        enemies = self.find_all_bots(player_id=self.enemy_id)
        moves = defaultdict(int)
        for e in enemies:
            for loc in self.adjacents(e):
                moves[loc] += 2
            
        ## also add spawn points if we are expecting spawn
        if self.turn % 10 == 0:
            for i in SPAWN_POINTS:
                moves[i] += 1
            
        return moves
    
    def find_best_attack_spots(self):
        hit_list = self.find_vuln_enemies()
        
        spots = []
        for enemy in hit_list:
            spots.extend(self.adjacents(location=enemy, filter_id=self.player_id))
            
        ## only those spots that have just 1 neighbouring enemy
        spots = [x for x in spots if self.count_neighbours(src=x, player_id=self.enemy_id) == 1]
            
        return dict((x,10) for x in spots)

    def find_vuln_enemies(self):
        """Scan arena for vuln enemies"""
        enemies = self.find_all_bots(player_id=self.enemy_id)      
        enemies = [x for x in enemies if self.is_vulnerable(x)]
                
        return enemies
    
    def find_safer_neighbours(self, src):
        can_move_here = self.adjacents(src, filter_id=self.enemy_id)
                
        safer = []
        spawn_imminent = self.is_spawn_imminent()
        
        src_enemies = self.count_neighbours(src=src, player_id=self.enemy_id)
        
        for dst in can_move_here:
            dst_enemies = self.count_neighbours(src=dst, player_id=self.enemy_id)

            if src_enemies <= dst_enemies:
                continue

            if spawn_imminent and is_spawn(dst):
                continue

            safer.append(dst)
            
        return set(safer)
    
    def calculate_proposals_for_loc(self, src):
        """
        Given a src, calculate a ProposedMoveCollection with priorities
        """
        
        panic = False
        aggressive = True if self.robots[src]['hp'] >= 30 else False

        proposals = ProposedMoveCollection()
        
        safer_neighbours = self.find_safer_neighbours(src)
        nearby_enemies = self.find_neighbours(src=src, player_id=self.enemy_id)        
        max_damage_to_me = 10 * len(nearby_enemies)      
        here_is_suicide = is_spawn(src) and self.is_spawn_imminent()
        i_will_be_killed = self.robots[src]['hp'] <= max_damage_to_me
        
        if nearby_enemies and not safer_neighbours and (i_will_be_killed or here_is_suicide):
            return proposals.add_move(SCORE['suicide'], 'suicide', src)
        
        if is_spawn(src) and self.is_spawn_imminent(within=1):
            panic = True
        
        # todo: should make an exception for overwhelmedness
        if len(nearby_enemies) >= 2:
            panic = True
            
        overwhelmed_enemies = [(x,self.count_neighbours(src=x,player_id=self.enemy_id),self.robots[x]['hp']) \
            for x in nearby_enemies if self.count_neighbours(src=x,player_id=self.player_id) > 1]
        
        for e in overwhelmed_enemies:
            score = SCORE['attack_overwhelmed_enemy'] + e[1]
            proposals.add_move(score, 'attack', src, e[0])

        for e in nearby_enemies:
            score = SCORE['attack_normal_enemy'] + 50 - self.robots[e]['hp']
            proposals.add_move(score, 'attack', src, e)
                          
        possibles = self.ring_search(src, inclusive=True)
        possibles = self.filter_locs(possibles, filter_id=self.enemy_id)
        
        src_ally_neighbours = self.count_neighbours(src=src,player_id=self.player_id)
        src_enemy_neighbours = self.count_neighbours(src=src,player_id=self.enemy_id)
        
        for dst in possibles:

            # pre emptive strike
            if dst in self.enemy_next_moves:
                score = SCORE['preemptive_strike'] + self.enemy_next_moves[dst]
                proposals.add_move(score, 'attack', src, dst)


            # only moving from here
            base_move_score = 0

            if dst in self.enemy_next_moves:
                base_move_score -= 20 * self.enemy_next_moves[dst]

            if aggressive and src in self.ally_assignments:
                src_target_distance = rg.wdist(src, self.ally_assignments[src])
                dst_target_distance = rg.wdist(dst, self.ally_assignments[src])
                                    
                ## prepare for swarm
                if dst in self.best_attack_spots:
                    base_move_score += SCORE['move_to_best_attack_spot']
                    
                base_move_score += 100 * (src_target_distance - dst_target_distance)
            
            # minus 1, so it will not count itself
            dst_enemy_neighbours = self.count_neighbours(src=dst,player_id=self.enemy_id) 
                            
            # slightly prefer not to move
            if src == dst:
                base_move_score += 10 
                            
            if is_spawn(src) and self.is_spawn_imminent(within=1):
                base_move_score += SCORE['move_to_safer_location']
                
            if is_spawn(dst):
                base_move_score -= 10
                
            if is_spawn(dst) and self.is_spawn_imminent():
                base_move_score -= SCORE['suicide']
                
            if panic and src != dst: 
                base_move_score += SCORE['panic']
                           
            #~ print "dst %s: enemey neighbours %s (old: %s)" % (dst, dst_enemy_neighbours, src_enemy_neighbours)
            if dst_enemy_neighbours < src_enemy_neighbours:
                base_move_score += SCORE['move_to_safer_location'] \
                    + dst_enemy_neighbours - src_enemy_neighbours

            action = 'guard' if dst == src else 'move'
            proposals.add_move(base_move_score, action, src, dst)
        
        return proposals
        
    #~ @print_timing
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

        #~ proposals.sort()
        moves = ProposedMoveCollection()
        
        while proposals:
            
            proposals.sort()
            
            ## 1. check if there are bots with one proposal only (bug: could be conflicts!)
            execute_proposals = proposals.find_singles()
            
            if not execute_proposals: ## if not, then just pick highest prio
                execute_proposals = [ proposals.pop(0) ]
                
            for p in execute_proposals:
                
                #~ print "I will execute: %s" % p
                
                proposals.eliminate(src=p.src)
                
                ## if moving, we should block this dst from happening again
                if p.action in ['move','guard']:
                    proposals.eliminate(src=p.dst, action='attack') ## somebody standing here, can't attack anymore
                    proposals.eliminate(dst=p.dst) ## remove everything to this cell
                    proposals.eliminate(dst=p.src, src=p.dst, action='move') ## prevent square swaps, akin to https://github.com/brandonhsiao/rgkit/blob/master/test/move_test.py#L58
                    
                    ## add prio to those sources that are now in conflict
                    proposals.add_prio(2000, p.dst)
                    
                    
                elif p.action == 'attack':
                    proposals.eliminate(dst=p.dst, action='move') ## prevent moves to this cell
                    proposals.eliminate(dst=p.src, action='move') 
                    proposals.eliminate(dst=p.src, action='attack') 
                    
                elif p.action == 'suicide': ## nothing, as this will free up the square
                    pass 
                    
                moves.append(p) ## maintain master list of final moves
                
                ## 

        # moves is a list of proposals, need to transform to api-compatible format
        return moves.to_plan()  
        
class NoBotFound(Exception):
    pass

class CannotFlee(Exception):
    pass
