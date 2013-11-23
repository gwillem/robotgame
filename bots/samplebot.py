import rg
import ast
import game as rgkit_game
import unittest

class Robot:
    def act(self, game):
        # if we're in the center, stay put
        if self.location == rg.CENTER_POINT:
            return ['guard']

        # if there are enemies around, attack them
        for loc, bot in game['robots'].items():
            if bot['player_id'] != self.player_id:
                if rg.dist(loc, self.location) <= 1:
                    return ['attack', loc]

        # move toward the center
        return ['move', rg.toward(self.location, rg.CENTER_POINT)]
        
class TestRobot(unittest.TestCase):

    @staticmethod
    def create_fake_game(allies,enemies,turn=1):
        
        robots = {}
        for x in allies:
            y = {'player_id': 0, 'hp': 50, 'location': x}
            robots[x] = y

        for x in enemies:
            y = {'player_id': 1, 'hp': 50, 'location': x}
            robots[x] = y

        return { 'turn' : turn, 'robots' : robots }

    def setUp(self):
        map_data = ast.literal_eval(open('maps/default.py').read())
        rgkit_game.init_settings(map_data)
        
        robot = Robot()
        robot.hp = 50
        robot.player_id = 0
        robot.enemy_id = 1
        
        self.robot = robot
        
    def test_act_move_to_center(self):
              
        allies = [(8,9)]
        enemies = [(3,3)]              
        testgame = self.create_fake_game(allies,enemies)

        self.robot.location = (8,9)
               
        rv = self.robot.act(testgame)
        assert rv == ['move',(9,9)], rv
        
