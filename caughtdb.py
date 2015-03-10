# -*- coding: utf-8 -*-
from   collections import namedtuple
import sqlite3

class CaughtDB(object):
    SCHEMA = '''
CREATE TABLE pokemon (dexno INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                      name  TEXT    NOT NULL UNIQUE);

CREATE TABLE pokemon_names (dexno INTEGER NOT NULL REFERENCES pokemon(dexno),
                            name  TEXT    NOT NULL UNIQUE,
                            CHECK (name = lower(name)));

CREATE TABLE games (gameID      INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                    name        TEXT    NOT NULL UNIQUE,
                    version     TEXT,
                    player_name TEXT,
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

    def create(self, pokedex=None):
        self.db.executescript(self.SCHEMA)
        if pokedex is not None:
            for poke in Pokemon.fromTSVFile(pokedex):
                self.db.execute('INSERT OR ROLLBACK INTO pokemon (dexno, name)'
                                ' VALUES (?,?)', (poke.dexno, poke.name))
                self.db.executemany('INSERT OR ROLLBACK INTO pokemon_names'
                                    ' (dexno, name) VALUES (?,?)',
                                    ((poke.dexno, name.lower())
                                     for name in (str(poke.dexno), poke.name)
                                                 + poke.synonyms))

    def newGame(self, game, ignore_dups=False):
        # `game.gameID` is ignored.
        cursor = self.db.cursor()
        cursor.execute('SELECT gameID FROM game_names WHERE name=?',
                       (game.name.lower(),))
        if cursor.fetchmany():
            raise DuplicateNameError('Game', game.name)
        cursor.execute('INSERT INTO games (name, version, player_name, dexsize)'
                       ' VALUES (?,?,?,?)', (game.name, game.version,
                                             game.player_name, game.dexsize))
        gameID = cursor.lastrowid
        usedSynonyms = set()
        for syn in [game.name] + list(game.synonyms):
            syn = syn.lower()
            if syn in usedSynonyms:
                continue
            try:
                cursor.execute('INSERT INTO game_names (gameID, name)'
                               ' VALUES (?,?)', (gameID, syn))
            except sqlite3.Error:
                if not ignore_dups:
                    raise DuplicateNameError('Game', syn)
            else:
                usedSynonyms.add(syn)
        usedSynonyms.remove(game.name.lower())
        return Game(gameID, game.name, game.version, game.player_name,
                    game.dexsize, tuple(sorted(usedSynonyms)))

    def deleteGame(self, game):
        self.db.execute('DELETE FROM caught WHERE gameID=?', (int(game),))
        self.db.execute('DELETE FROM game_names WHERE gameID=?', (int(game),))
        self.db.execute('DELETE FROM games WHERE gameID=?', (int(game),))

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
        return self.getPokemonByDexno(dexno)

    def getPokemonByDexno(self, dexno):
        dexno = int(dexno)
        cursor = self.db.cursor()
        cursor.execute('SELECT name FROM pokemon WHERE dexno=?', (dexno,))
        try:
            name, = cursor.fetchone()
        except TypeError:
            raise NoSuchPokemonError(dexno=gameID)
        return Pokemon(dexno, name, self.get_pokemon_names(dexno))

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
        cursor.execute('SELECT name, version, player_name, dexsize FROM games'
                       ' WHERE gameID=?', (gameID,))
        try:
            name, version, player_name, dexsize = cursor.fetchone()
        except TypeError:
            raise NoSuchGameError(gameID=gameID)
        return Game(gameID, name, version, player_name, dexsize,
                    self.get_game_names(gameID))

    def getGameCount(self, game):
        caught, = self.db.execute('SELECT count(*) FROM caught WHERE gameID = ?'
                                  ' AND status = ?', (int(game), int(Status.CAUGHT)))
        owned,  = self.db.execute('SELECT count(*) FROM caught WHERE gameID = ?'
                                  ' AND status = ?', (int(game), int(Status.OWNED)))
        return (caught[0], owned[0])

    def allGames(self):
        return [Game(*(row + (self.get_game_names(row[0]),)))
                for row in self.db.execute('SELECT gameID, name, version,'
                                           ' player_name, dexsize FROM games'
                                           ' ORDER BY gameID ASC')]

    def getStatus(self, game, poke):
        cursor = self.db.cursor()
        cursor.execute('SELECT status FROM caught WHERE gameID=? AND dexno=?',
                       (int(game), int(poke)))
        try:
            status, = cursor.fetchone()
        except TypeError:
            return self.UNCAUGHT
        return Status.fromValue(status)

    def getStatusRange(self, game, start=None, end=None):  # inclusive range
        if not isinstance(game, Game):
            ### Rethink this:
            game = self.getGameByID(game)
        if start is None and end is None:
            start, end = 1, game.dexsize
        elif end is None:
            start, end = 1, start
        elif start is None:
            ### Should this be an error instead?
            start = 1
        start = int(start)
        end = min(int(end), game.dexsize)
        return [(Pokemon(dexno, name, self.get_pokemon_names(dexno)),
                Status.fromValue(status))
                for dexno, name, status in self.db.execute('''
                    SELECT dexno, pokemon.name, IFNULL(caught.status, ?)
                    FROM pokemon LEFT JOIN (SELECT dexno, status FROM caught
                                            WHERE gameID = ?) AS caught
                    USING (dexno)
                    WHERE ? <= dexno AND dexno <= ?
                    ORDER BY dexno ASC
                    ''', (int(Status.UNCAUGHT), int(game), start, end))]

    def getByStatus(self, game, status, maxno=None):
        status = int(status)
        if status == int(Status.UNCAUGHT):
            return [Pokemon(dexno, name, self.get_pokemon_names(dexno))
                    for dexno, name in self.db.execute('''
                        SELECT dexno, pokemon.name
                        FROM pokemon LEFT JOIN (SELECT dexno, status FROM caught
                                                WHERE gameID = ?)
                        USING (dexno)
                        WHERE status IS NULL AND (? OR dexno <= ?)
                        ORDER BY dexno ASC
                        ''', (int(game), int(maxno is None), int(maxno)))]
        else:
            return [Pokemon(dexno, name, self.get_pokemon_names(dexno))
                    for dexno, name in self.db.execute('''
                        SELECT dexno, pokemon.name
                        FROM pokemon JOIN (SELECT dexno, status FROM caught
                                           WHERE gameID = ?)
                        USING (dexno)
                        WHERE status = ? AND (? OR dexno <= ?)
                        ORDER BY dexno ASC
                        ''', (int(game), status, int(maxno is None),
                              int(maxno)))]

    def setStatus(self, game, poke, status):
        status = int(status)
        if status not in tuple(int(s) for s in Status.STATUSES):
            ### Should this use a custom Exception type?
            raise ValueError('%d: not a valid status' % (status,))
        if status == int(Status.UNCAUGHT):
            self.db.execute('DELETE FROM caught WHERE gameID=? AND dexno=?',
                            (int(game), int(poke)))
        else:
            self.db.execute('INSERT OR REPLACE INTO caught (gameID, dexno,'
                            ' status) VALUES (?, ?, ?)', (int(game), int(poke),
                            status))

    def markCaught(self, game, poke):  # uncaught → caught
        self.db.execute('INSERT OR IGNORE INTO caught (gameID, dexno, status)'
                        ' VALUES (?, ?, ?)', (int(game), int(poke),
                        int(Status.CAUGHT)))

    def markOwned(self, game, poke):  # * → owned
        self.db.execute('INSERT OR REPLACE INTO caught (gameID, dexno, status)'
                        ' VALUES (?, ?, ?)', (int(game), int(poke),
                        int(Status.OWNED)))

    def markReleased(self, game, poke):  # owned → caught
        self.db.execute('UPDATE caught SET status=? WHERE gameID=? AND dexno=?'
                        ' AND status=?', (int(Status.CAUGHT), int(game),
                                          int(poke), int(Status.OWNED)))

    def markUncaught(self, game, poke):  # * → uncaught
        self.db.execute('DELETE FROM caught WHERE gameID=? AND dexno=?',
                        (int(game), int(poke)))

    def get_pokemon_names(self, dexno):  # internal function
        return sum(self.db.execute('SELECT name FROM pokemon_names'
                                   ' WHERE dexno=? ORDER BY name ASC',
                                   (dexno,)), ())

    def get_game_names(self, gameID):  # internal function
        return sum(self.db.execute('SELECT name FROM game_names'
                                   ' WHERE gameID=? ORDER BY name ASC',
                                   (gameID,)), ())


class Status(namedtuple('Status', 'value name checks')):
    __slots__ = ()

    def __int__(self): return self.value

    def __str__(self): return self.name

    def __repr__(self): return self.__class__.__name__ + '.' + self.name.upper()

    @classmethod
    def fromValue(cls, val): return cls.STATUSES[val]

### TODO: Improve the checkmarks:
Status.UNCAUGHT   = Status(0, 'uncaught', '  ')
Status.CAUGHT     = Status(1, 'caught',   '✓ ')
Status.OWNED      = Status(2, 'owned',    '✓✓')
Status.STATUSES   = (Status.UNCAUGHT, Status.CAUGHT, Status.OWNED)
Status.CHECKS_LEN = 2


class Game(namedtuple('Game', 'gameID name version player_name dexsize synonyms')):
# `version` and `player_name` are the only attributes that should ever be
# `None`.
    __slots__ = ()

    def __int__(self): return self.gameID

    def __str__(self): return self.name

    def asYAML(self, caught_or_owned=None, owned=None):
        version = 'null' if self.version is None else self.version
        player_name = 'null' if self.player_name is None else self.player_name
        yml = '''
