- `CaughtDB`:
    - Add a `newGame` method:

        def newGame(self, version, player_name, dexsize, altnames)

    - Add a method for getting a list of all Pokémon and their statuses for a
      given game
    - Add a method for getting a range of Pokémon & statuses for a given game?
    - Should `setStatus` check its `status` argument for validity?
    - Move to a module? (along with `Game` and `Pokemon`)
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

- Add functionality (accessed through caught.py or another program?) for
  extending/updating the Pokédex
- `mkcaughtdb.py`: Try to make the program rollback the CREATE TABLE statements
  (not just the INSERT statements) when an INSERT fails
- Should CaughtDB and/or caught.py raise an error when trying to set the status
  for a Pokémon that is beyond a game's dexsize?
- Add support for keeping track of Unown forms
- pokemon_names should include the dexno as an altname
- Add support for regional Pokédexes
