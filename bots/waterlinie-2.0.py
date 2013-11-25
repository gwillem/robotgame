from __future__ import division
from collections import defaultdict
import math
import rg
import os
import time

"""
See waterlinie.md for strategy elaboration 
"""

DEBUG = True # os.getenv('USER') == 'willem'
LOCAL = os.getenv('USER') == 'willem'

SCORE = {
    'suicide' : 2000,
    'panic' : 1000,
    'attack_underwhelmed_enemy' : 500,
    'move_to_best_attack_spot' : 400,
    'preemptive_strike' : 200,
    'guard' : 50,
}

CENTER_POINT = (9,9)

def print_timing(func):
    def wrapper(*arg):
        t1 = time.time()
        res = func(*arg)
        t2 = time.time()
        print '%-15.15s %6d ms' % (func.func_name, int ( (t2-t1)*1000.0 ))
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
        dist = rg.dist(p.dst, CENTER_POINT)
        angle = center_angle(p.dst)
        return (-p.prio, dist, angle)
       
    def to_plan(self):
        return dict((p.src, p.to_action()) for p in self)
       
    def find_singles(self):
        """Return proposed moves for bots that have only a single proposal"""
        sources = [p.src for p in self]
        bots_with_single_prop = [ x[0] for x in unique_c(sources) if x[1] == 1]
        return [p for p in self if p.src in bots_with_single_prop]
       
    def add_move(self, *args):
        self.append(ProposedMove(*args))
        return self
       
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
    
    def is_spawn_imminent(self):
        return self.turn % 10 in [0,9]
    
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
    
    #~ @print_timing
    def act(self, game):
        
        self.robots   = game['robots']
        self.turn     = game['turn']
        self.enemy_id = other_player_id(self.player_id)
        
        self.act_sanity_check() # initializes history dicts

        if self.turn not in self.history_arena:
            """ Only do this for the first bot in a turn.
            They all share the same object, so skip redundant calculations """

            log( "********** turn %d *********" % game['turn'] )
            log ("player_id: %s, hp: %s, location: %s" % (self.player_id, self.hp, self.location,))
            log( "I received game data: %s" % game )

            self.history_arena[self.turn] = self.robots

            #self.vuln_enemies = self.find_vuln_enemies()
            self.enemy_next_moves = self.find_enemy_next_moves()
            self.best_attack_spots = self.find_best_attack_spots()
            
            self.enemies_assigned, self.ally_assignments = self.assign_enemies()
            
            log( "enemies assigned: %s" % self.enemies_assigned)
            log( "ally_assignments: %s" % self.ally_assignments)
            log( "best attack spots: %s" % self.best_attack_spots )
            
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

        log( "available for duty: %s" % available_for_duty )
        #~ log( "enemies: %s" % enemies )

        # search 1 and 2 wdist deep
        for wdist in [1, 2]:
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
            if len(soldiers) < 2:
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
        
    def find_neighbours(self, src=None, player_id=None, wdist=1):
        """ Give me non-empty adjacent squares for 'src' """
        src = src or self.location
        locs = self.ring_search(src,wdist=wdist)
            
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
            return [loc for loc in locs if loc not in self.robots]
            
        if only_id != None:
            return [loc for loc in locs if loc in self.robots and self.robots[loc]['player_id'] == only_id]
                    
        if filter_empty == True:
            locs = [loc for loc in locs if loc in self.robots]
            
        if filter_id != None:
            locs = [loc for loc in locs if loc not in self.robots \
                or self.robots[loc]['player_id'] != filter_id]
        
        return locs
        
    ## todo: fix me!
    def adjacents(self, location=None, wdist=1, **kwargs):
        if location == None:
            location = self.location
            
        if wdist == 1:
            locs = rg.locs_around(location, filter_out=('invalid', 'obstacle'))
        else:
            locs = locs_around(location, wdist=wdist)
        
        return self.filter_locs(locs, **kwargs)
                    
    def find_all_bots(self, player_id=None):
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
        
    def ring_search(self, src, wdist=1):
        """Give me all locations that are within wdist of src excluding src"""
        result = []
        for x in range(src[0]-wdist, src[0]+wdist+1):
            for y in range(src[1]-wdist, src[1]+wdist+1):
                xy = (x,y)
                if rg.loc_types(xy) in ['obstacle','invalid']:
                    continue
                if rg.wdist(src,xy) <= wdist:
                    result.append(xy)
                
        result.remove(src)
        return result
    
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
    
    def find_enemy_next_moves(self):
        """Return dict of moves that enemy /could/ move to next turn, 
        with the value == num of enemies that could move here 
        (increasing chance that it will happen)"""
        
        enemies = self.find_all_bots(player_id=self.enemy_id)
        moves = defaultdict(int)
        for e in enemies:
            for loc in self.adjacents(e):
                moves[loc] += 1
            
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
    
    def panic(self, src):
        log(" i am panicking!!" )
        
    
    def calculate_proposals_for_loc(self, src):
        """
        Given a src, calculate a ProposedMoveCollection with priorities
        """
        
        panic = False
        
        ## find possible moves
        proposals = ProposedMoveCollection()

        ## stand still is also valid
        proposals.add_move(SCORE['guard'], 'guard', src)
        
        nearby_enemies = self.find_neighbours(src=src, player_id=self.enemy_id)
        if len(nearby_enemies) >= 3: ## suicide?
            weak_enemies = [x for x in nearby_enemies if self.robots[x]['hp'] <= 15]
            they_might_kill_me = self.robots[src]['hp'] < 10
            if weak_enemies and they_might_kill_me:
                return proposal.add_move(SCORE['suicide'], 'suicide', src)
        
        
        if is_spawn(src) and self.is_spawn_imminent():
            panic = True
        
        if len(nearby_enemies) >= 2:
            panic = True
        
        if nearby_enemies:
            # yields (loc, num_allies_surrounded, hp) tuples
            overwhelmed_enemies = [(x,self.count_neighbours(src=x,player_id=self.enemy_id),self.robots[x]['hp']) \
                for x in nearby_enemies if self.count_neighbours(src=x,player_id=self.player_id) > 1]

            overwhelmed_enemies.sort(key=lambda x: (x[1], x[2]), reverse=True)
        
        if nearby_enemies and overwhelmed_enemies:
            proposals.add_move(SCORE['attack_underwhelmed_enemy'],'attack',src,overwhelmed_enemies[0][0])

        elif nearby_enemies:
            try:
                proposals.append(self.try_to_flee(src))
            except CannotFlee:
                ## todo! try forced_flee
                #~ print "%s : Can't flee, will attack weakest neighbour" % (src,)
                proposals.append(self.attack_weakest_neighbour(src))
                
        else: ## sort possible moves
            possibles = self.adjacents(src, filter_id=self.enemy_id)
            
            src_peer_neighbours = self.count_neighbours(src=src,player_id=self.player_id)
            src_center_distance = rg.dist(src, CENTER_POINT)
            
            
            for dst in possibles:
                
                #~ if src in self.ally_assignments:
