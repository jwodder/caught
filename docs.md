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

    caught add      game [-F | --file file] pokemon ...  # uncaught → caught
    caught own      game [-F | --file file] pokemon ...  # * → owned
    caught release  game [-F | --file file] pokemon ...  # owned → caught
    caught uncaught game [-F | --file file] pokemon ...  # * → uncaught

    caught get      game [-F | --file file] [pokemon ...]
