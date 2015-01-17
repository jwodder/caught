#!/usr/bin/python
# -*- coding: utf-8 -*-
import argparse
import os
import sys
import caughtdb
from   caughtdb import CaughtDB, Game, Pokemon

default_dbfile = os.environ["HOME"] + '/.caughtdb'

# TODO: Improve these
statusLabels = {CaughtDB.UNCAUGHT: '  ',
                CaughtDB.CAUGHT:   '✓ ',
                CaughtDB.OWNED:    '✓✓'}

def getGame(db, args, game):
    if game.isdigit() and not args.force_gname:
        return db.getGameById(int(game))
    else:
        return db.getGame(game)

parser = argparse.ArgumentParser()
parser.add_argument('-D', '--dbfile', default=default_dbfile)
parser.add_argument('-G', dest='force_gname', action='store_true')

subparser = parser.add_subparsers(title='command', dest='cmd')

subparser_new = subparser.add_parser('new')
subparser_new.add_argument('version')
subparser_new.add_argument('playername')
subparser_new.add_argument('dexsize', type=int)
subparser_new.add_argument('altnames', nargs='*')

for name in ('add', 'own', 'release', 'uncatch'):
    sp = subparser.add_parser(name)
    sp.add_argument('game')
    sp.add_argument('pokemon', nargs='+')

subparser_get = subparser.add_parser('get')
subparser_get.add_argument('game')
subparser_get.add_argument('pokemon', nargs='*')

args = parser.parse_args()
try:
    with CaughtDB(args.dbfile) as db:

        if args.cmd == 'new':
            gameID, _ = db.newGame(args.version, args.playername, args.dexsize,
                                   args.altnames)
            print gameID

        elif args.cmd == 'add':
            game = getGame(db, args, args.game)
            for poke in args.pokemon:
                pokedata = db.getPokemon(poke)
                db.markCaught(game, pokedata)

        elif args.cmd == 'get':
            game = getGame(db, args, args.game)
            if args.pokemon:
                for poke in args.pokemon:
                    try:
                        pokedata = db.getPokemon(poke)
                    except caughtdb.NoSuchPokemonError as e:
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

except caughtdb.CaughtDBError as e:
    raise SystemExit(sys.argv[0] + ': ' + str(e))
