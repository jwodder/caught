- `CaughtDB`:
    - Add a method for getting a list of all Pokémon and their statuses for a
      given game
    - Add a method for getting a range of Pokémon & statuses for a given game?
    - Should `setStatus` check its `status` argument for validity?
    - Move to a module? (along with `Game` and `Pokemon`)
    - Add `commit` and `rollback` methods
    - Add `getPokemonByDexno` and `getGameById` methods
    - Add variants of `setStatus` that perform the following specific
      transitions:

        - uncaught → caught
        - uncaught or caught → owned
        - owned → caught

      If the specified `(game, poke)` pair is not in the appropriate initial
      state, the method does nothing and returns `False`; otherwise, the status
      is updated and `True` is returned.

- `caught.py`:
    - Add command-line options for setting statuses to "owned" and "uncaught"
    - In its default mode of marking Pokémon "caught", caught.py should not
      change the status of Pokémon marked "owned" unless an `-f` option is
      given
    - Add an option for specifying the database file
    - Add an option for making a new game
    - Add options for displaying statuses
    - Possible command-line usages:

        caught [-D dbfile] new version playername dexsize [altnames ...]

        caught [-D dbfile] add [-f] game pokemon ...
        caught [-D dbfile] own [-f] game pokemon ...

        # to undo an 'add'/'own', i.e., to mark as uncaught/caught
        caught [-D dbfile] add -u [-f] game pokemon ...
        caught [-D dbfile] own -u [-f] game pokemon ...

        caught [-D dbfile] games
        caught [-D dbfile] list game  # List all Pokémon up through `dexsize`
        caught [-D dbfile] list game pokemon|dexno|dexno_range ...
        caught [-D dbfile] listall  # List all Pokémon in all games in a table

        caught [-D dbfile] update tsvfile  # add more Pokémon

        caught [-D dbfile] export [game ...]  # Exports all games by default
        caught [-D dbfile] import [file]

    - All commands that take a "game" argument can alternatively have the game
      specified by a `-g gameID` option (or just take a bare `-g` option that
      forces the "game" argument to be interpreted as a `gameID`?)
    - Add functionality for automatically backing up the database?
    - Add commands for listing all Pokémon in a game with a given status
- Add functionality (accessed through caught.py or another program?) for
  extending/updating the Pokédex
- `mkcaughtdb.py`: Try to make the program rollback the CREATE TABLE statements
  (not just the INSERT statements) when an INSERT fails
- Should CaughtDB and/or caught.py raise an error when trying to set the status
  for a Pokémon that is beyond a game's dexsize?
- Add support for keeping track of Unown forms
- Add support for regional Pokédexes
- Add commands & methods for adding & removing game altnames
- The "new game" command and method should both have options/arguments for
  ignoring altnames that are already in use

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
