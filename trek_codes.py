
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
    "PRGMUPDATE":3,
    "GFXUPDATE":4,
    "LOAD_SHIP":5,
    "MODULE_REQUEST":6,
    "MODULE_UPDATE":7,
    "CHUNK_REQUEST":8,
    "ENTITY_REQUEST":9,
    "SENSOR_REQUEST":10, #May add REQPOSITION if needed
    "NEW_GAME_REQUEST":11,
#Message codes
    "PING":0xfc,
    "MESSAGE":0xfd,
    "DEBUG":0xfe,
    "SERVINFO":0xff
}

ResponseCodes = {
    "SUCCESS":0x0,
    "INVALID":0x1,
    "DUPLICATE":0x2,
    "MISSING":0x3,
    "BANNED":0x4,
    "VERSION_MISMATCH":0x5,
}
