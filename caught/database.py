# -*- coding: utf-8 -*-
from   collections import namedtuple
import json
import sqlalchemy as S

schema = S.MetaData()

pokemon_tbl = S.Table('pokemon', schema,
    S.Column('dexno', S.Integer, primary_key=True, nullable=False),
    S.Column('name', S.Unicode(255), nullable=False, unique=True),
)

pokemon_names_tbl = S.Table('pokemon_names', schema,
    S.Column('dexno', S.Integer, S.ForeignKey(pokemon_tbl.c.dexno), nullable=False),
    S.Column(
        'name',
        S.Unicode(255),
        S.CheckConstraint('name = lower(name)'),
        nullable=False,
        unique=True,
    ),
)

games_tbl = S.Table('games', schema,
    S.Column('gameID', S.Integer, primary_key=True, nullable=False),
    S.Column('name', S.Unicode(255), nullable=False, unique=True),
    S.Column('version', S.Unicode(255)),
    S.Column('player_name', S.Unicode(255)),
    S.Column('dexsize', S.Integer, nullable=False),
)

game_names_tbl = S.Table('game_names', schema,
    S.Column('gameID', S.Integer, S.ForeignKey(games_tbl.c.gameID), nullable=False),
    S.Column(
        'name',
        S.Unicode(255),
        S.CheckConstraint('name = lower(name)'),
        nullable=False,
        unique=True,
    ),
)

caught_tbl = S.Table('caught', schema,
    S.Column('gameID', S.Integer, S.ForeignKey(games_tbl.c.gameID), nullable=False, primary_key=True),
    S.Column('dexno', S.Integer, S.ForeignKey(pokemon_tbl.c.dexno), nullable=False, primary_key=True),
    S.Column('status', S.Integer, nullable=False),
)

