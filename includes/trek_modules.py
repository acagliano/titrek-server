
# modules.py
#Ship modules

import json

def IMPORT(fname):
	with open(fname) as f:
		return json.load(f)

def loadModule(module,level):
	try:
		return IMPORT("module/"+fname+"_L"+str(level)+".json")
	except:
		return None

