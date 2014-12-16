#!/usr/bin/python
# -*- coding: utf-8 -*-
from   collections import namedtuple
import os
import sqlite3

dbfile = os.environ["HOME"] + 'share/caught.db'

class Caught(object):
    UNCAUGHT = 0
    CAUGHT   = 1
    OWNED    = 2

    def __init__(self, dbpath):
	self.db = sqlite3.connect(dbpath)

    def getPokemon(self, name):
	"""Returns the Pokédex number for the Pokémon with the given name, or
	   ``None`` if there is no such Pokémon"""
        ???

    def getGame(self, name):
	"""Returns the ID number for the game with the given name, or ``None``
	   if there is no such game"""
        ???

    def getStatus(self, gameID, pokeID)
    def setStatus(self, gameID, pokeID, status)  # returns a boolean for whether there was a change?

    def newGame(self, name, dexsize, altnames)
    def getGameData(self, gameID)  # returns canonical name and dex size
    def getGameCount(self, gameID)  # returns number of Pokémon caught & owned (and dexsize?)

    def getPokemon(self, pokeID)  # returns canonical name

    def allGames(self)
    def allPokémon(self, maxno=None)

    # method for getting a list of all Pokémon for a given game
    # method for getting a range/set of Pokémon for a given game?


Game    = namedtuple('Game', 'gameID name dexsize altnames')
Pokemon = namedtuple('Pokemon', 'pokeID name altnames')
