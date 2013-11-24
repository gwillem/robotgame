import rg

class Robot:
    def act(self, game):
        if game['turn'] % 10 in [0, 9]: #next, or next-next turn will spawn
            return ['move', rg.toward(self.location, rg.CENTER_POINT)]
        
        return ['guard']
        
