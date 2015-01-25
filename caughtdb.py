# -*- coding: utf-8 -*-
from   collections import namedtuple
import sqlite3

class CaughtDB(object):
    UNCAUGHT = 0
    CAUGHT   = 1
    OWNED    = 2

    SCHEMA = '''
CREATE TABLE pokemon (dexno INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                      name  TEXT    NOT NULL UNIQUE);

CREATE TABLE pokemon_names (dexno INTEGER NOT NULL REFERENCES pokemon(dexno),
                            name  TEXT    NOT NULL UNIQUE,
                            CHECK (name = lower(name)));

CREATE TABLE games (gameID      INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                    version     TEXT    NOT NULL,
                    player_name TEXT    NOT NULL,
                    dexsize     INTEGER NOT NULL);

CREATE TABLE game_names (gameID INTEGER NOT NULL REFERENCES games(gameID),
                         name   TEXT    NOT NULL UNIQUE,
                         CHECK (name = lower(name)));

CREATE TABLE caught (gameID INTEGER NOT NULL REFERENCES games(gameID),
                     dexno  INTEGER NOT NULL REFERENCES pokemon(dexno),
                     status INTEGER NOT NULL,
                     PRIMARY KEY (gameID, dexno));
'''

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

    def commit(self):
        self.db.commit()

    def rollback(self):
        self.db.rollback()

    def close(self):
        self.db.close()

    def create(self, pokedex):
        self.db.executescript(self.SCHEMA)
        with open(pokedex) as dex:
            for (lineno, line) in enumerate(dex, start=1):
                line = line.strip()
                if line == '' or line[0] == '#':
                    continue
                fields = line.split('\t')
                if len(fields) < 2:
                    raise MalformedFileError(pokedex, lineno, 'too few fields')
                try:
                    dexno = int(fields[0])
                except ValueError:
                    raise MalformedFileError(pokedex, lineno,
                                             fields[0] + ': not a number')
                self.db.execute('INSERT OR ROLLBACK INTO pokemon (dexno, name)'
                                ' VALUES (?,?)', (dexno, fields[1]))
                self.db.executemany('INSERT OR ROLLBACK INTO pokemon_names'
                                    ' (dexno, name) VALUES (?,?)',
                                    ((dexno, name.lower()) for name in fields))

    def getPokemon(self, name):
        """Returns the ``Pokemon`` object for the Pokémon with the given name.
           Raises a `NoSuchPokemonError`` if there is no such Pokémon."""
        cursor = self.db.cursor()
        cursor.execute('SELECT dexno FROM pokemon_names WHERE name=?',
                       (name.lower(),))
        try:
            dexno, = cursor.fetchone()
        except TypeError:
            raise NoSuchPokemonError(name)
        cursor.execute('SELECT name FROM pokemon WHERE dexno=?', (dexno,))
        name, = cursor.fetchone()
        return Pokemon(dexno, name, self.get_pokemon_names(dexno))

    def getGame(self, name):
        """Returns the ``Game`` object for the game with the given name.
           Raises a ``NoSuchGameError`` if there is no such game."""
        cursor = self.db.cursor()
        cursor.execute('SELECT gameID FROM game_names WHERE name=?',
                       (name.lower(),))
        try:
            gameID, = cursor.fetchone()
        except TypeError:
            raise NoSuchGameError(name)
        return self.getGameByID(gameID)

    def getGameByID(self, gameID):
        gameID = int(gameID)
        cursor = self.db.cursor()
        cursor.execute('SELECT version, player_name, dexsize FROM games'
                       ' WHERE gameID=?', (gameID,))
        try:
            version, player_name, dexsize = cursor.fetchone()
        except TypeError:
            raise NoSuchGameError(gameID=gameID)
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

    def markCaught(self, game, poke):  # uncaught → caught
        if self.getStatus(game, poke) == self.UNCAUGHT:
            self.db.execute('INSERT OR REPLACE INTO caught (gameID, dexno,'
                            ' status) VALUES (?, ?, ?)', (int(game), int(poke),
                            self.CAUGHT))

    def markOwned(self, game, poke):  # * → owned
        self.db.execute('INSERT OR REPLACE INTO caught (gameID, dexno, status)'
                        ' VALUES (?, ?, ?)', (int(game), int(poke), self.OWNED))

    def markReleased(self, game, poke):  # owned → caught
        self.db.execute('UPDATE caught SET status=? WHERE gameID=? AND dexno=?'
                        ' AND status=?', (self.CAUGHT, int(game), int(poke),
                        self.OWNED))

    def markUncaught(self, game, poke):  # * → uncaught
        self.db.execute('DELETE FROM caught WHERE gameID=? AND dexno=?',
                        (int(game), int(poke)))

    def getGameCount(self, game):
        caught, = self.db.execute('SELECT count(*) FROM caught WHERE gameID = ?'
                                  ' AND status = ?', (int(game), self.CAUGHT))
        owned,  = self.db.execute('SELECT count(*) FROM caught WHERE gameID = ?'
                                  ' AND status = ?', (int(game), self.OWNED))
        return (caught[0], owned[0])

    def allGames(self):
        return [Game(*(row + (self.get_game_names(row[0]),)))
                for row in self.db.execute('SELECT gameID, version,'
                                           ' player_name, dexsize FROM games'
                                           ' ORDER BY gameID ASC')]

    def allPokemon(self, maxno=None):
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
                for name, in cursor.execute('SELECT name FROM game_names'
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
            altnames += (colonbase,)
        return Game(gameID, version, player_name, int(dexsize), altnames)

    def get_pokemon_names(self, dexno):  # internal function
        return sum(self.db.execute('SELECT name FROM pokemon_names'
                                   ' WHERE dexno=? ORDER BY name ASC',
                                   (dexno,)), ())

    def get_game_names(self, gameID):  # internal function
        return sum(self.db.execute('SELECT name FROM game_names'
                                   ' WHERE gameID=? ORDER BY name ASC',
                                   (gameID,)), ())


class Game(namedtuple('Game', 'gameID version player_name dexsize altnames')):
    __slots__ = ()

    def __int__(self): return self.gameID

    def asYAML(self, caught_or_owned=None, owned=None):
        s = '''
- game ID: %d
  version: %s
  player name: %s
  dexsize: %d
  altnames:
%s
'''.strip() % (self.gameID, self.version, self.player_name, self.dexsize, ''.join('    - ' + a + '\n' for a in self.altnames))
        if caught_or_owned is not None:
            s += '  caught or owned: ' + str(caught_or_owned) + '\n'
        if owned is not None:
            s += '  owned: ' + str(owned) + '\n'
        return s

class Pokemon(namedtuple('Pokemon', 'dexno name altnames')):
    __slots__ = ()
    def __int__(self): return self.dexno


class CaughtDBError(Exception): pass


class NoSuchGameError(CaughtDBError, LookupError):
    def __init__(self, name=None, gameID=None):
        self.name   = name
        self.gameID = gameID
        super(NoSuchGameError, self).__init__(name, gameID)

    def __str__(self):
        if self.gameID is None:
            return 'No such game name: %r' % (self.name,)
        else:
            return 'No such gameID: %d' % (self.gameID,)


class NoSuchPokemonError(CaughtDBError, LookupError):
    def __init__(self, name=None, dexno=None):
        self.name  = name
        self.dexno = dexno
        super(NoSuchPokemonError, self).__init__(name, dexno)

    def __str__(self):
        if self.dexno is None:
            return 'No such Pokémon name: %r' % (self.name,)
        else:
            return 'No such dexno: %d' % (self.dexno,)


class MalformedFileError(CaughtDBError, ValueError):
    def __init__(self, filename, lineno, reason):
        self.filename = filename
        self.lineno = lineno
        self.reason = reason
        super(MalformedFileError, self).__init__(filename, lineno, reason)

    def __str__(self):
        return '%s: line %d: %s' % (self.filename, self.lineno, self.reason)
