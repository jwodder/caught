# -*- coding: utf-8 -*-
import csv
import heapq
import json
import os
import os.path
import sys
import click
from   six.moves import input, zip_longest
from   .database import (
    CaughtDB, Game, Status, NoSuchPokemonError, NoSuchGameError,
)

DEFAULT_DBFILE = os.path.join(os.environ.get("HOME", os.curdir), '.caughtdb')

statuses = {
    "uncaught": {Status.UNCAUGHT},
    "caught":   {Status.CAUGHT},
    "caught+":  {Status.CAUGHT, Status.OWNED},
    "owned":    {Status.OWNED},
    "unowned":  {Status.UNCAUGHT, Status.CAUGHT}
}

POKEMON_NAME_LEN = 12

NONEXISTENT = '##'

def warn(s):
    #sys.stderr.write(sys.argv[0] + ': ' + s + "\n")
    sys.stderr.write('Warning: ' + s + "\n")

def listPokemon(db, pokefiles, pokemon, maxno=None, warn_on_fail=False):
    for fp in pokefiles:
        with fp:
            for line in fp:
                line = line.strip()
                if line == '' or line[0] == '#':
                    continue
                for pokedata in getPokemon(db, line, maxno, warn_on_fail):
                    yield pokedata
    for poke in pokemon:
        for pokedata in getPokemon(db, poke, maxno, warn_on_fail):
            yield pokedata

def splitHyphens(s):
    i = s.find('-')
    while i != -1:
        if 0 < i < len(s)-1:
            yield (s[:i], s[i+1:])
        i = s.find('-', i+1)

def getPokemon(db, poke, maxno=None, warn_on_fail=False):
    try:
        pokedata = db.getPokemon(poke)
    except NoSuchPokemonError as e:
        for (a, b) in splitHyphens(poke):
            try:
                pokeA = db.getPokemon(a)
                pokeB = db.getPokemon(b)
            except NoSuchPokemonError:
                continue
            else:
                return db.getPokemonRange(pokeA, pokeB, maxno)
        if warn_on_fail:
            warn(str(e))
            return []
        else:
            raise e
    else:
        return [pokedata]

def getGame(db, game, warn_on_fail=False, force_gname=False):
    try:
        if game.isdigit() and not force_gname:
            gamedata = db.getGameByID(int(game))
        else:
            gamedata = db.getGame(game)
    except NoSuchGameError as e:
        if warn_on_fail:
            warn(str(e))
            return None
        else:
            raise e
    else:
        return gamedata

def GameCSV(arg):
    ### TODO: Expand/customize (and add appropriate error handling?)
    return next(csv.reader([arg]))


class Tabulator(object):
    def __init__(self, minlengths, use_json=False):
        self.minlengths = tuple(minlengths)
        self.json = use_json
        self.first = True
        self.heads = None
        self.widths = None

    def header(self, heads):
        if self.json:
            self.heads = tuple(heads)
            click.echo('{', nl=False)
        else:
            self.widths = [self.minlengths[0]]
            click.echo(' ' * self.minlengths[0], nl=False)
            for h, ml in zip_longest(heads, self.minlengths[1:], fillvalue=0):
                if h == 0:
                    break
                h = from_bytes(h)
                self.widths.append(max(len(h), ml))
                click.echo(u'|%-*s' % (self.widths[-1], h), nl=False)
            click.echo()
            print('|'.join('-' * w for w in self.widths))

    def row(self, values):
        if self.heads is None and self.widths is None:
            raise RuntimeError('Tabulator.row() called before Tabulator.header()')
        if self.json:
            if self.first:
                self.first = False
            else:
                click.echo(',', nl=False)
            values = tuple(values)
            click.echo(
                json.dumps(values[0]) + ':'
                + json.dumps(dict(zip_longest(self.heads, values[1:]))),
                nl=False,
            )
        else:
            first = True
            for val, width in zip_longest(values, self.widths):
                if width is None:
                    break
                if first:
                    first = False
                else:
                    click.echo('|', nl=False)
                val = from_bytes(val)
                click.echo(u'%-*s' % (width, val or ''), nl=False)
            click.echo()

    def end(self):
        if self.json:
            click.echo('}')


