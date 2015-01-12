- Document everything!
- `CaughtDB`:
    - Add a method for getting a list of all Pokémon and their statuses for a
      given game
    - Add a method for getting a range of Pokémon & statuses for a given game?
    - Should `setStatus` check its `status` argument for validity?
    - Add `commit` and `rollback` methods
    - Add `getPokemonByDexno` and `getGameById` methods
    - `newGame` should return a complete `Game` object
    - `newGame` should take an argument to control whether a
      `version:playername[:N]` altname is created
    - `newGame` should take an argument to control whether duplicate altnames
      should be ignored instead of causing an error
    - Add a `getGameByName` method that (unlike `getGame`) only searches the
      `game_names` table (and add an option to `caught.py` for making use of
      it)

- `caught.py`:
    - Intended command-line usages to implement:

        caught [-D dbfile] new version playername dexsize [altnames ...]
        # Add option to turn off creation of `version:playername[:N]` altname
        # Add option to ignore altnames that already exist

        caught [-D dbfile] add game pokemon ...       # uncaught → caught
        caught [-D dbfile] own game pokemon ...       # * → owned
        caught [-D dbfile] release game pokemon ...   # owned → caught
        caught [-D dbfile] uncaught game pokemon ...  # * → uncaught

        caught [-D dbfile] games [-q]  # `-q` causes dex progress to be printed

	caught [-D dbfile] list status game [pokemon|dexno|dexno_range ...]

        caught [-D dbfile] table game[,game...]  # List all Pokémon up through maximum `dexsize`
        caught [-D dbfile] table game[,game...] pokemon|dexno|dexno_range ...
        caught [-D dbfile] table -A  # List all Pokémon in all games in a table
        caught [-D dbfile] table -A pokemon|dexno|dexno_range ...

        caught [-D dbfile] update tsvfile  # add more Pokémon

        caught [-D dbfile] export [-o file] [game ...]  # Exports all games by default
        caught [-D dbfile] import [file | -]

    - By default, "game" arguments that are all digits are interpreted as game
      IDs, unless the program-wide option `-G` is supplied, which forces them
      to be interpreted as regular names.
    - Add functionality for automatically backing up the database?
        - Idea: Add a program-wide option for backing up the database before
          performing any operations, and add a command for restoring from a
          backup
- Add functionality (accessed through caught.py or another program?) for
  extending/updating the Pokédex
- `mkcaughtdb.py`: Try to make the program rollback the CREATE TABLE statements
  (not just the INSERT statements) when an INSERT fails
- Should CaughtDB and/or caught.py raise an error when trying to set the status
  for a Pokémon that is beyond a game's dexsize?
- Add support for keeping track of Unown forms
- Add support for regional Pokédexes
- Add commands & methods for adding & removing game altnames?
- Make most of `mkcaughtdb.py` into a method of `CaughtDB`
- Add commands & methods for deleting games

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
    - Upon successful completion, `caught new` prints out the new game's
      `gameID` and all `game_names` entries.
    - When looking up a game by name, if there exists a `game_names` entry for
      that name, it is used.  Otherwise, all games whose `version` and/or
      `player_name` equals the supplied string are queried; if there is exactly
      one, it is used, otherwise it is an error.
