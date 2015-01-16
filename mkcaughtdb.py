#!/usr/bin/python
import sys
import caughtdb

if len(sys.argv) != 3:
    raise SystemExit('Usage: %s dbfile pokedex' % (sys.argv[0],))

try:
    with caughtdb.CaughtDB(sys.argv[1]) as db:
        db.create(sys.argv[2])
except CaughtDBError as e:
    raise SystemExit(sys.argv[0] + ': ' + str(e))
