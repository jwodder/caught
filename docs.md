## Very Rough Documentation

### Command-line functionality already implemented

- The `-D`/`--dbfile` and `-G` global options

    caught new version playername dexsize [altnames ...]

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
  explicitly appears in the "altnames" list for the game creation command.
