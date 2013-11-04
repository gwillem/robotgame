from __future__ import division
import ast
import inspect
import random
import operator
import math
import threading
import Tkinter
import sys
import traceback
import copy
import time
import json
import zlib
import base64
###
import codejail
from robotexception import *

LANE_TOP, LANE_MID, LANE_BOT = range(3)

class AttrDict(dict):
    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self

class SettingsDict:
    def __init__(self, settings_file, map_file=None):
        self.d = AttrDict(ast.literal_eval(open('settings.py').read()))

settings = SettingsDict('settings.py').d
codejail.PlayerCodeJail.allowed_imports = settings.safe_imports
codejail.PlayerCodeJail.allowed_magic = settings.safe_magic

def load_map(map_file):
    global settingss

    map_data = ast.literal_eval(open(map_file).read())
    settings.spawn_coords = map_data['spawn']
    settings.obstacles = map_data['obstacle']

class DefaultRobot:
    def act(self, game):
        return ['guard']

class Player:
    def __init__(self, player_id, code):
        global settings

        self._mod = None
        self._player_id = player_id
        self._robot = None
        self._mod = codejail.PlayerCodeJail(player_id, code).mod

    def get_usercode_class(self, class_name, default):
        if hasattr(self._mod, class_name):
            if inspect.isclass(getattr(self._mod, class_name)):
                return getattr(self._mod, class_name)()
        return default()

    def get_robot(self):
        if self._robot is not None:
            return self._robot
        self._robot = self.get_usercode_class('Robot', DefaultRobot)
        return self._robot

class InternalRobot:
    def __init__(self, location, hp, player_id, field):
        self.location = location
        self.hp = hp
        self.player_id = player_id
        self.field = field
        
    @staticmethod
    def distance(p1, p2):
        return math.sqrt(pow(p2[0]-p1[0], 2) + pow(p2[1]-p1[1], 2))

    @staticmethod
    def parse_command(action):
        return (action[0], action[1:])

    def issue_command(self, action, actions):
        cmd, params = InternalRobot.parse_command(action)
        if cmd == 'move' or cmd == 'attack':
            getattr(self, 'call_' + cmd)(params[0], actions)
        if cmd == 'suicide':
            self.call_suicide(actions)

    @staticmethod
    def loc_in_board(loc):
        for i in range(2):
            if not (0 <= loc[i] < settings.board_size):
                return False
        return True

    def get_robots_around(self, loc):
        offsets = ((0, 0), (0, 1), (1, 0), (0, -1), (-1, 0))
        robots = []
        for offset in offsets:
            new_loc = tuple(map(operator.add, loc, offset))
            if InternalRobot.loc_in_board(new_loc):
                robots.append(self.field[new_loc])
        return [x for x in robots if x is not None]

    def movable_loc(self, loc):
        if loc is None:
            return False
        if InternalRobot.distance(loc, self.location) != 1:
            return False
        if loc in settings.obstacles:
            return False
        if not InternalRobot.loc_in_board(loc):
            return False
        return True

    def can_act(self, loc, action_table, no_raise=False, move_stack=None):
        global settings

        if move_stack is not None and self in move_stack:
            return self == move_stack[0]
        if not self.movable_loc(loc):
            return False

        moving = []

        nearby_robots = self.get_robots_around(loc)
        for robot in nearby_robots:
            if robot == self:
                continue

            cmd, params = InternalRobot.parse_command(action_table[robot])

            if cmd == 'suicide' and robot.location == loc:
                continue
            if cmd == 'guard' and robot.location == loc:
                if no_raise:
                    return False
                raise UnitGuardCollision(robot)
            if cmd == 'attack' and robot.location == loc:
                if no_raise:
                    return False
                raise UnitBlockCollision(robot)
            if cmd == 'move':
                if params[0] == loc:
                    moving.append(robot)
                elif robot.location == loc:
                    if move_stack is None:
                        move_stack = [self]
                    move_stack.append(robot)
                    if not robot.can_act(params[0], action_table, True, move_stack):
                        if no_raise:
                            return False
                        raise UnitBlockCollision(robot)
                            
        if len(moving) > 0:
            if no_raise:
                return False
            raise UnitMoveCollision(moving)
        return True

    def call_move(self, loc, action_table):
        global settings
        try:
            if self.can_act(loc, action_table):
                self.location = loc
        except UnitGuardCollision as e:
            if e.other_robot.player_id != self.player_id:
                self.hp -= settings.collision_damage
        except UnitMoveCollision as e:
            for robot in e.other_robots:
                if robot.player_id != self.player_id:
                    robot.hp -= settings.collision_damage
        except UnitBlockCollision as e:
            if e.other_robot.player_id != self.player_id:
                self.hp -= settings.collision_damage
                e.other_robot.hp -= settings.collision_damage
        except RobotException:
            pass

    def call_attack(self, loc, action_table, damage=None):
        if damage is None:
            damage = random.randint(*settings.attack_range)
        try:
            self.can_act(loc, action_table)
        except UnitGuardCollision as e:
            if e.other_robot.player_id != self.player_id:
                e.other_robot.hp -= int(damage / 2)
        except UnitMoveCollision as e:
            for robot in e.other_robots:
                if robot.player_id != self.player_id:
                    robot.hp -= damage
        except UnitBlockCollision as e:
            if e.other_robot.player_id != self.player_id:
                e.other_robot.hp -= int(damage)
        except RobotException:
            pass

    def call_suicide(self, action_table):
        self.hp = 0
        for loc in ((0, 1), (1, 0), (0, -1), (-1, 0)):
            new_loc = tuple(map(operator.add, loc, self.location))
            self.call_attack(new_loc, action_table, damage=settings.suicide_damage)

    @staticmethod
    def is_valid_action(action):
        global settings

        cmd, params = InternalRobot.parse_command(action)
        return cmd in settings.valid_commands