@click.group()
@click.option('-D', '--dbfile', default=DEFAULT_DBFILE)
@click.pass_context
def main(ctx, dbfile):
    ctx.obj = CaughtDB(dbfile)

@main.command()
@click.argument('pokedex')
@click.pass_context
def create(ctx, pokedex):
    with ctx.obj as db:
        db.create(pokedex)

@main.command()
@click.option('-i', '--ignore-dups', is_flag=True)
@click.option('-q', '--quiet', is_flag=True)
@click.option('--version')
@click.option('--player-name', '--player')
@click.option('-D', '--dexsize', type=int)
@click.argument('name')
@click.argument('synonyms', nargs=-1)
@click.pass_context
def new(ctx, ignore_dups, quiet, version, player_name, dexsize, name, synonyms):
    with ctx.obj as db:
        if dexsize is None:
            dexsize = db.pokemonQty()
        gameID = db.newGame(
            Game(None, name, version, player_name, dexsize, synonyms),
            ignore_dups=ignore_dups,
        )
        if not quiet:
            print(gameID.asYAML())

@main.command()
@click.option('-f', '--force', is_flag=True)
@click.option('-G', 'force_gname', is_flag=True)
@click.argument('games', nargs=-1, required=True)
@click.pass_context
def delete(ctx, force, force_gname, games):
    with ctx.obj as db:
        for g in games:
            game = getGame(db, g, warn_on_fail=True, force_gname=force_gname)
            if game is None:
                continue
            yesdel = force
            while not yesdel:
                response = input('Really delete ' + g + '? (y/n) ').strip().lower()
                if response in ('y', 'yes'):
                    yesdel = True
                elif response in ('n', 'no'):
                    yesdel = False
                    break
                else:
                    print('Invalid response.')
            if yesdel:
                db.deleteGame(game)

def set_cmd(group, name, method, domain, target):
    @group.command(name)
    @click.option('-F', '--file', 'pokefiles', multiple=True, type=click.File('r'))
    @click.option('-G', 'force_gname', is_flag=True)
    @click.option('-v', '--verbose', is_flag=True)
    @click.argument('game')
    @click.argument('pokemon', nargs=-1)
    @click.pass_context
    def cmd(ctx, game, pokefiles, pokemon, verbose, force_gname):
        with ctx.obj as db:
            game = getGame(db, game, force_gname=force_gname)
            for pokedata in listPokemon(db, pokefiles, pokemon, maxno=game.dexsize):
                if verbose:
                    stat = db.getStatus(game, pokedata)
                    if stat in domain:
                        method(db, game, pokedata)
                        print('%3d. %s: %s → %s'
                              % (pokedata.dexno, pokedata.name, stat, target))
                    else:
                        print('%3d. %s: %s' % (pokedata.dexno, pokedata.name, stat))
                else:
                    method(db, game, pokedata)

for name, method, domain, target in [
    ('add',     CaughtDB.markCaught, (Status.UNCAUGHT,), Status.CAUGHT),
    ('own',     CaughtDB.markOwned, (Status.UNCAUGHT, Status.CAUGHT), Status.OWNED),
    ('release', CaughtDB.markReleased, (Status.OWNED,), Status.CAUGHT),
    ('uncatch', CaughtDB.markUncaught, (Status.CAUGHT, Status.OWNED), Status.UNCAUGHT),
]: set_cmd(main, name, method, domain, target)

