import game
import sys
import codejail

def create_player(player_id, fname):
    return game.Player(player_id, open(fname).read())

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print 'usage: python run.py <usercode1.py> <usercode2.py> [<map file>]'
        sys.exit()

    try: 
        players = [create_player(i, x) for i, x in enumerate(sys.argv[1:3])]
        g = game.Game(*players)

        map_name = 'maps/default.py'
        if len(sys.argv) > 3:
            map_name = sys.argv[3]

        game.load_map(map_name)

        if '--render' in sys.argv:
            game.Render(g)
        else:
            for i in range(game.settings.max_turns):
                g.run_turn()
            print g.get_scores()

    except codejail.SecurityError as e:
        print 'security breach by player %d: %s' % (e.player_id, e.message)
