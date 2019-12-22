
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

#returned from user input
InputError={
    "success":b'\000',
    "invalid":b'\001',
    "duplicate":b'\002',
    "missing":b'\003'
}
#returned from the registration routine
RegisterError={
    "success":b'\000\001\000',
    "invalid":b'\000\001\001',
    "duplicate":b'\000\001\002',
    "missing":b'\000\001\003',
    "banned":b'\000\002\004'
}
#returned from the login routine
LoginError={
    "success":b'\000\002\000',
    "invalid":b'\000\002\001',
    "duplicate":b'\000\002\002',
    "missing":b'\000\002\003',
    "banned":b'\000\002\004'
}
#returned from the disconect routine
DisconnectError={
    "success":b'\000\003\000'
}
#server control codes
ControlCode={
    "servresponse":b'\000',
    "register":b'\001',
    "login":b'\002',
    "disconnect":b'\003',
    "ping":b'\00d',
    "message":b'\00e',
    "debug":b'\00f',
    "servinfo":b'\0ff'
}
#server response codes. The same as server control codes for simplicity.
ResponseCodes={
    "register":b'\000\001',
    "login":b'\000\002',
    "disconnect":b'\000\003',
    "ping":b'\00d',
    "message":b'\000\00e',
    "debug":b'\000\00f',
    "servinfo":b'\000\0ff'
}

