from __future__ import division
import ast # for the literal_eval in unittest
import unittest
import waterlinie as wl

class TestRobot(unittest.TestCase):

    @staticmethod
    def create_fake_game(allies=(9,9),enemies=(8,8),turn=5):
        
        bots = []
        bots.extend([(0,x) for x in allies])
        bots.extend([(1,x) for x in enemies])
        
        robots = {}
        for bot in bots:
            pid, bot = bot
            if len(bot) == 3:
                hp = bot[2]
                bot = tuple(bot[:2])
            else:
                hp = 50
                bot = tuple(bot)
            val = {'player_id': pid, 'hp': hp, 'location': bot}
            robots[bot] = val

        return { 'turn' : turn, 'robots' : robots }
    
    def init_game(self, *args, **kwargs):
        game = self.create_fake_game(*args, **kwargs)
        
        try:
            self.robot.location = tuple(args[0][0][:2]) ## first friendly player
        except IndexError, e:
            self.robot.location = (9,9)
            
        self.robot.turn = game['turn']
        self.robot.robots = game['robots']
        return self.robot, game
    
    def setUp(self):
        import game
        map_data = ast.literal_eval(open('maps/default.py').read())
        game.init_settings(map_data)
        
        robot = wl.Robot()
        robot.hp = 50
        robot.player_id = 0
        robot.enemy_id = 1
        robot.location = (3,4)
        robot.test_game = True
        
        self.robot = robot
        
    def test_act_panic(self):
        # a is blocked by e, and at spawn point. Panic!
        a = [ (11,1) ]
        e = [ (11,3) ]
        r, g = self.init_game(a, e, turn=9)
        rv = r.act(g)
        
        assert rv == ['move',(10,1)], rv
        
    def test_is_static(self):
       
        game = self.create_fake_game([],[(9,9)])
       
        self.robot.history_arena = {}

        game = self.create_fake_game([],[(9,9)])
        self.robot.history_arena[1] = game['robots']

        game = self.create_fake_game([],[(9,9)])
        self.robot.history_arena[2] = game['robots']
        self.robot.turn = 2        
        
        assert self.robot.is_static((9,9)) == True

        game = self.create_fake_game([],[(10,9)])
        self.robot.history_arena[3] = game['robots']
        self.robot.turn = 3
        
        assert self.robot.is_static((10,9)) == False
        
        
    def test_attack_if_we_are_more(self):
        
        a = [(9,9),(10,10)]
        e = [(10,9)]
    
        self.robot.location = (9,9)
        
        game = self.create_fake_game(a,e)
        
        rv = self.robot.act(self.create_fake_game(a,e))
        assert rv == ['attack',(10,9)], rv
        
    def test_flee_has_priority(self):
        a = [(3,14),(3,15),]
        e = [(4,15),]
        r, g = self.init_game(a,e,turn=9)
        rv = r.act(g)
        assert rv[0] == 'move', rv
        assert rv[1] != (3,14), rv
        
    def test_make_way_for_fleeing_instead_of_attack(self):
        a = [(2,9),(1,9),]
        e = [(2,11),]
        r, g = self.init_game(a,e, turn=10)
        rv = r.act(g)
        assert rv[0] != 'attack', rv

    def test_flee_has_priority_over_attack(self):
        a = [(1,9),(2,9),]
        e = [(2,11),]
        r, g = self.init_game(a,e, turn=9)
        rv = r.act(g)
        assert rv == ['move', (2,9)], rv
        
    def test_run_away(self):
        a = [(11,17),]
        e = [(10,17),]
        r, g = self.init_game(a,e)
        rv = r.act(g)
        assert rv == ['move',(11,16)], rv
        
    def test_suicide(self):
        # i am cornered by 2 enemies and have < 20 hp, do suicide!
        a = [(17,11),] # corner
        e = [(16,11), (17,10), ]
        r, g = self.init_game(a,e,turn=43)
        
        r.robots[(17,11)]['hp'] = 11
        r.robots[(17,10)]['hp'] = 35
        r.robots[(16,11)]['hp'] = 8

        rv = r.act(g)
        assert rv == ['suicide'], rv
        
    def test_move_to_safest_location(self):
        a = [(3,15),(4,15),] 
        e = [(4,14), (5,15), ]
        r, g = self.init_game(a,e,turn=5)
        rv = r.act(g)
        assert rv == ['move', (3,14)], rv
                
    def test_retreat(self):
        a = [(15,6),] 
        e = [(14,6),]
        r, g = self.init_game(a,e,turn=40)
        rv = r.act(g)
        assert rv == ['move', (15,7)], rv        
                
    def test_move_instead_of_suicide(self):
        a = [(10,13,10),] 
        e = [(10,14,18),]
        r, g = self.init_game(a,e,turn=66)

        rv = r.act(g)
        assert rv[0] == 'move', rv
        
    def test_attack_instead_of_suicide_when_im_still_healthy(self):        
        a = [(3,13),] # corner
        e = [(3,12), (4,13), ]
        r, g = self.init_game(a,e,turn=30)

        ## so attack when i still have enough hp
        r.robots[(3,13)]['hp'] = 32
        r.robots[(3,12)]['hp'] = 10
        rv = r.act(g)
        assert rv == ['attack', (3,12)], rv
        
        
    def test_suicide_when_only_spawn_remains(self):
        a = [(3,13),] # corner
        e = [(3,12), (4,13), ]
        r, g = self.init_game(a,e,turn=30)
        r.robots[(3,13)]['hp'] = 8
        r.robots[(3,12)]['hp'] = 10
        rv = r.act(g)
        assert rv == ['suicide'], rv 

    def test_proposed_move_collection(self):
        
        pmc = wl.ProposedMoveCollection()
        
        for i in range(3):
            pmc.add_move(100, 'move', (1,1), (i,i))
        assert len(pmc) == 3, pmc
        
        pmc.eliminate(dst=(1,1))
        assert len(pmc) == 2, pmc
        
        pmc.eliminate(action='move')
        assert len(pmc) == 0, pmc
                
    def test_find_neighbours(self):
        
        a = [(9,9),(9,8),(9,10),]
        e = [(8,9),]
        
        game = self.create_fake_game(a,e)
        self.robot.robots = game['robots']
        
        assert len(self.robot.find_neighbours(src=(9,9), player_id=0) ) == 2, \
            self.robot.find_neighbours(src=(9,9), player_id=0)
            
        assert len(self.robot.find_neighbours(src=(9,9), player_id=1) ) == 1, \
            self.robot.find_neighbours(src=(9,9), player_id=1)
            
    def test_is_vulnerable(self):

        a = [(8,8),(10,8),(8,10),(10,10),]
        e = [(9,9),(3,3),(3,4),(5,4)]

        """
        ---
        -x
        -x x
        
        and
        
        o o
         x
        o o
        """
        
        r,g = self.init_game(a,e)
        
        assert r.is_vulnerable((9,9)) == True
        assert r.is_vulnerable((3,3)) == False
        assert r.is_vulnerable((3,4)) == False
        assert r.is_vulnerable((5,4)) == True
        
        a = [(8,8),(8,9),(10,9),]
        e = [(9,9),]
        r,g = self.init_game(a,e)
        assert r.is_vulnerable((9,9))
        
    def test_is_vulnerable2(self):
        a = [(8,8),]
        e = [(9,9),]
        r, g = self.init_game(a,e)
        r.act(g)
        assert r.is_vulnerable((9,9)) 
        
        
        
    def test_find_best_attack_spots(self):
        a = [(8,8),(10,8),(8,10),(10,10),]
        e = [(9,9),]
        
        game = self.create_fake_game(a,e)
        
        self.robot.location = (8,8)
        game['turn'] = 10
        rv = self.robot.act(game)

        self.robot.location = (8,8)
        game['turn'] = 11
        rv = self.robot.act(game)
        
        locs = sorted(self.robot.find_best_attack_spots())
        
        assert len(locs) == 4, locs
        
    def test_find_vuln_enemies(self):
        a = [(8,8),(10,8),(8,10),(10,10),]
        e = [(9,9),(3,3),(3,4),(5,4)]
        game = self.create_fake_game(a,e)
        self.robot.robots = game['robots']
        
        vuln = sorted(self.robot.find_vuln_enemies())
        
        assert vuln== [(5,4),(9,9)], vuln
        
    def test_act_sane_surround(self):
        a = [(8,10),(9,11),(8,9),(9,9),]
        e = [(8,12),(9,13),]
        r, g = self.init_game(a,e)
        rv = r.act(g)
        assert rv == ['attack',(8,11)], rv
                
    def test_adjacents(self):
        a = [(9,9),(9,10),]
        e = [(9,8),]
        r, g = self.init_game(a,e)
        
        assert r.adjacents(location=(9,9)) \
            == set([(9, 10), (10, 9), (9, 8), (8, 9)])

        assert r.adjacents(location=(9,9),filter_empty=True) \
            == set([(9, 10), (9, 8),])

        assert r.adjacents(location=(9,9),only_id=1) \
            == set([(9,8),])

        assert r.adjacents(location=(9,9),filter_id=0) \
            == set([(10, 9), (9, 8), (8, 9)])

        assert r.adjacents(location=(9,9),only_empty=True) \
            == set([(10, 9), (8, 9),])
        
    def test_count_find_neighbours(self):
        a = [(9,9),(9,8),(9,10),]
        e = [(8,9),]
        
        game = self.create_fake_game(a,e)
        self.robot.robots = game['robots']

        assert self.robot.count_neighbours(src=(9,9), player_id=0) == 2
        assert self.robot.count_neighbours(src=(9,9), player_id=1) == 1
        
    def test_assign_enemies(self):
        a = [(8,8),(8,9),(10,9),]
        e = [(9,9),]
        game = self.create_fake_game(a,e)
        
        self.robot.location = (8,8)

        game['turn'] = 1
        self.robot.act(game)
        
        game['turn'] = 2
        self.robot.act(game)
        
        enemies_assigned, ally_assignments = self.robot.assign_enemies()
        
        assert (8,8) in enemies_assigned[(9,9)], enemies_assigned
        assert (10,9) in enemies_assigned[(9,9)], enemies_assigned
        assert ally_assignments[(8,8)] == (9,9), ally_assignments
        
    #~ def test_move_to_best_attack_spot(self):
        #~ a = [(8,8),(10,8)]
        #~ e = [(9,9),]
        #~ game = self.create_fake_game(a,e)
        #~ 
        #~ self.robot.location = (8,8)
        #~ game['turn'] = 10
        #~ rv = self.robot.act(game)
        #~ 
        #~ game['turn'] = 11
        #~ rv = self.robot.act(game)
