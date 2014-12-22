#!/usr/bin/python
# -*- coding: utf-8 -*-
from   collections import namedtuple
import os
import sqlite3
import sys

dbfile = os.environ["HOME"] + 'share/caught.db'

class CaughtDB(object):
### TODO: Give this with_statement methods that call db.commit() on success and
### db.rollback() on error

    UNCAUGHT = 0
    CAUGHT   = 1
    OWNED    = 2

    def __init__(self, dbpath):
	self.db = sqlite3.connect(dbpath)
	self.db.text_factory = str

    def getPokemon(self, name):
	"""Returns the ``Pokemon`` object for the Pokémon with the given name,
	   or ``None`` if there is no such Pokémon"""
	cursor = self.db.cursor()
	cursor.execute('SELECT dexno FROM pokemon_names WHERE name=?',
		       name.lower())
	try:
	    dexno, = cursor.fetchone()
	except TypeError:
	    return None
	cursor.execute('SELECT name FROM pokemon WHERE dexno=?', dexno)
	name, = cursor.fetchone()
	altnames = list(cursor.execute('SELECT name FROM pokemon_names WHERE dexno=? ORDER BY name ASC', dexno))
	return Pokemon(dexno, name, altnames)

    def getGame(self, name):
	"""Returns the ``Game`` object for the game with the given name, or
	   ``None`` if there is no such game"""
	cursor = self.db.cursor()
	cursor.execute('SELECT gameID FROM game_names WHERE name=?',
		       name.lower())
	try:
	    gameID, = cursor.fetchone()
	except TypeError:
	    return None
	cursor.execute('SELECT version, player_name, dexsize FROM games WHERE gameID=?', gameID)
	version, player_name, dexsize = cursor.fetchone()
	altnames = list(cursor.execute('SELECT name FROM game_names WHERE gameID=? ORDER BY name ASC', gameID))
	return Game(gameID, version, player_name, dexsize, altnames)

    def getStatus(self, game, poke):
	cursor = self.db.cursor()
	cursor.execute('SELECT status FROM caught WHERE gameID=? AND dexno=?',
		       int(game), int(poke))
	try:
	    status, = cursor.fetchone()
	except TypeError:
	    return self.UNCAUGHT
	return status

    def setStatus(self, game, poke, status)  # returns a boolean for whether there was a change?

    def newGame(self, name, dexsize, altnames)
    def getGameCount(self, game)  # returns number of Pokémon caught & owned (and dexsize?)

    def allGames(self)
    def allPokémon(self, maxno=None)

    # method for getting a list of all Pokémon for a given game
    # method for getting a range/set of Pokémon for a given game?


class Game(namedtuple('Game', 'gameID version player_name dexsize altnames')):
    __slots__ = ()
    def __int__(self): return self.gameID


class Pokemon(namedtuple('Pokemon', 'dexno name altnames')):
    __slots__ = ()
    def __int__(self): return self.dexno


def usage():
    sys.stderr.write("Usage: %s game Pokémon ...\n" % (sys.argv[0],))
    sys.exit(2)

def main():
    if len(sys.argv) < 3:
	usage()
    db = CaughtDB(dbfile)
    game = db.getGame(sys.argv[1])
    if game is None:
	sys.stderr.write('%s: %s: unknown game\n' % (sys.argv[0], sys.argv[1]))
	sys.exit(2)
    for poke in sys.argv[2:]:
	pokedata = db.getPokemon(poke)
	if pokedata is None:
	    sys.stderr.write('%s: %s: unknown Pokémon\n' % (sys.argv[0], poke))
	    sys.exit(2)
	db.setStatus(game, pokedata, CaughtDB.CAUGHT)

if __name__ == '__main__':
    main()
