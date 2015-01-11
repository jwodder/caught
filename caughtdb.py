# -*- coding: utf-8 -*-
from   collections import namedtuple
import sqlite3

class CaughtDB(object):
    UNCAUGHT = 0
    CAUGHT   = 1
    OWNED    = 2

    def __init__(self, dbpath):
        self.db = sqlite3.connect(dbpath)
        self.db.text_factory = str
        self.db.execute('PRAGMA foreign_keys = ON')
        self.db.execute('PRAGMA encoding = "UTF-8"')  # Is this necessary?

    def __enter__(self): return self

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is None:
            self.db.commit()
        else:
            self.db.rollback()
        self.db.close()
        return False

    def getPokemon(self, name):
        """Returns the ``Pokemon`` object for the Pokémon with the given name,
           or ``None`` if there is no such Pokémon"""
        cursor = self.db.cursor()
        cursor.execute('SELECT dexno FROM pokemon_names WHERE name=?',
                       (name.lower(),))
        try:
            dexno, = cursor.fetchone()
        except TypeError:
            return None
        cursor.execute('SELECT name FROM pokemon WHERE dexno=?', (dexno,))
        name, = cursor.fetchone()
        return Pokemon(dexno, name, self.get_pokemon_names(dexno))

    def getGame(self, name):
        """Returns the ``Game`` object for the game with the given name, or
           ``None`` if there is no such game"""
        cursor = self.db.cursor()
        cursor.execute('SELECT gameID FROM game_names WHERE name=?',
                       (name.lower(),))
        try:
            gameID, = cursor.fetchone()
        except TypeError:
            return None
        cursor.execute('SELECT version, player_name, dexsize FROM games'
                       ' WHERE gameID=?', (gameID,))
        version, player_name, dexsize = cursor.fetchone()
        return Game(gameID, version, player_name, dexsize,
                    self.get_game_names(gameID))

    def getStatus(self, game, poke):
        cursor = self.db.cursor()
        cursor.execute('SELECT status FROM caught WHERE gameID=? AND dexno=?',
                       (int(game), int(poke)))
        try:
            status, = cursor.fetchone()
        except TypeError:
            return self.UNCAUGHT
        return status

    def setStatus(self, game, poke, status):
        if status == self.UNCAUGHT:
            self.db.execute('DELETE FROM caught WHERE gameID=? AND dexno=?',
                            (int(game), int(poke)))
        else:
            self.db.execute('INSERT OR REPLACE INTO caught (gameID, dexno,'
                            ' status) VALUES (?, ?, ?)', (int(game), int(poke),
                            status))

    def getGameCount(self, game):
        caught, = self.db.execute('SELECT count(*) FROM caught WHERE gameID = ?'
                                  ' AND status = ?', (int(game), self.CAUGHT))
        owned,  = self.db.execute('SELECT count(*) FROM caught WHERE gameID = ?'
                                  ' AND status = ?', (int(game), self.OWNED))
        return (caught, owned)

    def allGames(self):
        return [Game(*(row + (self.get_game_names(row[0]),)))
                for row in self.db.execute('SELECT gameID, version,'
                                           ' player_name, dexsize FROM games'
                                           ' ORDER BY gameID ASC')]

    def allPokémon(self, maxno=None):
        if maxno is None:
            results = self.db.execute('SELECT dexno, name FROM pokemon'
                                      ' ORDER BY dexno ASC')
        else:
            results = self.db.execute('SELECT dexno, name FROM pokemon '
                                      'WHERE dexno <= ? ORDER BY dexno ASC',
                                      (maxno,))
        return [Pokemon(dexno, name, self.get_pokemon_names(dexno))
                for dexno, name in results]

    def newGame(self, version, player_name, dexsize, altnames):
        cursor = self.db.cursor()
        cursor.execute('INSERT INTO games (version, player_name, dexsize)'
                       ' VALUES (?,?,?)', (version, player_name, int(dexsize)))
        gameID = cursor.lastrowid
        altnames = tuple(alt.lower() for alt in altnames)
        cursor.executemany('INSERT INTO game_names (gameID, name) VALUES (?,?)',
                           ((gameID, alt) for alt in altnames))
        specialName = None
        colonbase = version.lower() + ':' + player_name.lower()
        if not any(alt == colonbase or alt.startswith(colonbase + ':')
                   for alt in altnames):
            try:
                cursor.execute('INSERT INTO game_names (gameID, name) VALUES'
                               ' (?,?)', (gameID, colonbase))
            except Exception:
                escapebase = colonbase.replace('\\', r'\\') \
                                      .replace('%', r'\%') \
                                      .replace('_', r'\_')
                n = 1
                for name in cursor.execute('SELECT name FROM game_names'
                                           ' WHERE name LIKE ? ESCAPE ?',
                                           (escapebase + ':%', '\\')):
                    name = name[len(colonbase)+1:]
                    try:
                        m = int(name)
                    except ValueError:
                        pass
                    else:
                        n = max(n,m)
                colonbase += ':' + str(n+1)
                cursor.execute('INSERT INTO game_names (gameID, name) VALUES'
                               ' (?,?)', (gameID, colonbase))
        return (gameID, colonbase)

    def get_pokemon_names(self, dexno):  # internal function
        return list(self.db.execute('SELECT name FROM pokemon_names'
                                    ' WHERE dexno=? ORDER BY name ASC',
                                    (dexno,)))

    def get_game_names(self, gameID):  # internal function
        return list(self.db.execute('SELECT name FROM game_names'
                                    ' WHERE gameID=? ORDER BY name ASC',
                                    (gameID,)))


class Game(namedtuple('Game', 'gameID version player_name dexsize altnames')):
    __slots__ = ()
    def __int__(self): return self.gameID


class Pokemon(namedtuple('Pokemon', 'dexno name altnames')):
    __slots__ = ()
    def __int__(self): return self.dexno
