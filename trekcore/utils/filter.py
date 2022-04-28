
# This file is a self-contained custom packet filter firewall for the TI-Trek service.
# It has 3 packet check modes:
# 	<> Validate packet size
#	<> Unpriviledged client accessing priviledged packet IDs
#	<> Special characters in text-only packet segments
# A packet failing any of these three checks triggers a Filter event.
# A packet triggering a filter event causes the immediate disconnect of the offending client.
# The offense is logged to the server logfile.
# There is a fail2ban jail that can ban repeat offenders.

import os,json,traceback,importlib,logging
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler
from trekcore.codes import *
from trekcore.utils.logging import TrekLogging

logging.FILTER=60

PacketSizes={
    "LOGIN":128+16+16,
    "GET_ENGINE_MAXIMUMS":0,
    "MODULE_STATE_CHANGE":2,
    "MODULE_INFO_REQUEST":1,
    "ENGINE_SETSPEED":4,
    "LOAD_SHIP":0
}

UnprivPackets={
	"LOGIN",
	"REGISTER",
	"MAIN_REQ_UPDATE",
	"MAIN_FRAME_NEXT",
	"REQ_SECURE_SESSION",
	"RSA_SEND_SESSION_KEY",
	"PING"
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
			if not data[0] in ControlCodes:
				self.server.logger.log(logging.FILTER, f"Suspect packet from {client.addr[0]} intercepted. Reason: unregistered packet type")
				client.send([ControlCodes["DEBUG"]]+list(bytes("Unregistered packet. ID:"+data[0]+'\0', 'UTF-8')))
				return False
			if self.invalid_size(data):
				self.server.logger.log(logging.FILTER, f"Suspect packet from {client.addr[0]} intercepted. Reason: invalid size")
				client.send([ControlCodes["DEBUG"]]+list(bytes("Packet size err. ID:"+data[0]+'\0', 'UTF-8')))
				return False
			if self.restricted_ids(client, data):
				self.server.logger.log(logging.FILTER, f"Suspect packet from {client.addr[0]} intercepted. Reason: unpriviledged client attempting to use priviledged packet IDs")
				client.send([ControlCodes["DEBUG"]]+list(bytes("Packet permission err. ID:"+data[0]+'\0', 'UTF-8')))
				return False
			if self.special_chars(data):
				self.server.logger.log(logging.FILTER, f"Suspect packet from {client.addr[0]} intercepted. Reason: non-text characters in text-only data segment")
				client.send([ControlCodes["DEBUG"]]+list(bytes("Packet invalid text field err. ID:"+data[0]+'\0', 'UTF-8')))
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
		position = TrekFilter.packet_values.index(data[0])
		key = TrekFilter.packet_names[position]
		if (key in UnprivPackets) or client.logged_in:
			return False
		else:
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
