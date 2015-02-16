## Very Rough Documentation

### Command-line functionality already implemented

- The `-D`/`--dbfile` and `-G` global options
- By default, "game" arguments that are all digits are interpreted as game IDs,
  unless the program-wide option `-G` is supplied, which forces them to be
  interpreted as regular names.

    caught create pokedex

    caught new [-i | --ignore-dups]
               [--version version]
               [--player-name | --player player-name]
               name dexsize [synonyms ...]

    caught delete [-f | --force] game ...

    caught games [-J | --json] [-s | --stats] [game ...]
    # Output is in YAML just to make some attempt at parseability
    # `-J` causes output to be JSON instead
    # `-s` causes dex progress to be printed

    caught add      [-F | --file file] game pokemon ...  # uncaught → caught
    caught own      [-F | --file file] game pokemon ...  # * → owned
    caught release  [-F | --file file] game pokemon ...  # owned → caught
    caught uncaught [-F | --file file] game pokemon ...  # * → uncaught

    caught get      [-F | --file file] game [pokemon ...]

    caught getall [--games game1,game2]  [-F | --file file] [pokemon ...]

    caught list status game
    # Statuses:
    # - uncaught
    # - caught
    # - caught+ - equivalent to `caught/owned`
    # - owned
    # - unowned - equivalent to `uncaught/caught`
    # - status1/status2 - all Pokémon with either status
    # - status1/status2/status3 - all Pokémon (just for completeness's sake)