@main.command()
@click.option('--games', type=GameCSV)
@click.option('-F', '--file', 'pokefiles', multiple=True, type=click.File('r'))
@click.option('-G', 'force_gname', is_flag=True)
@click.option('-J', '--json', 'use_json', is_flag=True)
@click.argument('pokemon', nargs=-1)
@click.pass_context
def get(ctx, games, pokefiles, use_json, pokemon, force_gname):
    with ctx.obj as db:
        if games:
            games = [getGame(db, g, force_gname=force_gname) for g in games]
        else:
            games = db.allGames()
        table = Tabulator(
            [POKEMON_NAME_LEN+5] + [2]*len(games),
            use_json=use_json,
        )
        table.header(g.name for g in games)
        maxno = max(g.dexsize for g in games)
        if pokefiles or pokemon:
            pokemon = listPokemon(db, pokefiles, pokemon, maxno=maxno,
                                  warn_on_fail=True)
        else:
            pokemon = db.allPokemon(maxno=maxno)
        for pokedata in pokemon:
            stats = [db.getStatus(g, pokedata)
                     if pokedata.dexno <= g.dexsize
                     else None
                     for g in games]
            if use_json:
                table.row([pokedata.name] +
                          [s.name if s is not None else s for s in stats])
            else:
                table.row(['%3d. %-*s' % (pokedata.dexno,
                                          POKEMON_NAME_LEN,
                                          pokedata.name)] +
                          [s.checks if s is not None else NONEXISTENT
                           for s in stats])
        table.end()

@main.command('list')
@click.option('-G', 'force_gname', is_flag=True)
@click.argument('status')
@click.argument('game')
@click.pass_context
def list_cmd(ctx, status, game, force_gname):
    with ctx.obj as db:
        game = getGame(db, game, force_gname=force_gname)
        toList = set()
        for stat in status.split('/'):
            stat = status.strip().lower()
            if stat in statuses:
                toList |= statuses[stat]
            else:
                ctx.fail(stat + ': invalid status')
        pokemon = []
        for status in toList:
            pokemon = heapq.merge(pokemon, db.getByStatus(game, status,
                                                          game.dexsize))
        for poke in pokemon:
            print(str(poke))

@main.command()
@click.option('-G', 'force_gname', is_flag=True)
@click.option('-J', '--json', 'use_json', is_flag=True)
@click.option('-s', '--stats', is_flag=True)
@click.argument('games', nargs=-1)
@click.pass_context
def games(ctx, games, use_json, stats, force_gname):
    with ctx.obj as db:
        if stats:
            def gameArgs(game):
                caught, owned = db.getGameCount(game)
                return (caught+owned, owned)
        else:
            gameArgs = lambda _: ()
        if games:
            games = filter(None, [getGame(db, g, warn_on_fail=True,
                                          force_gname=force_gname)
                                  for g in games])
        else:
            games = db.allGames()
        if use_json:
            jsonses = []
            for game in games:
                jsonses.append(game.asJSON(*gameArgs(game)))
            print('[' + ', '.join(jsonses) + ']')
        else:
            for game in games:
                print(game.asYAML(*gameArgs(game)))

@main.command()
@click.option('-G', 'force_gname', is_flag=True)
@click.option('-J', '--json', 'use_json', is_flag=True)
@click.argument('games', nargs=-1)
@click.pass_context
def stats(ctx, games, use_json, force_gname):
    with ctx.obj as db:
        if games:
            games = filter(None, [getGame(db, g, warn_on_fail=True,
                                          force_gname=force_gname)
                                  for g in games])
        else:
            games = db.allGames()
        table = Tabulator(
            [max(len(from_bytes(g.name)) for g in games), 3, 3],
            use_json=use_json,
        )
        table.header(['caught or owned', 'owned', 'maximum'])
        for game in games:
            caught, owned = db.getGameCount(game)
            table.row([game.name, caught+owned, owned, game.dexsize])
        table.end()

def from_bytes(s):
    return s.decode('utf-8') if isinstance(s, bytes) else s

if __name__ == '__main__':
    main()
