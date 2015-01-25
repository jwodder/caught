- Document everything!
- `CaughtDB`:
    - Add a method for getting a list of all Pokémon and their statuses for a
      given game
    - Add a method for getting a range of Pokémon & statuses for a given game?
    - Should `setStatus` check its `status` argument for validity?
    - Add a `getPokemonByDexno` method
    - `newGame` should take an argument to control whether a
      `version:playername[:N]` altname is created
    - `newGame` should take an argument to control whether duplicate altnames
      should be ignored instead of causing an error
    - Add a `getGameByName` method that (unlike `getGame`) only searches the
      `game_names` table (and add an option to `caught.py` for making use of
      it)
    - Should `create` ensure the dexnos are all positive & contiguous?
    - Try to make `create` rollback the CREATE TABLE statements (not just the
      INSERT statements) when an INSERT fails

- `caught.py`:
    - Intended command-line usages to implement:

        caught list status game [pokemon|dexno|dexno_range ...]
        # Statuses:
        # - uncaught
        # - caught
        # - caught+ - equivalent to `caught/owned`
        # - owned
        # - status1/status2 - all Pokémon with either status
        # - status1/status2/status3 - all Pokémon (just for completeness's sake)

        caught get game [pokemon|dexno|dexno_range ...]

        caught getall [--games game1,game2]  # List all Pokémon in all games in a table
        caught getall [--games game1,game2] pokemon|dexno|dexno_range ...

        caught update tsvfile  # add more Pokémon

        caught export [-o file] [game ...]
        # Exports all games by default (as JSON?)

        caught import [file | -]

    - Add functionality for automatically backing up the database?
        - Idea: Add a program-wide option for backing up the database before
          performing any operations, and add a command for restoring from a
          backup
    - Fill in 'help', 'metavar', and other help message-related values for
      argparse
    - Give all of the commands that take a list of Pokémon an `-F file` option
      for reading the list from a file instead
    - Add a command for showing all information about a specific game (or
      Pokémon?)
    - Give `new` an option to turn off creation of the `version:playername[:N]`
      altname
    - Give `new` an option to ignore altnames that already exist
    - Give `new` an option for setting the game ID?
    - Let the `games` command take an optional list of games to describe

- Add functionality (accessed through caught.py or another program?) for
  extending/updating the Pokédex
- Should CaughtDB and/or caught.py raise an error when trying to set the status
  for a Pokémon that is beyond a game's dexsize?
- Add support for keeping track of Unown forms
- Add support for regional Pokédexes
- Add commands & methods for adding & removing game altnames?
- Merge `mkcaughtdb.py` into `caught.py` (and then merge `caughtdb.py` back
  into `caught.py`) ?
- Make the `dbfile` argument to `mkcaughtdb.py` optional
- Rethink whether each Pokémon should have its dexno as an altname
- Add a table (and a TSV file) listing possible versions and their
  corresponding dexsizes (and, eventually, regional dexes)
- Generalize the code into being able to track completion of sets
  (corresponding to games) of arbitrary checklists
- Rename "altnames" to "synonyms"
- Should the first game to have a `version:player` name also have
  `version:player:1`?  If so, should `version:player` be automatically
  reassigned to the newest game with those parameters whenever such a game is
  created?
- TO IMPLEMENT: When looking up a game by name, if there exists a `game_names`
  entry for that name, it is used.  Otherwise, all games whose `version` and/or
  `player_name` equals the supplied string are queried; if there is exactly
  one, it is used, otherwise it is an error.
- Instead of the version+player_name+altnames system, each game should have a
  single canonical name (which is used in the headings of tabular output) and
  zero or more altnames, with 'version' and 'player_name' being (optional?)
  extra fields that are not used in naming and simply describe the game further
  (and can be searched, e.g., getting all Diamond games?)