- game ID: %d
  name: %s
  version: %s
  player name: %s
  dexsize: %d
  synonyms:
%s
'''.strip() % (self.gameID, self.name, version, player_name, self.dexsize,
               ''.join('    - ' + syn + '\n' for syn in self.synonyms))
        if caught_or_owned is not None:
            yml += '  caught or owned: ' + str(caught_or_owned) + '\n'
        if owned is not None:
            yml += '  owned: ' + str(owned) + '\n'
        return yml

    def asDict(self, caught_or_owned=None, owned=None):
        d = {
                "game ID":     self.gameID,
                "name":        self.name,
                "version":     self.version,
                "player name": self.player_name,
                "dexsize":     self.dexsize,
                "synonyms":    list(self.synonyms)
            }
        if caught_or_owned is not None:
            d["caught or owned"] = caught_or_owned
        if owned is not None:
            d["owned"] = owned
        return d

    def asJSON(self, caught_or_owned=None, owned=None):
        import json
        return json.dumps(self.asDict(caught_or_owned, owned))


class Pokemon(namedtuple('Pokemon', 'dexno name synonyms')):
    __slots__ = ()

    def __int__(self): return self.dexno

    def __str__(self): return self.name

    @classmethod
    def fromTSVFile(cls, pokedex):
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
                yield cls(dexno, fields[1], tuple(fields[2:]))


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


class DuplicateNameError(CaughtDBError, ValueError):
    def __init__(self, objType, name):
        self.objType = objType
        self.name = name
        super(DuplicateNameError, self).__init__(objType, name)

    def __str__(self):
        return 'Duplicate %s name: %r' % (self.objType, self.name)
