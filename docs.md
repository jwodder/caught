## Very Rough Documentation

### Command-line functionality already implemented

- The `-D`/`--dbfile` and `-G` global options
- By default, "game" arguments that are all digits are interpreted as game IDs,
  unless the program-wide option `-G` is supplied, which forces them to be
  interpreted as regular names.

    caught new version playername dexsize [synonyms ...]

    caught games [-Js] [game ...]
    # Output is in YAML just to make some attempt at parseability
    # `-J` causes output to be JSON instead
    # `-s` causes dex progress to be printed

    caught add game pokemon ...       # uncaught → caught
    caught own game pokemon ...       # * → owned
    caught release game pokemon ...   # owned → caught
    caught uncaught game pokemon ...  # * → uncaught

    caught get game [pokemon ...]

### On game names

- Creating a game entry with version `version` and player name `player` creates
  a `game_names` entry `version:player`; if such an entry already exists, the
  new `game_names` entry is instead named `version:player:N`, where `N` is the
  number of `game_names` entries of the form `/^version:player(:.*)?$/` already
  present.  Neither `version` nor `player` is added to `game_names` unless it
  explicitly appears in the "synonyms" list for the game creation command.
