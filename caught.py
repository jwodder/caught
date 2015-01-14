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

def main():
    parser = argparse.ArgumentParser
    parser.add_argument('-D', '--dbfile', default=default_dbfile)
    parser.add_argument('-G', dest='force_gname', action='store_true')
    subparser = parser.add_subparsers('command', dest='cmd')
    for name in ('add', 'own', 'release', 'uncatch'):
        sp = subparser.add_parser(name)
        sp.add_argument('game')
        sp.add_argument('pokemon', nargs='+')
    args = parser.parse_args()
    try:
        with CaughtDB(args.dbfile) as db:
            if args.cmd == 'add':
                game = getGame(db, args, args.game)
                for poke in args.pokemon:
                    pokedata = db.getPokemon(poke)
                    db.markCaught(game, pokedata)
    except Exception as e:
        #raise SystemExit(sys.argv[0] + ': ' + sys.exc_info()[1])
        raise SystemExit(sys.argv[0] + ': ' + str(e))

if __name__ == '__main__':
    main()
