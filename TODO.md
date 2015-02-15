- Document everything!
- Make the code pass pylint
- `CaughtDB`:
    - Add a `getPokemonByDexno` method
    - Should `create` ensure the dexnos are all positive & contiguous?
    - Try to make `create` rollback the CREATE TABLE statements (not just the
      INSERT statements) when an INSERT fails
    - Let `create` use either a TSV file or JSON file as the Pokédex
    - Should more SQL calls be given custom types for their exceptions?  (At
      the very least, those that can propagate to the top of caught.py during
      normal execution should be more end-user friendly)
    - Add a method for testing whether `create` has been run on the DB
    - `newGame` should probably take a `Game` as its argument
    - The `synonyms` attributes of Game and Pokemon objects should not include
      the canonical name (or, for Pokemon, the dexno)
    - Should `getGame` fall back to looking up by gameID if no name is found?
    - When `getGame` is called, if there exists a `game_names` entry for that
      name, that should be returned.  Otherwise, all games whose `version`
      and/or `player_name` fields equal the supplied string are queried; if
      there is exactly one, it is returned, otherwise it is an error.
        - Add a `getGameByName` method that only searches the `game_names`
          table (and add an option to `caught.py` for making use of it)

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

        caught update tsvfile|jsonfile  # add more Pokémon

        caught export [-o file] [game ...]
        # Exports all games by default (as JSON?)

        caught import [file | -]

    - Add functionality for automatically backing up the database?
        - Idea: Add a program-wide option for backing up the database before
          performing any operations, and add a command for restoring from a
          backup
    - Fill in 'help', 'metavar', and other help message-related values for
      argparse
    - Add a command for showing all information about a specific Pokémon?
    - Give `new` an option for setting the game ID?
    - Rename `new` to "`newgame`"?
    - Make warning and error messages look less alike
    - Give the `add` family a "verbose" option to make them print out each
      specified Pokémon's previous status and whether or not a change was made
    - Let `getall` take multiple `--games` switches (and/or multiple `--game`
      switches, allowing it to subsume `get`?)
    - Improve the output of `getall`
        - Handle padding with non-ASCII characters
    - Rename the `-G` option
    - Let the `add` family, `get`, and `getall` take Pokémon specifications as
      species names, dexnos, or ranges (given as two species and/or dexnos
      separated by a hyphen)

- Add functionality for extending/updating the Pokédex
- Should CaughtDB and/or caught.py raise an error when trying to set the status
  for a Pokémon that is beyond a game's dexsize?
- Add support for keeping track of Unown forms
- Add support for regional Pokédexes
- Add a "seen" status
- Add commands & methods for adding & removing game synonyms
- Add functionality for changing a game's canonical name, version, and player
  name (and dexsize?)
- Merge `caughtdb.py` back into `caught.py`
- Rethink whether each Pokémon should have its dexno as an synonym
- Add a table (and a TSV file) listing possible versions and their
  corresponding dexsizes (and, eventually, regional dexes)
- Add functionality for getting games by version & player name

- Generalize the code into being able to track completion of sets
  (corresponding to games) of arbitrary checklists
