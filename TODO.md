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

        caught [-D dbfile] new version playername dexsize [altnames ...]
        # Add option to turn off creation of `version:playername[:N]` altname
        # Add option to ignore altnames that already exist
        # Add an option for setting the game ID?

        caught [-D dbfile] add game pokemon ...       # uncaught → caught
        caught [-D dbfile] own game pokemon ...       # * → owned
        caught [-D dbfile] release game pokemon ...   # owned → caught
        caught [-D dbfile] uncaught game pokemon ...  # * → uncaught

        caught [-D dbfile] games [-s]  # `-s` causes dex progress to be printed
        # output is in YAML just to make some attempt at parseability
        # TODO: Add a `-J` option for outputting JSON

	caught [-D dbfile] list status game [pokemon|dexno|dexno_range ...]

        # Rename `table` to `get`?
        caught [-D dbfile] table game[,game...]  # List all Pokémon up through maximum `dexsize`
        caught [-D dbfile] table game[,game...] pokemon|dexno|dexno_range ...
        caught [-D dbfile] table -A  # List all Pokémon in all games in a table
        caught [-D dbfile] table -A pokemon|dexno|dexno_range ...

        caught [-D dbfile] update tsvfile  # add more Pokémon

        caught [-D dbfile] export [-o file] [game ...]
        # Exports all games by default (as JSON?)

        caught [-D dbfile] import [file | -]

    - By default, "game" arguments that are all digits are interpreted as game
      IDs, unless the program-wide option `-G` is supplied, which forces them
      to be interpreted as regular names.
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
- Add functionality (accessed through caught.py or another program?) for
  extending/updating the Pokédex
- Should CaughtDB and/or caught.py raise an error when trying to set the status
  for a Pokémon that is beyond a game's dexsize?
- Add support for keeping track of Unown forms
- Add support for regional Pokédexes
- Add commands & methods for adding & removing game altnames?
- Add commands & methods for deleting games
- Merge `mkcaughtdb.py` into `caught.py` (and then merge `caughtdb.py` back
  into `caught.py`) ?
- Make the `dbfile` argument to `mkcaughtdb.py` optional
- Rethink whether each Pokémon should have its dexno as an altname
- Add a table (and a TSV file) listing possible versions and their
  corresponding dexsizes (and, eventually, regional dexes)
- Generalize the code into being able to track completion of sets
  (corresponding to games) of arbitrary checklists

- Possible way to handle game names:
    - Creating a game entry with version `version` and player name `player`
      creates a `game_names` entry `version:player`; if such an entry already
      exists, the new `game_names` entry is instead named `version:player:N`,
      where `N` is the number of `game_names` entries of the form
      `/^version:player(:.*)?$/` already present.  Neither `version` nor
      `player` is added to `game_names` unless it explicitly appears in the
      "altnames" list for the game creation command.
        - Should the first game to have a `version:player` name also have
          `version:player:1`?  If so, should `version:player` be automatically
          reassigned to the newest game with those parameters whenever such a
          game is created?
    - TO IMPLEMENT: When looking up a game by name, if there exists a
      `game_names` entry for that name, it is used.  Otherwise, all games whose
      `version` and/or `player_name` equals the supplied string are queried; if
      there is exactly one, it is used, otherwise it is an error.
