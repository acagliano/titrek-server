
# This file is the beginning of a self-contained, custom firewall
# for the TI-Trek server. It uses a JSON rules file, containing
# check names, methods, and actions.

# "check" name of the test to be done
#  -----(also the name of the file in which the method can be found)
# "method" the self.method to call to perform the check
# "failaction" the action to take should the packet fail the check
# Might add the ability to pass a format specifier to the filter, such that our sanity checks...
# ... can know what type of data to expect in different packet segments

# Not yet implemented, but this module will be designed as a class
# that can be invoked optionally, should a user wish to provide it on their own server

import os,json,traceback,importlib,logging
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler
from trek.codes import *
from trek.utils.logging import TrekLogging

logging.FILTER=60

PacketSizes={
    "LOGIN":128+16+16,
    "GET_ENGINE_MAXIMUMS":0,
    "MODULE_STATE_CHANGE":2,
    "MODULE_INFO_REQUEST":1,
    "ENGINE_SETSPEED":4,
    "LOAD_SHIP":0
}

TextOnlyPackets={

}

class TrekFilter:
	special_characters = [bytes(a,'UTF-8') for a in ["/","\\","#","$","%","^","&","*","!","~","`","\"","|"]] + \
					[bytes([a]) for a in range(1,0x20)] + [bytes([a]) for a in range(0x7F,0xFF)]
	packet_names = list(ControlCodes.keys())
	packet_values = list(ControlCodes.values())

	def __init__(self, server):
	# not really much to do here.
		self.server=server
		logging.addLevelName(logging.FILTER, "FILTER")
		return
	
	
	def filter_packet(self,client,data):
		try:
			self.server.log(f"Checking packet {data[0]} from {client.addr[0]}")
			if self.invalid_size(data):
				self.server.logger.log(logging.FILTER, f"Suspect packet from {client.addr[0]} intercepted. Reason: invalid size")
				return False
			if self.restricted_ids(client, data):
				self.server.logger.log(logging.FILTER, f"Suspect packet from {client.addr[0]} intercepted. Reason: unpriviledged client attempting to use priviledged packet IDs")
				return False
			if self.special_chars(data):
				self.server.logger.log(logging.FILTER, f"Suspect packet from {client.addr[0]} intercepted. Reason: non-text characters in text-only data segment")
				return False

			return True
            
			
		except:
			self.server.elog(traceback.print_exc(limit=None, file=None, chain=True))
			return

	def invalid_size(self, data):
		position = TrekFilter.packet_values.index(data[0])
		key = TrekFilter.packet_names[position]
		if key in PacketSizes:
			if (len(data)-1) == PacketSizes[key]:
				return False
			else:
				return True
		else: return False

	def restricted_ids(self, client, data):
		if client.logged_in:
			return False
		if(data[0] > 9):
			return True

	def special_chars(self, data):
		position = TrekFilter.packet_values.index(data[0])
		key = TrekFilter.packet_names[position]
		if key in TextOnlyPackets:
			segment = data[TextOnlyPackets[key]["start"]:TextOnlyPackets[key]["stop"]]
			if any([a in segment for a in TrekFilter.special_characters]):
				return True
			else:
				return False
		else: return False
