import rg
import math

def prop_to_dict(prio, action, src, dst=None):
    if not dst:
        dst = src
    return {
        'prio': prio,
        'action': action,
        'src': src,
        'dst': dst
    }
    

class Robot():
        
    def act(self, game):
        self.robots = game['robots']
        self.turn   = game['turn']
        
        if not hasattr(self, 'history'):
            self.history = [None]

        self.history.append(self.robots)
            
        proposals = self.collect_all_proposals()
        plan = self.proposals_to_plan(proposals)
        
        return plan[self.location]
        
    def adjacents(self, location=None, filter_id=None, filter_empty=False):
        if not location:
            location = self.location
            
        locs = rg.locs_around(location, filter_out=('invalid', 'obstacle'))
                    
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
        print "I found %d peers" % len(peers)
        
        proposals = []
        for peer in peers:
            proposals.extend(self.calculate_proposals_for_loc(peer))
        
        return proposals
        
    def calculate_proposals_for_loc(self, src):
        ## find possible moves
        possibles = self.adjacents(src)
        proposals = []
        
        for dst in possibles:
            score = 50
            
            src_dist = rg.wdist(src, rg.CENTER_POINT)
            dst_dist = rg.wdist(dst, rg.CENTER_POINT)
            
            if dst_dist < src_dist:
                score += 10
            elif dst_dist == src_dist:
                score += 3
            else:
                score -= 5
                
            
            
            prop = prop_to_dict(score, 'move', loc, dst)
            proposals.append(prop)
        
        ## stand still is also valid
        proposals.append(prop_to_dict(30, 'guard', loc))
            
        
    def proposals_to_plan(self, proposals):
        """ Sort proposals on priority and fill the projected map 
        
        Need deterministic sort, so use these keys:
        1. priority
        2. distance to center
        3. radius to center (slope) 
        
        Output: plan = {
            (x,y): ['guard'],
            (p,q): ['attack', (y,z)],
        
        }
        """