#~ 
                    #~ src_target_distance = rg.wdist(src, self.ally_assignments[src])
                    #~ dst_target_distance = rg.wdist(dst, self.ally_assignments[src])
                                        #~ 
                    #~ ## prepare for swarm
                    #~ if dst in self.best_attack_spots and dst_target_distance < src_target_distance:
                        #~ score = SCORE['move_to_best_attack_spot'] + self.best_attack_spots[dst]
                        #~ proposals.add_move(score, 'move', src, dst)


                ## pre-emptive strike
                if dst in self.enemy_next_moves:
                    score = SCORE['preemptive_strike'] + self.enemy_next_moves[dst]
                    proposals.add_move(score, 'attack', src, dst)
                
                
                ## non-aggressive move logic commences
                score = 49
                
                dst_peer_neighbours = self.count_neighbours(src=dst,player_id=self.player_id) - 1 
                dst_center_distance = rg.dist(dst, CENTER_POINT)
                
                if is_spawn(dst) and not is_spawn(src):
                    #~ print "%s is not in %s" % (dst, rg.loc_types(dst) )
                    score -= 5
                    
                if is_spawn(src):
                    score += 5
                    
                if panic:
                    score += SCORE['panic']
                    
                if dst in self.enemy_next_moves:
                    score -= 100
                
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
        
class NoBotFound(Exception):
    pass

class CannotFlee(Exception):
    pass
