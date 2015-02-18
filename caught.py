#!/usr/bin/python
# -*- coding: utf-8 -*-
import argparse
import csv
import heapq
import os
import sys
import caughtdb
from   caughtdb import CaughtDB, Game, Pokemon

### TODO: Make this non-Unix friendly:
default_dbfile = os.environ.get("HOME", ".") + '/.caughtdb'

### TODO: Improve these:
statusLabels = {CaughtDB.UNCAUGHT: '  ',
                CaughtDB.CAUGHT:   '✓ ',
                CaughtDB.OWNED:    '✓✓'}

statuses = {"uncaught": set([CaughtDB.UNCAUGHT]),
            "caught":   set([CaughtDB.CAUGHT]),
            "caught+":  set([CaughtDB.CAUGHT, CaughtDB.OWNED]),
            "owned":    set([CaughtDB.OWNED]),
            "unowned":  set([CaughtDB.UNCAUGHT, CaughtDB.CAUGHT])}

POKEMON_NAME_LEN = 12

def listPokemon(db, args, warn_on_fail=False):
    for fp in args.file:
        with fp:
            for line in fp:
                line = line.strip()
                if line == '' or line[0] == '#':
                    continue
                pokedata = getPokemon(db, args, line, warn_on_fail)
                if pokedata is not None:
                    yield pokedata
    for poke in args.pokemon:
        pokedata = getPokemon(db, args, poke, warn_on_fail)
        if pokedata is not None:
            yield pokedata

def getPokemon(db, args, poke, warn_on_fail=False):
    try:
        pokedata = db.getPokemon(poke)
    except caughtdb.NoSuchPokemonError as e:
        if warn_on_fail:
            sys.stderr.write(sys.argv[0] + ': ' + str(e) + "\n")
            return None
        else:
            raise e
    else:
        return pokedata

def getGame(db, args, game, warn_on_fail=False):
    try:
        if game.isdigit() and not args.force_gname:
            gamedata = db.getGameByID(int(game))
        else:
            gamedata = db.getGame(game)
    except caughtdb.NoSuchGameError as e:
        if warn_on_fail:
            sys.stderr.write(sys.argv[0] + ': ' + str(e) + "\n")
            return None
        else:
            raise e
    else:
        return gamedata