#~ 
        #~ assert rv[0] == 'move', rv
        #~ assert rv[1] in [(8,9),(9,8)], rv
#~ 
        #~ self.robot.location = (10,8)
        #~ rv = self.robot.act(game)
        #~ assert rv[0] == 'move', rv
        #~ assert rv[1] in [(9,8),(10,9)], rv
        
    def test_act_dont_move_to_best_attack_spot_when_alone(self):
        a = [(8,8),]
        e = [(9,9),]
        r, g = self.init_game(a, e)
        rv = r.act(g)

        if rv[0] == 'move':
            assert rv[1] not in [(8,9),(9,8)]
        
    def test_escape_majority(self):
        a = [(6,16),(5,16),]
        e = [(6,15),(7,16),]
        r, g = self.init_game(a, e)
        
        g['robots'][(7,16)]['hp'] = 40
        
        rv = r.act(g)
        assert rv == ['move',(5,16)], rv
        
    def test_act_dont_collide(self):
        a = [(6,6),(5,7),(7,7),(7,8),]
        e = []
        r, g = self.init_game(a, e)
        rv1 = r.act(g)

        a = [(5,7),(6,6),(7,7),(7,8),]
        e = []
        r, g = self.init_game(a, e)
        rv2 = r.act(g)
        
        print rv1
        print rv2
        
        try:
            assert rv1[1] != rv2[1], (rv1, rv2) ## same dst
        except IndexError:
            pass

    def test_find_friends_nearby(self):
        a = [(11,1),(13,14),(13,13),(13,11)]
        e = [(1,1),]
        r, g = self.init_game(a, e)

        rv = r.find_friends_nearby((11,1))
        assert rv == [], rv
        
        rv = r.find_friends_nearby((13,13))
        assert len(rv) == 2, rv
        
        

        
    def test_is_spawn_imminent(self):
        r, g = self.init_game([(9,9)],[(10,10)],turn=7)
        
        assert r.is_spawn_imminent(within=0) == False
        assert r.is_spawn_imminent(within=1) == False
        assert r.is_spawn_imminent(within=2) == False
        assert r.is_spawn_imminent(within=3) == True
        assert r.is_spawn_imminent(within=4) == True
        
        
    def test_find_enemy_next_moves(self):
        a = [(8,8),]
        e = [(9,9),]
        r, g = self.init_game(a, e, turn=3)
        r.act(g)
        
        rv = sorted(self.robot.find_enemy_next_moves())
        assert rv == sorted(self.robot.adjacents((9,9))), rv        
    
    def test_find_all_bots(self):

        game = {'turn': 1, 'robots': {(13, 2): {'player_id': 1, 'hp': 50, 'location': (13, 2)}, (17, 7): {'player_id': 0, 'hp': 50, 'location': (17, 7)}, (12, 16): {'player_id': 0, 'hp': 50, 'location': (12, 16)}, (13, 16): {'player_id': 0, 'hp': 50, 'location': (13, 16)}, (1, 10): {'player_id': 1, 'hp': 50, 'location': (1, 10)}, (1, 8): {'player_id': 1, 'hp': 50, 'location': (1, 8)}, (8, 17): {'player_id': 0, 'hp': 50, 'location': (8, 17)}, (15, 4): {'player_id': 1, 'hp': 50, 'location': (15, 4)}, (14, 3): {'player_id': 1, 'hp': 50, 'location': (14, 3)}, (3, 14): {'player_id': 0, 'hp': 50, 'location': (3, 14)}}}
        self.robot.robots = game['robots']
        
        assert len(self.robot.find_all_bots(0)) == 5
        assert len(self.robot.find_all_bots(1)) == 5
        assert len(self.robot.find_all_bots(2)) == 0

    def test_ring_search(self):
        rv = self.robot.ring_search((9,9), wdist=2, inclusive=True)
        assert len(rv) == 13, rv

        rv = self.robot.ring_search((9,9), wdist=2, inclusive=False)
        assert len(rv) == 8, rv

        rv = self.robot.ring_search((9,9), wdist=1, inclusive=True)
        assert len(rv) == 5, rv

        rv = self.robot.ring_search((9,9), wdist=1, inclusive=False)
        assert len(rv) == 4, rv
        
        rv = self.robot.ring_search((11,1), wdist=1, inclusive=False)
        assert len(rv) == 2, rv

class TestProposedMoveCollection(unittest.TestCase):
    def setUp(self):
        import game
        map_data = ast.literal_eval(open('maps/default.py').read())
        game.init_settings(map_data)
    
    def test_pmc_sort(self):
        pmc = wl.ProposedMoveCollection()
        x = (9,9)
        y = (10,9)
        
        pmc.add_move(100,'bla',x,y)
        pmc.add_move(200,'bla',x,y)
        pmc.add_move(50,'bla',x,y)
        pmc.add_move(-40,'bla',x,y)
        
        pmc.sort()
        assert pmc[0].prio == 200, pmc

class TestHelperFunctions(unittest.TestCase):
    def test_unique_c(self):
        mylist = "a b a c b d e c a".split()
        rv = wl.unique_c(mylist)
        assert rv['a'] == 3, rv
        assert rv['d'] == 1, rv
