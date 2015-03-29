#!/usr/bin/python
# -*- coding: utf-8 -*-
import argparse
from   collections import OrderedDict
import csv
import heapq
from   itertools import izip_longest
import json
import os
import sys
import caughtdb
from   caughtdb import CaughtDB, Game, Status

### TODO: Make this non-Unix friendly:
default_dbfile = os.environ.get("HOME", ".") + '/.caughtdb'

statuses = {"uncaught": set([Status.UNCAUGHT]),
            "caught":   set([Status.CAUGHT]),
            "caught+":  set([Status.CAUGHT, Status.OWNED]),
            "owned":    set([Status.OWNED]),
            "unowned":  set([Status.UNCAUGHT, Status.CAUGHT])}

set_cmds = OrderedDict([('add', (CaughtDB.markCaught, (Status.UNCAUGHT,), Status.CAUGHT)),
                        ('own', (CaughtDB.markOwned, (Status.UNCAUGHT, Status.CAUGHT), Status.OWNED)),
                        ('release', (CaughtDB.markReleased, (Status.OWNED,), Status.CAUGHT)),
                        ('uncatch', (CaughtDB.markUncaught, (Status.CAUGHT, Status.OWNED), Status.UNCAUGHT))])

POKEMON_NAME_LEN = 12

NONEXISTENT = '##'

def warn(s):
    #sys.stderr.write(sys.argv[0] + ': ' + s + "\n")
    sys.stderr.write('Warning: ' + s + "\n")

