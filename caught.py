#!/usr/bin/python
# -*- coding: utf-8 -*-
import argparse
import os
import sys
import caughtdb
from   caughtdb import CaughtDB, Game, Pokemon

default_dbfile = os.environ["HOME"] + '/.caughtdb'

### TODO: Improve these:
statusLabels = {CaughtDB.UNCAUGHT: '  ',
                CaughtDB.CAUGHT:   '✓ ',
                CaughtDB.OWNED:    '✓✓'}

def getGame(db, args, game, warn_on_fail=False):
    try:
        if game.isdigit() and not args.force_gname:
            gamedata = db.getGameByID(int(game))
        else:
            gamedata = db.getGame(game)
    except caughtdb.NoSuchGameError as e:
        if warn_on_fail:
            ### Should this use the `warnings` module?
            sys.stderr.write(sys.argv[0] + ': ' + str(e) + "\n")
            return None
        else:
            raise e
    else:
        return gamedata

parser = argparse.ArgumentParser()
parser.add_argument('-D', '--dbfile', default=default_dbfile)
parser.add_argument('-G', dest='force_gname', action='store_true')

subparser = parser.add_subparsers(title='command', dest='cmd')

subparser_new = subparser.add_parser('new')
subparser_new.add_argument('version')
subparser_new.add_argument('playername')
subparser_new.add_argument('dexsize', type=int)
subparser_new.add_argument('synonyms', nargs='*')

subparser_delete = subparser.add_parser('delete')
subparser_delete.add_argument('-f', dest='force', action='store_true')
subparser_delete.add_argument('games', nargs='+')

for name in ('add', 'own', 'release', 'uncatch'):
    sp = subparser.add_parser(name)
    sp.add_argument('game')
    sp.add_argument('pokemon', nargs='+')

subparser_get = subparser.add_parser('get')
subparser_get.add_argument('game')
subparser_get.add_argument('pokemon', nargs='*')

subparser_games = subparser.add_parser('games')
subparser_games.add_argument('-J', dest='as_json', action='store_true')
subparser_games.add_argument('-s', dest='stats', action='store_true')
subparser_games.add_argument('games', nargs='*')

args = parser.parse_args()

try:
    with CaughtDB(args.dbfile) as db:

        if args.cmd == 'new':
            gameID = db.newGame(args.version, args.playername, args.dexsize,
                                args.synonyms)
            print gameID.asYAML()

        elif args.cmd == 'delete':
            for g in args.games:
                game = getGame(db, args, g, warn_on_fail=True)
                if game is None:
                    continue
                yesdel = args.force
                while not yesdel:
                    response = raw_input('Really delete ' + g + '? (y/n) ')\
                                        .strip().lower()
                    if response in ('y', 'yes'):
                        yesdel = True
                    elif response in ('n', 'no'):
                        yesdel = False
                        break
                    else:
                        print 'Invalid response.'
                if yesdel:
                    db.deleteGame(game)

        elif args.cmd == 'add':
            game = getGame(db, args, args.game)
            for poke in args.pokemon:
                pokedata = db.getPokemon(poke)
                db.markCaught(game, pokedata)

        elif args.cmd == 'own':
            game = getGame(db, args, args.game)
            for poke in args.pokemon:
                pokedata = db.getPokemon(poke)
                db.markOwned(game, pokedata)

        elif args.cmd == 'release':
            game = getGame(db, args, args.game)
            for poke in args.pokemon:
                pokedata = db.getPokemon(poke)
                db.markRelease(game, pokedata)

        elif args.cmd == 'uncatch':
            game = getGame(db, args, args.game)
            for poke in args.pokemon:
                pokedata = db.getPokemon(poke)
                db.markUncaught(game, pokedata)

        elif args.cmd == 'get':
            game = getGame(db, args, args.game)
            if args.pokemon:
                for poke in args.pokemon:
                    try:
                        pokedata = db.getPokemon(poke)
                    except caughtdb.NoSuchPokemonError as e:
                        ### Should this use the `warnings` module?
                        sys.stderr.write(sys.argv[0] + ': ' + str(e) + "\n")
                    else:
                        status = db.getStatus(game, pokedata)
                        print '%s %3d. %s' % (statusLabels[status],
                                              pokedata.dexno, pokedata.name)
            else:
                for pokedata in db.allPokemon(maxno=game.dexsize):
                    status = db.getStatus(game, pokedata)
                    print '%s %3d. %s' % (statusLabels[status], pokedata.dexno,
                                          pokedata.name)

        elif args.cmd == 'games':
            if args.stats:
                def gameArgs(game):
                    caught, owned = db.getGameCount(game)
                    return (caught+owned, owned)
            else:
                gameArgs = lambda _: ()
            if args.games:
                games = filter(None, [getGame(db, args, g, warn_on_fail=True)
                                      for g in args.games])
            else:
                games = db.allGames()
            if args.as_json:
                jsonses = []
                for game in games:
                    jsonses.append(game.asJSON(*gameArgs(game)))
                print '[' + ', '.join(jsonses) + ']'
            else:
                for game in games:
                    print game.asYAML(*gameArgs(game))

except caughtdb.CaughtDBError as e:
    raise SystemExit(sys.argv[0] + ': ' + str(e))
