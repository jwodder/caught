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
	return Pokemon(dexno, name, self.get_pokemon_names(dexno))

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
	cursor.execute('SELECT version, player_name, dexsize FROM games'
		       ' WHERE gameID=?', gameID)
	version, player_name, dexsize = cursor.fetchone()
	return Game(gameID, version, player_name, dexsize,
		    self.get_game_names(gameID))

    def getStatus(self, game, poke):
	cursor = self.db.cursor()
	cursor.execute('SELECT status FROM caught WHERE gameID=? AND dexno=?',
		       int(game), int(poke))
	try:
	    status, = cursor.fetchone()
	except TypeError:
	    return self.UNCAUGHT
	return status

    def setStatus(self, game, poke, status):
	if status == self.UNCAUGHT:
	    self.db.execute('DELETE FROM caught WHERE gameID=? AND dexno=?',
			    int(game), int(poke))
	else:
	    self.db.execute('INSERT OR REPLACE INTO caught (gameID, dexno,'
			    ' status) VALUES (?, ?, ?)', int(game), int(poke),
			    status)

    def getGameCount(self, game):
	caught, = self.db.execute('SELECT count(*) FROM caught WHERE gameID = ?'
				  ' AND status = ?', int(game), self.CAUGHT)
	owned,  = self.db.execute('SELECT count(*) FROM caught WHERE gameID = ?'
				  ' AND status = ?', int(game), self.OWNED)
	return (caught, owned)

    def allGames(self):
	for row in self.db.execute('SELECT gameID, version, player_name,'
				   ' dexsize FROM games ORDER BY gameID ASC'):
	    yield Game(*(row + (self.get_game_names(row[0]),)))

    def allPokémon(self, maxno=None):
        if maxno is None:
	    results = self.db.execute('SELECT dexno, name FROM pokemon'
				      ' ORDER BY dexno ASC')
	else:
	    results = self.db.execute('SELECT dexno, name FROM pokemon '
				      'WHERE dexno <= ? ORDER BY dexno ASC',
				      maxno)
	for dexno, name in results:
	    yield Pokemon(dexno, name, self.get_pokemon_names(dexno))

    def get_pokemon_names(self, dexno):  # internal function
	return list(self.db.execute('SELECT name FROM pokemon_names'
				    ' WHERE dexno=? ORDER BY name ASC', dexno))

    def get_game_names(self, gameID):  # internal function
	return list(self.db.execute('SELECT name FROM game_names'
				    ' WHERE gameID=? ORDER BY name ASC',
				    gameID))

    def newGame(self, version, player_name, dexsize, altnames)

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