class Field:
    def __init__(self, size):
        self._field = [[None for x in range(size)] for y in range(size)]

    def __getitem__(self, point):
        return self._field[point[1]][point[0]]

    def __setitem__(self, point, v):
        self._field[point[1]][point[0]] = v

class TimeoutError: pass

def limit_execution_time(timeout, func, *args, **kwargs):
    def tracer(frame, event, arg, start=time.time()):
        now = time.time()
        if now > start + timeout:
            raise TimeoutError
        return tracer if event == "call" else None

    old_tracer = sys.gettrace()
    try:
        sys.settrace(tracer)
        return func(*args, **kwargs)
    finally:
        sys.settrace(old_tracer)

class Game:
    def __init__(self, player1, player2, record_turns=False):
        self._players = (player1, player2)
        self.turns = 0
        self._robots = []
        self._field = Field(settings.board_size)
        self._record = record_turns
        if self._record:
            self._field_storage = []

    def build_game_info(self):
        global settings

        return {
            'robots': dict((
                y.location,
                dict((x, getattr(y, x)) for x in settings.exposed_properties)
            ) for y in self._robots),
            'turn': self.turns,
        }

    def notify_new_turn(self):
        for player_id in range(2):
            user_robot = self._players[player_id].get_robot()

            if not hasattr(user_robot, 'on_new_turn'):
                continue
            if not inspect.ismethod(user_robot.on_new_turn):
                continue
            user_robot.on_new_turn()

    def make_robots_act(self):
        global settings

        game_info = self.build_game_info()
        actions = {}

        for robot in self._robots:
            user_robot = self._players[robot.player_id].get_robot()

            # copy properties
            for prop in settings.exposed_properties:
                setattr(user_robot, prop, getattr(robot, prop))

            # get next action
            try:
                next_action = limit_execution_time(settings.max_usercode_time/1000, user_robot.act, game_info)
                if not InternalRobot.is_valid_action(next_action):
                    raise Exception
            except Exception:
                print "The robot at (%s, %s) raised an exception:" % robot.location
                print '-'*60
                traceback.print_exc(file=sys.stdout)
                print '-'*60
                next_action = ['guard']

            actions[robot] = next_action

        for robot, action in actions.iteritems():
            old_loc = robot.location
            robot.issue_command(action, actions)
            if robot.location != old_loc:
                self._field[old_loc] = None
                self._field[robot.location] = robot

    def robot_at_loc(self, loc):
        robot = self._field[loc]
        #~ return robot.player_id if robot else None
        return robot

    def spawn_robot(self, player_id, loc):
        if self.robot_at_loc(loc) is not None:
            return False

        robot = InternalRobot(loc, settings.robot_hp, player_id, self._field)
        self._robots.append(robot)
        self._field[loc] = robot

    def spawn_robot_batch(self):
        global settings

        locs = random.sample(settings.spawn_coords, settings.spawn_per_player * 2)
        for player_id in range(2):
            for i in range(settings.spawn_per_player):
                self.spawn_robot(player_id, locs.pop())

    def clear_spawn_points(self):
        for loc in settings.spawn_coords:
            if self._field[loc] is not None:
                self._robots.remove(self._field[loc])
                self._field[loc] = None

    def remove_dead(self):
        to_remove = [x for x in self._robots if x.hp <= 0]
        for robot in to_remove:
            self._robots.remove(robot)
            self._field[robot.location] = None

    def make_field_record(self):
        record = [[], []]
        for x in range(settings.board_size):
            for y in range(settings.board_size):
                loc = (x, y)
                if self._field[loc] is not None:
                    record[self._field[loc].player_id].append('%d,%d' %loc)
        return '|'.join([' '.join(x) for x in record])

    def run_turn(self):
        global settings

        self.notify_new_turn()
        self.make_robots_act()
        self.remove_dead()

        if self.turns % settings.spawn_every == 0:
            self.clear_spawn_points()
            self.spawn_robot_batch()

        if self._record:
            self._field_storage.append(self.make_field_record())

        self.turns += 1

    def get_game_history(self):
        s = ';'.join(self._field_storage)
        return base64.b64encode(zlib.compress(s, 9))

    def get_scores(self):
        scores = [0, 0]
        for robot in self._robots:
            scores[robot.player_id] += 1
        return scores

