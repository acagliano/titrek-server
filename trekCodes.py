
#TITrek server python3
#Authors:
# Anthony "ACagliano" Cagliano
# Adam "beckadamtheinventor" Beckingham
#These are the response/message/error dictionaries for Star Trek CE.

#This file is external from the main server file so it can be used in multiple programs.
##This code will import everything from this file without the need to prepend the namespace "trekCodes"
##[code]
##  from trekCodes import *
##[/code]

#These are mostly used for mnemonics

ControlCodes = {
    "REGISTER":0,
    "LOGIN":1,
    "DISCONNECT":2,
    "PLAYER_MOV":3,
    "CHUNK_REQ":4,
#returned from the registration and login routines
    "SUCCESS":0xd0,
    "INVALID":0xd1,
    "DUPLICATE":0xd2,
    "MISSING":0xd3,
    "BANNED":0xd4,
    "VERSION_MISMATCH":0xd5,
#Message codes
    "PING":0xfc,
    "MESSAGE":0xfd,
    "DEBUG":0xfe,
    "SERVINFO":0xff
}

