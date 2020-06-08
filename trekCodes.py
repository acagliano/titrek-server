
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

OutboundCodes = {
    "REGISTER":0,
    "LOGIN":1,
    "DISCONNECT":2,
    "PING":0x000d,
    "MESSAGE":0x000e,
    "DEBUG":0x000f,
    "SERVINFO":0x00ff
}

InboundCodes = {
    "REGISTER":0,
    "LOGIN":1,
    "DISCONNECT":2,
    "PLAYER_MOV":3,
    "CHUNK_REQ":4,
    "PING":0x000d,
    "MESSAGE":0x000e,
    "DEBUG":0x00ff
}

#returned from the registration and login routines
ResponseCodes = {
    "SUCCESS":0,
    "INVALID":1,
    "DUPLICATE":2,
    "MISSING":3,
    "BANNED":4,
    "VERSION_MISMATCH":5
}

