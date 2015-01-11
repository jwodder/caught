#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import sys
from   caughtdb import CaughtDB, Game, Pokemon

dbfile = os.environ["HOME"] + '/share/caught.db'

def usage(): raise SystemExit("Usage: %s game Pokémon ..." % (sys.argv[0],))

def main():
    if len(sys.argv) < 3:
        usage()
    with CaughtDB(dbfile) as db:
        game = db.getGame(sys.argv[1])
        if game is None:
            raise SystemExit('%s: %s: unknown game' % tuple(sys.argv[:2]))
        for poke in sys.argv[2:]:
            pokedata = db.getPokemon(poke)
            if pokedata is None:
                raise SystemExit('%s: %s: unknown Pokémon'
                                 % (sys.argv[0], poke))
            db.setStatus(game, pokedata, CaughtDB.CAUGHT)

if __name__ == '__main__':
    main()