class CaughtDB(object):
    def __init__(self, dbpath):
        self.engine = S.create_engine(S.engine.url.URL(
            drivername = 'sqlite',
            database   = dbpath,
        ))
        schema.create_all(self.engine)

    def __enter__(self):
        self.conn = self.engine.connect()
        self.trans = self.conn.begin()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is None:
            self.trans.commit()
        else:
            self.trans.rollback()
        self.conn.close()
        return False

    def create(self, pokedex=None):
        #schema.create_all(engine)
        if pokedex is not None:
            for poke in Pokemon.fromTSVFile(pokedex):
                self.conn.execute(
                    pokemon_tbl.insert().values(dexno=poke.dexno,name=poke.name)
                )
                self.conn.execute(pokemon_names_tbl.insert(), [{
                    "dexno": poke.dexno,
                    "name": name.lower(),
                } for name in (str(poke.dexno), poke.name) + poke.synonyms])

    def newGame(self, game, ignore_dups=False):
        # `game.gameID` is ignored.
        r = self.conn.execute(
            S.select([S.func.count()]).select_from(game_names_tbl)
             .where(game_names_tbl.c.name == game.name.lower())
        ).scalar()
        if r > 0:
            raise DuplicateNameError('Game', game.name)
        gameID = self.conn.execute(games_tbl.insert().values(
            name        = game.name,
            version     = game.version,
            player_name = game.player_name,
            dexsize     = game.dexsize,
        )).inserted_primary_key[0]
        usedSynonyms = set()
        for syn in [game.name] + list(game.synonyms):
            syn = syn.lower()
            if syn in usedSynonyms:
                continue
            try:
                self.conn.execute(
                    game_names_tbl.insert().values(gameID=gameID, name=syn)
                )
            except S.exc.DBAPIError:
                if not ignore_dups:
                    raise DuplicateNameError('Game', syn)
            else:
                usedSynonyms.add(syn)
        usedSynonyms.remove(game.name.lower())
        return Game(gameID, game.name, game.version, game.player_name,
                    game.dexsize, tuple(sorted(usedSynonyms)))

    def deleteGame(self, game):
        self.conn.execute(
            caught_tbl.delete().where(caught_tbl.c.gameID == int(game))
        )
        self.conn.execute(
            game_names_tbl.delete().where(game_names_tbl.c.gameID == int(game))
        )
        self.conn.execute(
            games_tbl.delete().where(games_tbl.c.gameID == int(game))
        )

    def getPokemon(self, name):
        """
        Returns the `Pokemon` object for the Pokémon with the given name.
        Raises a `NoSuchPokemonError` if there is no such Pokémon.
        """
        r = self.conn.execute(
            S.select([pokemon_names_tbl.c.dexno])
             .where(pokemon_names_tbl.c.name == name.lower())
        )
        try:
            dexno, = r.fetchone()
        except TypeError:
            raise NoSuchPokemonError(name)
        return self.getPokemonByDexno(dexno)

    def getPokemonByDexno(self, dexno):
        dexno = int(dexno)
        r = self.conn.execute(
            S.select([pokemon_tbl.c.name]).where(pokemon_tbl.c.dexno == dexno)
        )
        try:
            name, = r.fetchone()
        except TypeError:
            raise NoSuchPokemonError(dexno=dexno)
        return Pokemon(dexno, name, self.get_pokemon_names(dexno))

    def getPokemonRange(self, pokeA, pokeB, maxno=None):
        pokeA = int(pokeA)
        pokeB = int(pokeB)
        if maxno is not None:
            pokeB = min(pokeB, maxno)
        return [
            Pokemon(dexno, name, self.get_pokemon_names(dexno))
            for dexno, name in self.conn.execute(
                S.select([pokemon_tbl.c.dexno, pokemon_tbl.c.name])
                 .where(pokeA <= pokemon_tbl.c.dexno)
                 .where(pokemon_tbl.c.dexno <= pokeB)
                 .order_by(S.asc(pokemon_tbl.c.dexno))
            )
        ]

    def allPokemon(self, maxno=None):
        query = S.select([pokemon_tbl.c.dexno, pokemon_tbl.c.name]) \
                 .order_by(S.asc(pokemon_tbl.c.dexno))
        if maxno is not None:
            query = query.where(pokemon_tbl.c.dexno <= maxno)
        return [Pokemon(dexno, name, self.get_pokemon_names(dexno))
                for dexno, name in self.conn.execute(query)]

    def pokemonQty(self):
        """
        Returns the largest Pokémon ``dexno`` in the database, i.e., the
        largest possible ``dexsize`` value
        """
        return self.conn.execute(
            ### S.select(S.func.max(pokemon_tbl.c.dexno))
            S.select([pokemon_tbl.c.dexno])
             .order_by(S.desc(pokemon_tbl.c.dexno))
             .limit(1)
        ).scalar()

    def getGame(self, name):
        """
        Returns the `Game` object for the game with the given name.  Raises a
        `NoSuchGameError` if there is no such game.
        """
        r = self.conn.execute(
            S.select([game_names_tbl.c.gameID])
             .where(game_names_tbl.c.name == name.lower())
        )
        try:
            gameID, = r.fetchone()
        except TypeError:
            raise NoSuchGameError(name)
        return self.getGameByID(gameID)

    def getGameByID(self, gameID):
        gameID = int(gameID)
        game = self.conn.execute(
            S.select([games_tbl]).where(games_tbl.c.gameID == gameID)
        ).first()
        if game is None:
            raise NoSuchGameError(gameID=gameID)
        return Game(
            gameID,
            game["name"],
            game["version"],
            game["player_name"],
            game["dexsize"],
            self.get_game_names(gameID),
        )

    def getGameCount(self, game):
        caught = self.conn.execute(
            S.select([S.func.count()]).select_from(caught_tbl)
             .where(caught_tbl.c.gameID == int(game))
             .where(caught_tbl.c.status == int(Status.CAUGHT))
        ).scalar()
        owned = self.conn.execute(
            S.select([S.func.count()]).select_from(caught_tbl)
             .where(caught_tbl.c.gameID == int(game))
             .where(caught_tbl.c.status == int(Status.OWNED))
        ).scalar()
        return (caught, owned)

    def allGames(self):
        return [Game(
            game["gameID"],
            game["name"],
            game["version"],
            game["player_name"],
            game["dexsize"],
            self.get_game_names(game["gameID"])
        ) for game in self.conn.execute(
            S.select([games_tbl]).order_by(S.asc(games_tbl.c.gameID))
        )]

    def getStatus(self, game, poke):
        status = self.conn.execute(
            S.select([caught_tbl.c.status])
             .where(caught_tbl.c.gameID == int(game))
             .where(caught_tbl.c.dexno  == int(poke))
        ).scalar()
        return Status.UNCAUGHT if status is None else Status.fromValue(status)

    def getStatusRange(self, game, start=None, end=None):  # inclusive range
        if not isinstance(game, Game):
            ### TODO: Rethink this:
            game = self.getGameByID(game)
        if start is None and end is None:
            start, end = 1, game.dexsize
        elif end is None:
            start, end = 1, start
        elif start is None:
            ### TODO: Should this be an error instead?
            start = 1
        start = int(start)
        end = min(int(end), game.dexsize)
        game_caught = S.select([caught_tbl])\
                       .where(caught_tbl.c.gameID == int(game))\
                       .alias('game_caught')
        return [(
            Pokemon(dexno, name, self.get_pokemon_names(dexno)),
            Status.fromValue(status),
        ) for dexno, name, status in self.conn.execute(
            S.select([
                pokemon_tbl.c.dexno,
                pokemon_tbl.c.name,
                S.func.IFNULL(game_caught.c.status, int(Status.UNCAUGHT)),
            ]).select_from(pokemon_tbl.outerjoin(game_caught))
              .where(start <= pokemon_tbl.c.dexno)
              .where(pokemon_tbl.c.dexno <= end)
              .order_by(S.asc(pokemon_tbl.c.dexno))
        )]

    def getByStatus(self, game, status, maxno=None):
        status = int(status)
        game_caught = S.select([caught_tbl])\
                       .where(caught_tbl.c.gameID == int(game))\
                       .alias('game_caught')
        query = S.select([pokemon_tbl.c.dexno, pokemon_tbl.c.name])\
                  .select_from(pokemon_tbl.join(
                    game_caught,
                    isouter=(status == int(Status.UNCAUGHT)),
                  )).order_by(S.asc(pokemon_tbl.c.dexno))
        if status == int(Status.UNCAUGHT):
            query = query.where(game_caught.c.status == None)  # noqa: E711
        else:
            query = query.where(game_caught.c.status == status)
        if maxno is not None:
            query = query.where(pokemon_tbl.c.dexno <= int(maxno))
        return [
            Pokemon(dexno, name, self.get_pokemon_names(dexno))
            for dexno, name in self.conn.execute(query)
        ]

    def setStatus(self, game, poke, status):
        status = int(status)
        if status not in tuple(int(s) for s in Status.STATUSES):
            raise ValueError('%d: not a valid status' % (status,))
        if status == int(Status.UNCAUGHT):
            self.conn.execute(
                caught_tbl.delete().where(caught_tbl.c.gameID == int(game))
                                   .where(caught_tbl.c.dexno  == int(poke))
            )
        elif self.getStatus(game, poke) == Status.UNCAUGHT:
            self.conn.execute(caught_tbl.insert().values(
                gameID = int(game),
                dexno  = int(poke),
                status = status,
            ))
        else:
            self.conn.execute(
                caught_tbl.update().values(status=status)
                                   .where(caught_tbl.c.gameID == int(game))
                                   .where(caught_tbl.c.dexno  == int(poke))
            )

    def markCaught(self, game, poke):  # uncaught → caught
        if self.getStatus(game, poke) == Status.UNCAUGHT:
            self.conn.execute(caught_tbl.insert().values(
                gameID = int(game),
                dexno  = int(poke),
                status = int(Status.CAUGHT),
            ))

    def markOwned(self, game, poke):  # * → owned
        self.setStatus(game, poke, Status.OWNED)

    def markReleased(self, game, poke):  # owned → caught
        self.conn.execute(
            caught_tbl.update().values(status=int(Status.CAUGHT))
                               .where(caught_tbl.c.gameID == int(game))
                               .where(caught_tbl.c.dexno  == int(poke))
                               .where(caught_tbl.c.status == int(Status.OWNED))
        )

    def markUncaught(self, game, poke):  # * → uncaught
        self.setStatus(game, poke, Status.UNCAUGHT)

    def get_pokemon_names(self, dexno):  # internal function
        return [n for n, in self.conn.execute(
            S.select([pokemon_names_tbl.c.name])
             .where(pokemon_names_tbl.c.dexno == dexno)
             .order_by(S.asc(pokemon_names_tbl.c.name))
        )]

    def get_game_names(self, gameID):  # internal function
        return [n for n, in self.conn.execute(
            S.select([game_names_tbl.c.name])
             .where(game_names_tbl.c.gameID == gameID)
             .order_by(S.asc(game_names_tbl.c.name))
        )]


