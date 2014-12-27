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
- Add functionality (accessed through caught.py or another program?) for
  extending/updating the Pokédex
