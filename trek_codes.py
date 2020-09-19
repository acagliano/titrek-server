
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
    
    # CONNECTION/ADMIN
    # 0 - 9
    "REGISTER":0,
    "LOGIN":1,
    "DISCONNECT":2,
    "VERSION_MISMATCH":3,   # This is for the client not up to date response , See response codes. VERSION_* must be the second byte of packet
    
    # GAMEPLAY
    # Map Interfacing: 10 - 19 
    "FRAMEDATA_REQUEST":10,
    "SENSOR_DATA_REQUEST":11, #May add REQPOSITION if needed
    "PLAYER_MOVE":12,
    "POSITION_REQUEST":13,
    
    # Ship Interfacing: 20 - 29
    "LOAD_SHIP":20,
    "MODULE_INFO_REQUEST":21,
    "MODULE_STATE_CHANGE":22,
    "NEW_GAME_REQUEST":23,
    
    # File Streaming: 90 - 91
    "PRGMUPDATE":90,
    "GFXUPDATE":91,
    
    # DEBUG: 0xf*
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
    "VERSION_ERROR":0x5,    # This will produce a blocking error on client saying (1) update, or (2) disconnect
    "VERSION_OUTDATED":0x6,     # this will show a non-blocking error on client letting you update or proceed.
    "BAD_MESSAGE_CONTENT":0x7,
}