def GameCSV(arg):
    ### TODO: Expand/customize (and add appropriate error handling?)
    return next(csv.reader([arg]))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-D', '--dbfile', default=default_dbfile)
    parser.add_argument('-G', dest='force_gname', action='store_true')

    subparser = parser.add_subparsers(title='command', dest='cmd')

    subparser_create = subparser.add_parser('create')
    subparser_create.add_argument('pokedex')

    subparser_new = subparser.add_parser('new')
    subparser_new.add_argument('-i', '--ignore-dups', action='store_true')
    subparser_new.add_argument('-q', '--quiet', action='store_true')
    subparser_new.add_argument('--version')
    subparser_new.add_argument('--player-name', '--player')
    subparser_new.add_argument('name')
    subparser_new.add_argument('dexsize', type=int)
    subparser_new.add_argument('synonyms', nargs='*')

    subparser_delete = subparser.add_parser('delete')
    subparser_delete.add_argument('-f', '--force', action='store_true')
    subparser_delete.add_argument('games', nargs='+')

    for name in ('add', 'own', 'release', 'uncatch'):
        sp = subparser.add_parser(name)
        sp.add_argument('-F', '--file', action='append', default=[],
                        type=argparse.FileType('r'))
        sp.add_argument('game')
        sp.add_argument('pokemon', nargs='*')

    subparser_get = subparser.add_parser('get')
    subparser_get.add_argument('-F', '--file', action='append', default=[],
                               type=argparse.FileType('r'))
    subparser_get.add_argument('game')
    subparser_get.add_argument('pokemon', nargs='*')

    subparser_getall = subparser.add_parser('getall')
    subparser_getall.add_argument('--games', type=GameCSV)
    subparser_getall.add_argument('-F', '--file', action='append', default=[],
                                  type=argparse.FileType('r'))
    subparser_getall.add_argument('pokemon', nargs='*')

    subparser_list = subparser.add_parser('list')
    subparser_list.add_argument('status')
    subparser_list.add_argument('game')

    subparser_games = subparser.add_parser('games')
    subparser_games.add_argument('-J', '--json', action='store_true')
    subparser_games.add_argument('-s', '--stats', action='store_true')
    subparser_games.add_argument('games', nargs='*')

    args = parser.parse_args()

    try:
        with CaughtDB(args.dbfile) as db:

            if args.cmd == 'create':
                db.create(args.pokedex)

            elif args.cmd == 'new':
                gameID = db.newGame(args.name, args.version, args.player_name,
                                    args.dexsize, args.synonyms,
                                    ignore_dups=args.ignore_dups)
                if not args.quiet:
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
                for pokedata in listPokemon(db, args):
                    db.markCaught(game, pokedata)

            elif args.cmd == 'own':
                game = getGame(db, args, args.game)
                for pokedata in listPokemon(db, args):
                    db.markOwned(game, pokedata)

            elif args.cmd == 'release':
                game = getGame(db, args, args.game)
                for pokedata in listPokemon(db, args):
                    db.markRelease(game, pokedata)

            elif args.cmd == 'uncatch':
                game = getGame(db, args, args.game)
                for pokedata in listPokemon(db, args):
                    db.markUncaught(game, pokedata)

            elif args.cmd == 'get':
                game = getGame(db, args, args.game)
                if args.file or args.pokemon:
                    pokemon = listPokemon(db, args, warn_on_fail=True)
                else:
                    pokemon = db.allPokemon(maxno=game.dexsize)
                for pokedata in pokemon:
                    status = db.getStatus(game, pokedata)
                    print '%s %3d. %s' % (statusLabels[status], pokedata.dexno,
                                          pokedata.name)

            elif args.cmd == 'getall':
                if args.games:
                    games = [getGame(db, args, g) for g in args.games]
                else:
                    games = db.allGames()
                ### TODO: vv
                print ' ' * (POKEMON_NAME_LEN+5) + '|' + '|'.join(g.name
                                                                  for g in games)
                if args.file or args.pokemon:
                    pokemon = listPokemon(db, args, warn_on_fail=True)
                else:
                    pokemon = db.allPokemon(maxno=max(g.dexsize for g in games))
                for pokedata in pokemon:
                    sys.stdout.write('%3d. %-*s' % (pokedata.dexno,
                                                    POKEMON_NAME_LEN,
                                                    pokedata.name))
                    for g in games:
                        status = db.getStatus(g, pokedata)
                        ### TODO: vv
                        sys.stdout.write('|' + statusLabels[status]
                                             + ' ' * (len(g.name)-2))
                    print

            elif args.cmd == 'list':
                game = getGame(db, args, args.game)
                toList = set()
                for status in args.status.split('/'):
                    status = status.strip().lower()
                    if status in statuses:
                        toList |= statuses[status]
                    else:
                        raise SystemExit(sys.argv[0] + ': ' + status
                                                     + ': invalid status')
                pokemon = []
                for status in toList:
                    pokemon = heapq.merge(pokemon,
                                          db.getByStatus(game, status,
                                                         game.dexsize))
                for poke in pokemon:
                    print str(poke)

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
                if args.json:
                    jsonses = []
                    for game in games:
                        jsonses.append(game.asJSON(*gameArgs(game)))
                    print '[' + ', '.join(jsonses) + ']'
                else:
                    for game in games:
                        print game.asYAML(*gameArgs(game))

    except caughtdb.CaughtDBError as e:
        raise SystemExit(sys.argv[0] + ': ' + str(e))


if __name__ == '__main__':
    main()
