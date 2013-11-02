import math
import random 
import pprint

class Robot:
    def act(self, game):
        """
        Should return:
        
        ['move', (x, y)]
        ['attack', (x, y)]
        ['guard']
        ['suicide']
        
        """

        #~ pprint.pprint(game)
        #~ print game

        try:
            print "%8d Robo reporting in!" % self.robo_id
        except Exception as e:
            #~ self.robo_id = random.randint(0,100000)
            print e.message
        
        try:

            #~ print "I'm run! %s" % self
            print "My location is %s, %s" % (self.location)
            #~ return ['suicide']
        except Exception as e:
            print "Exception" + e.message

        return ['guard']
