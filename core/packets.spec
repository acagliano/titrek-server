# Default packet spec list
# Do not modify. It will break core functionality.

# login system, encryption setup
SEND_RSA_KEY:
	id: 0x02
	func: "rsa_send"
RECV_AES_KEY:
	id: 0x03
	func: "aes_recv"
RECV_LOGIN_TOKEN:
	id: 0x04
	func: "login"

# ship interfacing
LOAD_SHIP:
	id: 0x10
	req-login: true
	func: "load_ship"
MODULE_INFO:
	id: 0x11
	req-login: true
	func: "module_info"
MODULE_CONFIG:
	id: 0x12
	req-login: true
	func: "module_config"

# File Streaming: 0xe*
GFX_FCHECK:
	id: 0xe0
	req-login: true
	func: "gfx_fcheck"
GFX_FSTART:
	id: 0xe1
	req-login: true
	func: "gfx_fstart"
GFX_FREAD:
	id: 0xe2
	req-login: true
	func: "gfx_fread"
GFX_FNEXT:
	id: 0xe3
	req-login: true
	func: "gfx_fnext"
GFX_FDONE:
	id: 0xe4
	req-login: true
	func: "gfx_fdone"
GFX_FSKIP:
	id: 0xe5
	req-login: true
	func: "gfx_fskip"

CLIENT_FCHECK:
	id: 0xe6
	func: "client_fcheck"
CLIENT_FSTART:
	id: 0xe7
	func: "client_fstart"
CLIENT_FREAD:
	id: 0xe8
	func: "client_fread"
CLIENT_FNEXT:
	id: 0xe9
	func: "client_fnext"
CLIENT_FDONE:
	id: 0xea
	func: "client_fdone"
CLIENT_FSKIP:
	id: 0xeb
	func: "client_fskip"






