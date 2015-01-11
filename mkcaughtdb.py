#!/usr/bin/python
import sqlite3
import sys

if len(sys.argv) != 3:
    raise SystemExit('Usage: %s dbfile pokedex' % (sys.argv[0],))

dbfile  = sys.argv[1]
pokedex = sys.argv[2]

with sqlite3.connect(dbfile) as db:
    db.text_factory = str
    db.executescript('''
PRAGMA foreign_keys = ON;
PRAGMA encoding = "UTF-8";

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
''')

    with open(pokedex) as dex:
        for (lineno, line) in enumerate(dex, start=1):
            line = line.strip()
            if line == '' or line[0] == '#':
                continue
            fields = line.split('\t')
            if len(fields) < 2:
                raise SystemExit('%s: %s: line %d: too few fields'
                                 % (sys.argv[0], pokedex, lineno))
            try:
                dexno = int(fields[0])
            except ValueError:
                raise SystemExit('%s: %s: line %d: %s: not a number'
                                 % (sys.argv[0], pokedex, lineno, fields[0]))
            db.execute('INSERT OR ROLLBACK INTO pokemon (dexno, name)'
                       ' VALUES (?,?)', (dexno, fields[1]))
            db.executemany('INSERT OR ROLLBACK INTO pokemon_names (dexno, name)'
                           ' VALUES (?,?)', ((dexno, name.lower())
                                             for name in fields))
    db.commit()
