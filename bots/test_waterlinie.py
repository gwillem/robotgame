from __future__ import division
import ast # for the literal_eval in unittest
import unittest
import waterlinie as wl

class TestRobot(unittest.TestCase):

    @staticmethod
    def create_fake_game(allies,enemies,turn=10):
        
        robots = {}
        for x in allies:
            y = {'player_id': 0, 'hp': 50, 'location': x}
            robots[x] = y

        for x in enemies:
            y = {'player_id': 1, 'hp': 50, 'location': x}
            robots[x] = y

        return { 'turn' : turn, 'robots' : robots }
    
    def init_game(self, *args, **kwargs):
        game = self.create_fake_game(*args, **kwargs)
        self.robot.location = args[0][0] ## first friendly player
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
        r, g = self.init_game(a, e)
        rv = r.act(g)
        
        assert rv == ['move',(10,1)]
        
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
        
        pmc = wl.ProposedMoveCollection()
        
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
        
    def test_fill_empty_peer_spot(self):
        game = {'turn': 70, 'robots': {(6, 9): {'player_id': 1, 'robot_id': 15, 'hp': 50, 'location': (6, 9)}, (16, 8): {'player_id': 0, 'hp': 50, 'location': (16, 8)}, (10, 8): {'player_id': 1, 'robot_id': 17, 'hp': 30, 'location': (10, 8)}, (6, 6): {'player_id': 1, 'robot_id': 55, 'hp': 42, 'location': (6, 6)}, (2, 8): {'player_id': 0, 'hp': 50, 'location': (2, 8)}, (9, 8): {'player_id': 1, 'robot_id': 9, 'hp': 50, 'location': (9, 8)}, (4, 7): {'player_id': 1, 'robot_id': 47, 'hp': 30, 'location': (4, 7)}, (13, 5): {'player_id': 0, 'hp': 50, 'location': (13, 5)}, (15, 13): {'player_id': 0, 'hp': 50, 'location': (15, 13)}, (7, 16): {'player_id': 1, 'robot_id': 68, 'hp': 50, 'location': (7, 16)}, (10, 14): {'player_id': 0, 'hp': 41, 'location': (10, 14)}, (15, 5): {'player_id': 1, 'robot_id': 65, 'hp': 50, 'location': (15, 5)}, (10, 3): {'player_id': 0, 'hp': 33, 'location': (10, 3)}, (16, 7): {'player_id': 0, 'hp': 50, 'location': (16, 7)}, (6, 14): {'player_id': 0, 'hp': 50, 'location': (6, 14)}, (8, 14): {'player_id': 0, 'hp': 50, 'location': (8, 14)}, (4, 9): {'player_id': 0, 'hp': 50, 'location': (4, 9)}, (16, 10): {'player_id': 1, 'robot_id': 25, 'hp': 40, 'location': (16, 10)}, (2, 9): {'player_id': 0, 'hp': 50, 'location': (2, 9)}, (9, 15): {'player_id': 0, 'hp': 50, 'location': (9, 15)}, (10, 7): {'player_id': 1, 'robot_id': 6, 'hp': 50, 'location': (10, 7)}, (3, 10): {'player_id': 0, 'hp': 50, 'location': (3, 10)}, (4, 4): {'player_id': 0, 'hp': 25, 'location': (4, 4)}, (10, 12): {'player_id': 0, 'hp': 50, 'location': (10, 12)}, (8, 8): {'player_id': 1, 'robot_id': 39, 'hp': 32, 'location': (8, 8)}, (15, 11): {'player_id': 0, 'hp': 50, 'location': (15, 11)}, (3, 6): {'player_id': 1, 'robot_id': 57, 'hp': 50, 'location': (3, 6)}, (14, 14): {'player_id': 1, 'robot_id': 56, 'hp': 50, 'location': (14, 14)}, (8, 16): {'player_id': 1, 'robot_id': 35, 'hp': 40, 'location': (8, 16)}, (11, 2): {'player_id': 0, 'hp': 42, 'location': (11, 2)}, (9, 7): {'player_id': 1, 'robot_id': 59, 'hp': 20, 'location': (9, 7)}, (14, 10): {'player_id': 0, 'hp': 50, 'location': (14, 10)}, (12, 14): {'player_id': 1, 'robot_id': 45, 'hp': 32, 'location': (12, 14)}, (3, 13): {'player_id': 1, 'robot_id': 7, 'hp': 4, 'location': (3, 13)}, (8, 11): {'player_id': 1, 'robot_id': 16, 'hp': 50, 'location': (8, 11)}, (4, 14): {'player_id': 0, 'hp': 13, 'location': (4, 14)}, (5, 15): {'player_id': 0, 'hp': 50, 'location': (5, 15)}, (9, 6): {'player_id': 1, 'robot_id': 18, 'hp': 23, 'location': (9, 6)}, (7, 15): {'player_id': 1, 'robot_id': 29, 'hp': 22, 'location': (7, 15)}, (2, 7): {'player_id': 0, 'hp': 15, 'location': (2, 7)}, (10, 5): {'player_id': 1, 'robot_id': 26, 'hp': 33, 'location': (10, 5)}, (13, 3): {'player_id': 0, 'hp': 50, 'location': (13, 3)}, (4, 6): {'player_id': 1, 'robot_id': 69, 'hp': 35, 'location': (4, 6)}, (10, 10): {'player_id': 1, 'robot_id': 38, 'hp': 41, 'location': (10, 10)}, (9, 2): {'player_id': 1, 'robot_id': 36, 'hp': 22, 'location': (9, 2)}, (10, 16): {'player_id': 1, 'robot_id': 67, 'hp': 50, 'location': (10, 16)}, (11, 5): {'player_id': 1, 'robot_id': 8, 'hp': 13, 'location': (11, 5)}, (2, 11): {'player_id': 0, 'hp': 42, 'location': (2, 11)}, (11, 3): {'player_id': 0, 'hp': 50, 'location': (11, 3)}, (3, 8): {'player_id': 0, 'hp': 50, 'location': (3, 8)}, (14, 12): {'player_id': 0, 'hp': 50, 'location': (14, 12)}, (12, 4): {'player_id': 0, 'hp': 32, 'location': (12, 4)}, (15, 9): {'player_id': 0, 'hp': 50, 'location': (15, 9)}, (9, 1): {'player_id': 1, 'robot_id': 66, 'hp': 50, 'location': (9, 1)}, (11, 15): {'player_id': 1, 'robot_id': 27, 'hp': 42, 'location': (11, 15)}, (7, 8): {'player_id': 1, 'robot_id': 28, 'hp': 30, 'location': (7, 8)}, (5, 12): {'player_id': 0, 'hp': 50, 'location': (5, 12)}}}
        self.robot.location = (9,1)
        self.robot.player_id = 1
        self.robot.act(game)
        
        props = self.robot.calculate_proposals_for_loc((9,1))
        props.sort()
        
        assert props[0].action == 'move', props
        assert props[0].dst == (9,2), props
        
        #~ assert rv == ['move', (9,2)], rv
        
    def test_adjacents(self):
        a = [(9,9),(9,10),]
        e = [(9,8),]
        r, g = self.init_game(a,e)
        
        assert r.adjacents(location=(9,9)) \
            == [(9, 10), (10, 9), (9, 8), (8, 9)]

        assert r.adjacents(location=(9,9),filter_empty=True) \
            == [(9, 10), (9, 8),]

        assert r.adjacents(location=(9,9),only_id=1) \
            == [(9,8),]

        assert r.adjacents(location=(9,9),filter_id=0) \
            == [(10, 9), (9, 8), (8, 9)]

        assert r.adjacents(location=(9,9),only_empty=True) \
            == [(10, 9), (8, 9),]
        
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
        assert rv[0] != 'move', rv
        
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

        
    def test_find_enemy_next_moves(self):
        a = [(8,8),]
        e = [(9,9),]
        game = self.create_fake_game(a,e)
        self.robot.robots = game['robots']
        rv = sorted(self.robot.find_enemy_next_moves())
        assert rv == sorted(self.robot.adjacents((9,9))), rv        
    
    def test_find_all_bots(self):

        game = {'turn': 1, 'robots': {(13, 2): {'player_id': 1, 'hp': 50, 'location': (13, 2)}, (17, 7): {'player_id': 0, 'hp': 50, 'location': (17, 7)}, (12, 16): {'player_id': 0, 'hp': 50, 'location': (12, 16)}, (13, 16): {'player_id': 0, 'hp': 50, 'location': (13, 16)}, (1, 10): {'player_id': 1, 'hp': 50, 'location': (1, 10)}, (1, 8): {'player_id': 1, 'hp': 50, 'location': (1, 8)}, (8, 17): {'player_id': 0, 'hp': 50, 'location': (8, 17)}, (15, 4): {'player_id': 1, 'hp': 50, 'location': (15, 4)}, (14, 3): {'player_id': 1, 'hp': 50, 'location': (14, 3)}, (3, 14): {'player_id': 0, 'hp': 50, 'location': (3, 14)}}}
        self.robot.robots = game['robots']
        
        assert len(self.robot.find_all_bots(0)) == 5
        assert len(self.robot.find_all_bots(1)) == 5
        assert len(self.robot.find_all_bots(2)) == 0

    def test_ring_search(self):
        rv = self.robot.ring_search((9,9),wdist=2)
        assert len(rv) == 12, rv

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