class Status(namedtuple('Status', 'value name checks')):
    __slots__ = ()

    def __int__(self):
        return self.value

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.__class__.__name__ + '.' + self.name.upper()

    @classmethod
    def fromValue(cls, val):
        return cls.STATUSES[val]

### TODO: Improve the checkmarks:
Status.UNCAUGHT = Status(0, 'uncaught', '  ')
Status.CAUGHT = Status(1, 'caught', '✓ ')
Status.OWNED = Status(2, 'owned', '✓✓')
Status.STATUSES = (Status.UNCAUGHT, Status.CAUGHT, Status.OWNED)
Status.CHECKS_LEN = 2


class Game(namedtuple('Game', 'gameID name version player_name dexsize synonyms')):
    # `version` and `player_name` are the only attributes that should ever be
    # `None`.
    __slots__ = ()

    def __int__(self):
        return self.gameID

    def __str__(self):
        return self.name

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
        return json.dumps(self.asDict(caught_or_owned, owned))


class Pokemon(namedtuple('Pokemon', 'dexno name synonyms')):
    __slots__ = ()

    def __int__(self):
        return self.dexno

    def __str__(self):
        return self.name

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


class CaughtDBError(Exception):
    pass


class NoSuchGameError(CaughtDBError, LookupError):
    def __init__(self, name=None, gameID=None):
        self.name = name
        self.gameID = gameID
        super(NoSuchGameError, self).__init__(name, gameID)

    def __str__(self):
        if self.gameID is None:
            return 'No such game name: %r' % (self.name,)
        else:
            return 'No such gameID: %d' % (self.gameID,)


class NoSuchPokemonError(CaughtDBError, LookupError):
    def __init__(self, name=None, dexno=None):
        self.name = name
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