def listPokemon(db, args, maxno=None, warn_on_fail=False):
    for fp in args.file:
        with fp:
            for line in fp:
                line = line.strip()
                if line == '' or line[0] == '#':
                    continue
                for pokedata in getPokemon(db, line, maxno, warn_on_fail):
                    yield pokedata
    for poke in args.pokemon:
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
    except caughtdb.NoSuchPokemonError as e:
        for (a, b) in splitHyphens(poke):
            try:
                pokeA = db.getPokemon(a)
                pokeB = db.getPokemon(b)
            except caughtdb.NoSuchPokemonError:
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
    except caughtdb.NoSuchGameError as e:
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
            sys.stdout.write('{')
        else:
            self.widths = [self.minlengths[0]]
            sys.stdout.write(' ' * self.minlengths[0])
            for h, ml in izip_longest(heads, self.minlengths[1:], fillvalue=0):
                if h == 0:
                    break
                h = h.decode('utf-8')
                self.widths.append(max(len(h), ml))
                sys.stdout.write((u'|%-*s' % (self.widths[-1], h)).encode('utf-8'))
            sys.stdout.write('\n')
            print '|'.join('-' * w for w in self.widths)

    def row(self, values):
        if self.heads is None and self.widths is None:
            raise RuntimeError('Tabulator.row() called before Tabulator.header()')
        if self.json:
            if self.first:
                self.first = False
            else:
                sys.stdout.write(',')
            values = tuple(values)
            sys.stdout.write(json.dumps(values[0]) + ':' +
                             json.dumps(dict(izip_longest(self.heads,
                                                          values[1:]))))
        else:
            first = True
            for val, width in izip_longest(values, self.widths):
                if width is None:
                    break
                if first:
                    first = False
                else:
                    sys.stdout.write('|')
                val = str(val).decode('utf-8')
                sys.stdout.write((u'%-*s' % (width, val or '')).encode('utf-8'))
            sys.stdout.write('\n')

    def end(self):
        if self.json:
            sys.stdout.write('}\n')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-D', '--dbfile', default=default_dbfile)
    parser.add_argument('-G', dest='force_gname', action='store_true')

    subparser = parser.add_subparsers(title='command', dest='cmd')

    subparser_create = subparser.add_parser('create')
    subparser_create.add_argument('pokedex')

    subparser_new = subparser.add_parser('new')
    subparser_new.add_argument('-i', '--ignore-dups', action='store_true')
    subparser_new.add_argument('-q', '--quiet', action='store_true')
    subparser_new.add_argument('--version')
    subparser_new.add_argument('--player-name', '--player')
    subparser_new.add_argument('name')
    subparser_new.add_argument('dexsize', type=int)
    subparser_new.add_argument('synonyms', nargs='*')

    subparser_delete = subparser.add_parser('delete')
    subparser_delete.add_argument('-f', '--force', action='store_true')
    subparser_delete.add_argument('games', nargs='+')

    for name in set_cmds.iterkeys():
        sp = subparser.add_parser(name)
        sp.add_argument('-F', '--file', action='append', default=[],
                        type=argparse.FileType('r'))
        sp.add_argument('-v', '--verbose', action='store_true')
        sp.add_argument('game')
        sp.add_argument('pokemon', nargs='*')

    subparser_get = subparser.add_parser('get')
    subparser_get.add_argument('--games', type=GameCSV)
    subparser_get.add_argument('-F', '--file', action='append', default=[],
                                  type=argparse.FileType('r'))
    subparser_get.add_argument('-J', '--json', action='store_true')
    subparser_get.add_argument('pokemon', nargs='*')

    subparser_list = subparser.add_parser('list')
    subparser_list.add_argument('status')
    subparser_list.add_argument('game')

    subparser_games = subparser.add_parser('games')
    subparser_games.add_argument('-J', '--json', action='store_true')
    subparser_games.add_argument('-s', '--stats', action='store_true')
    subparser_games.add_argument('games', nargs='*')

    subparser_stats = subparser.add_parser('stats')
    subparser_stats.add_argument('-J', '--json', action='store_true')
    subparser_stats.add_argument('games', nargs='*')

    args = parser.parse_args()

    try:
        with CaughtDB(args.dbfile) as db:

            if args.cmd == 'create':
                db.create(args.pokedex)

            elif args.cmd == 'new':
                gameID = db.newGame(Game(None, args.name, args.version,
                                         args.player_name, args.dexsize,
                                         args.synonyms),
                                    ignore_dups=args.ignore_dups)
                if not args.quiet:
                    print gameID.asYAML()

            elif args.cmd == 'delete':
                for g in args.games:
                    game = getGame(db, g, warn_on_fail=True, force_gname=args.force_gname)
                    if game is None:
                        continue
                    yesdel = args.force
                    while not yesdel:
                        response = raw_input('Really delete ' + g + '? (y/n) ')\
                                            .strip().lower()
                        if response in ('y', 'yes'):
                            yesdel = True
                        elif response in ('n', 'no'):
                            yesdel = False
                            break
                        else:
                            print 'Invalid response.'
                    if yesdel:
                        db.deleteGame(game)

            elif args.cmd in set_cmds:
                method, domain, target = set_cmds[args.cmd]
                game = getGame(db, args.game, force_gname=args.force_gname)
                for pokedata in listPokemon(db, args, maxno=game.dexsize):
                    if args.verbose:
                        stat = db.getStatus(game, pokedata)
                        if stat in domain:
                            method(db, game, pokedata)
                            print '%3d. %s: %s → %s' % (pokedata.dexno, pokedata.name, stat, target)
                        else:
                            print '%3d. %s: %s' % (pokedata.dexno, pokedata.name, stat)
                    else:
                        method(db, game, pokedata)

            elif args.cmd == 'get':
                if args.games:
                    games = [getGame(db, g, force_gname=args.force_gname)
                             for g in args.games]
                else:
                    games = db.allGames()
                table = Tabulator([POKEMON_NAME_LEN+5] + [2]*len(games),
                                  use_json=args.json)
                table.header(g.name for g in games)
                maxno = max(g.dexsize for g in games)
                if args.file or args.pokemon:
                    pokemon = listPokemon(db, args, maxno=maxno,
                                          warn_on_fail=True)
                else:
                    pokemon = db.allPokemon(maxno=maxno)
                for pokedata in pokemon:
                    stats = [db.getStatus(g, pokedata)
                             if pokedata.dexno <= g.dexsize
                             else None
                             for g in games]
                    if args.json:
                        table.row([pokedata.name] +
                                  [s.name if s is not None else s
                                   for s in stats])
                    else:
                        table.row(['%3d. %-*s' % (pokedata.dexno,
                                                  POKEMON_NAME_LEN,
                                                  pokedata.name)] +
                                  [s.checks if s is not None else NONEXISTENT
                                   for s in stats])
                table.end()

            elif args.cmd == 'list':
                game = getGame(db, args.game, force_gname=args.force_gname)
                toList = set()
                for status in args.status.split('/'):
                    status = status.strip().lower()
                    if status in statuses:
                        toList |= statuses[status]
                    else:
                        raise SystemExit(sys.argv[0] + ': ' + status
                                                     + ': invalid status')
                pokemon = []
                for status in toList:
                    pokemon = heapq.merge(pokemon,
                                          db.getByStatus(game, status,
                                                         game.dexsize))
                for poke in pokemon:
                    print str(poke)

            elif args.cmd == 'games':
                if args.stats:
                    def gameArgs(game):
                        caught, owned = db.getGameCount(game)
                        return (caught+owned, owned)
                else:
                    gameArgs = lambda _: ()
                if args.games:
                    games = filter(None, [getGame(db, g, warn_on_fail=True,
                                                  force_gname=args.force_gname)
                                          for g in args.games])
                else:
                    games = db.allGames()
                if args.json:
                    jsonses = []
                    for game in games:
                        jsonses.append(game.asJSON(*gameArgs(game)))
                    print '[' + ', '.join(jsonses) + ']'
                else:
                    for game in games:
                        print game.asYAML(*gameArgs(game))

            elif args.cmd == 'stats':
                if args.games:
                    games = filter(None, [getGame(db, g, warn_on_fail=True,
                                                  force_gname=args.force_gname)
                                          for g in args.games])
                else:
                    games = db.allGames()
                table = Tabulator([max(len(g.name.decode('utf-8')) for g in games), 3, 3], use_json=args.json)
                table.header(['caught or owned', 'owned', 'maximum'])
                for game in games:
                    caught, owned = db.getGameCount(game)
                    table.row([game.name, caught+owned, owned, game.dexsize])
                table.end()

    except caughtdb.CaughtDBError as e:
        raise SystemExit(sys.argv[0] + ': ' + str(e))


if __name__ == '__main__':
    main()