class Render:
    def __init__(self, game, block_size=30):
        global settings

        self._blocksize = block_size
        self._winsize = block_size * settings.board_size + 40
        self._game = game
        self._colors = Field(settings.board_size)

        self._master = Tkinter.Tk()
        self._master.title('robot game')
        self._win = Tkinter.Canvas(self._master, width=self._winsize, height=self._winsize + self._blocksize * 7/4)
        self._win.pack()

        self.prepare_backdrop(self._win)
        self._label = self._win.create_text(self._blocksize/2, self._winsize + self._blocksize/2,
            anchor='nw', font='TkFixedFont', fill='white')

        self.callback()
        self._win.mainloop()

    def prepare_backdrop(self, win):
        global settings

        self._win.create_rectangle(0, 0, self._winsize, self._winsize + self._blocksize, fill='#555', width=0)
        self._win.create_rectangle(0, self._winsize, self._winsize, self._winsize + self._blocksize * 7/4, fill='#333', width=0)
        for x in range(settings.board_size):
            for y in range(settings.board_size):
                self._win.create_rectangle(
                    x * self._blocksize + 21, y * self._blocksize + 21,
                    x * self._blocksize + self._blocksize - 3 + 21, y * self._blocksize + self._blocksize - 3 + 21,
                    fill='black',
                    width=0)

    def draw_square(self, loc, color):
        if self._colors[loc] == color:
            return

        self._colors[loc] = color
        x, y = loc
        self._win.create_rectangle(x * self._blocksize + 20, y * self._blocksize + 20,
            x * self._blocksize + self._blocksize - 3 + 20, y * self._blocksize + self._blocksize - 3 + 20,
            fill=color, width=0)

    def update_title(self, turns, max_turns):
        red, green = self._game.get_scores()
        self._win.itemconfig(self._label,
            text='Red: %d | Green: %d | Turn: %d/%d' % (
                red, green, turns, max_turns))

    def callback(self):
        global settings

        self._game.run_turn()
        self.paint()
        self.update_title(self._game.turns, settings.max_turns)

        if self._game.turns < settings.max_turns:
            self._win.after(settings.turn_interval, self.callback)

    def determine_color(self, loc):
        global settings

        if loc in settings.obstacles:
            return '#222'
            
        robot = self._game.robot_at_loc(loc)
        if robot is None:
            return 'white'
            
        damage = robot.hp / 5
        colorhex = 5 + robot.hp / 5
        
        if robot.player_id == 0: # red
            return '#%X00' % colorhex
        else: # green
            return '#0%X0' % colorhex

    def paint(self):
        global settings

        for y in range(settings.board_size):
            for x in range(settings.board_size):
                loc = (x, y)
                self.draw_square(loc, self.determine_color(loc))
