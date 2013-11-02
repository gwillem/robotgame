import imp
from RestrictedPython.Guards import safe_builtins
import random

class SecurityError:
    def __init__(self, player_id, message):
        self.player_id = player_id
        self.message = message

class PlayerCodeJail:
    allowed_imports = []
    allowed_magic = []

    def __init__(self, player_id, code):
        self.player_id = player_id

        suffix = str(random.randint(19319385, 1398513985))
        for s in PlayerCodeJail.allowed_magic:
            code = code.replace('__%s__' % s, s + suffix)

        if '__' in code:
            self.halt('not allowed to use \'__\' in your code')

        for s in PlayerCodeJail.allowed_magic:
            code = code.replace(s + suffix, '__%s__' % s)

        self.mod = imp.new_module('usercode%d' % id(self))
        self.mod.__dict__['__builtins__'] = safe_builtins
        self.mod.__dict__['__builtins__']['__import__'] = PlayerCodeJail.create_import_hook(self)
        self.mod.__dict__['__builtins__']['getattr'] = PlayerCodeJail.create_getattr_hook(self)
        exec code in self.mod.__dict__

    def halt(self, msg):
        raise SecurityError(self.player_id, msg)

    @staticmethod
    def create_import_hook(self):
        def import_hook(name, globals=None, locals=None, fromlist=None, level=-1):
            if name not in PlayerCodeJail.allowed_imports: 
                self.halt('not allowed to import %s' % name)
            return __import__(name, globals, locals, fromlist, level)
        return import_hook

    @staticmethod
    def create_getattr_hook(self):
        def getattr_hook(obj, key):
            if '__' in key:
                self.halt('not allowed to access a key containing \'__\'')
            return getattr(obj, key)
        return getattr_hook
