#!/usr/bin/python
# -*- coding: utf-8 -*-
import argparse
import os
import sys
from   caughtdb import CaughtDB, Game, Pokemon

default_dbfile = os.environ["HOME"] + '/.caughtdb'

def getGame(db, args, game):
    if game.isdigit() and not args.force_gname:
        return db.getGameById(int(game))
    else:
        return db.getGame(game)

parser = argparse.ArgumentParser
parser.add_argument('-D', '--dbfile', default=default_dbfile)
parser.add_argument('-G', dest='force_gname', action='store_true')

subparser = parser.add_subparsers('command', dest='cmd')

subparser_new = subparser.add_parser('new')
subparser_new.add_argument('version')
subparser_new.add_argument('playername')
subparser_new.add_argument('dexsize', type=int)
subparser_new.add_argument('altnames', nargs='*')

for name in ('add', 'own', 'release', 'uncatch'):
    sp = subparser.add_parser(name)
    sp.add_argument('game')
    sp.add_argument('pokemon', nargs='+')
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
except Exception as e:
    raise SystemExit(sys.argv[0] + ': ' + str(e))
