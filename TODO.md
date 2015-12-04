- Document everything!
- Make the code pass pylint
- Enforce UTF-8 throughout the code
- `CaughtDB`:
    - Should `create` ensure the dexnos are all positive & contiguous?
    - Try to make `create` rollback the CREATE TABLE statements (not just the
      INSERT statements) when an INSERT fails
    - Let `create` use either a TSV file or JSON file as the Pokédex
    - Should more SQL calls be given custom types for their exceptions?  (At
      the very least, those that can propagate to the top of `caught.py` during
      normal execution should be more end-user friendly)
    - Add a method for testing whether `create` has been run on the DB
    - Should `getGame` fall back to looking up by gameID if no name is found?
    - When `getGame` is called, if there exists a `game_names` entry for that
      name, that should be returned.  Otherwise, all games whose `version`
      and/or `player_name` fields equal the supplied string are queried; if
      there is exactly one, it is returned, otherwise it is an error.
        - Add a `getGameByName` method that only searches the `game_names`
          table (and add an option to `caught.py` for making use of it)
    - `create` and `newGame` need to roll back partial changes if an exception
      is raised in the middle of execution
    - Add a method and/or DB constraint for ensuring there are no `UNCAUGHT`
      entries in `caught`

- `caught.py`:
    - Commands to implement:

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
        - cf. <http://stackoverflow.com/a/28908244/744178>
    - Add a command for showing all information about a specific Pokémon?
    - Let `get` take multiple `--games` switches?
    - Rename the `-G` option
    - Give `new` an option for automatically making the version and player name
      synonyms of the game
    - Make `list` take an optional set of Pokémon to restrict itself to
    - Add a tabular output mode for `games`?
        - Make the output be tabular by default and get rid of YAML support

- The `synonyms` attributes of Game and Pokemon objects should not include the
  canonical name (or, for Pokemon, the dexno)
- Add functionality for extending/updating the Pokédex
- CaughtDB and/or caught.py should raise an error when trying to set the status
  for a Pokémon that is beyond a game's dexsize
- Add support for keeping track of Unown forms
- Add support for regional Pokédexes
- Add a "seen" status
- Add commands & methods for adding & removing game synonyms
- Add functionality for changing a game's canonical name, version, and player
  name (and dexsize?)
- Merge `caughtdb.py` back into `caught.py`
- Rethink whether each Pokémon should have its dexno as an synonym
- Add a table (and a TSV file) listing possible versions and their
  corresponding dexsizes (and, eventually, regional dexes and generations)
- Add functionality for getting games by version & player name (and generation)
- Override `Game.__new__` and `Pokemon.__new__` (and `Status.__new__`?) so that
  the `synonyms` fields are always sorted tuples of stripped(?) lowercase
  strings (and so that `dexsize` is always an integer?)
- Give `Status` (and `Pokemon` and `Game`?) an `__eq__` method that allows for
  comparison with integers
- Add support for event Pokémon that are not needed for completing the Pokédex?
- Sidestep the whole "force_gname" thing by prohibiting using numbers as game
  names?
- Eliminate the `pokemon` & `pokemon_names` tables and the dependency on
  external TSVs and just hardcode the Pokédex into the source code?
    - Get rid of the `create` command and have `caught.py` implicitly call
      `create` whenever it is used on a new dbfile

- Generalize the code into being able to track completion of sets
  (corresponding to games) of arbitrary checklists
