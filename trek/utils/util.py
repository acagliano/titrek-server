import os
import os.path

class Binaries:
	def __init__(self, loggers, path, repo_link, binary):
		try:
			parent, new = os.path.split(path)
			self.path=path
			try:
				os.makedirs(path)
				os.system(f"cd {parent} && git clone {repo_link}")
				os.system(f"cd {path} && git submodule update --init --recursive && make")
				if path.exists(f"{path}bin/{binary}"):
					self.log(f"{repo_link} fetched and built")
					self.bin=f"{path}bin/{binary}"
			except:
				self.update(path)
		except:
			sys.exit("Error loading needed binaries")			
				
	def update(self, path):
		try:
			os.system(f"cd {path} && git pull && make")
			if path.exists(f"{path}bin/{binary}"):
				self.log(f"{path} successfully updated")
				self.bin=f"{path}bin/{binary}"
		except:
			self.elog(traceback.format_exc(limit=None, chain=True))
	
	def run(self):
		return os.popen(self.bin)


def ToUTF8(dt):
	if b"\0" in dt:
		return str(bytes(dt[:dt.find(b"\0")]),'UTF-8')
	return str(bytes(dt),'UTF-8')

def FromSignedInt(n):
	if n&0x80:
		return -(0x80-(n&0x7F))
	else:
		return n

def ToSignedByte(n):
	if n<0:
		return 0x100-(abs(n)&0x7F)
	else:
		return n&0x7F

def i24(*args):
	o=[]
	for arg in args:
		if int(arg)>0:
			o.extend(list(int(arg).to_bytes(3,'little')))
		else:
			o.extend(list((0-abs(int(arg))&0x7FFFFF).to_bytes(3,'little')))
	return o

def u32(*args):
	o=[]
	for arg in args:
		if int(arg)<0: arg = abs(int(arg))
		else: arg = int(arg)
		o.extend(list(int(arg).to_bytes(4,'little')))
	return o

def u24(*args):
	o=[]
	for arg in args:
		if int(arg)<0: arg = abs(int(arg))
		else: arg = int(arg)
		o.extend(list(int(arg).to_bytes(3,'little')))
	return o

def i16(*args):
	o=[]
	for arg in args:
		if int(arg)>0:
			o.extend(list(int(arg).to_bytes(2,'little')))
		else:
			o.extend(list((0-abs(int(arg))&0x7FFF).to_bytes(2,'little')))
	return o

def u16(*args):
	o=[]
	for arg in args:
		if int(arg)<0: arg = abs(int(arg))
		else: arg = int(arg)
		o.extend(list(int(arg).to_bytes(2,'little')))
	return o

def i8(*args):
	o=[]
	for arg in args:
		if int(arg)>0:
			o.append(int(arg)&0xFF)
		else:
			o.append((0-abs(int(arg))&0x7F)&0xFF)
	return o

def u8(*args):
	o=[]
	for arg in args:
		if int(arg)<0: arg = abs(int(arg))
		else: arg = int(arg)
		o.append(int(arg)&0xFF)
	return o

def PaddedString(s, amt, char=" "):
	if len(s)>=amt:
		return s[:amt]
	else:
		return s.ljust(amt, char)

if __name__=='__main__':
	print("ToUTF8 test:",ToUTF8([0x41,0x42,0x43,0x44,0x45,0x00]))
	print("FromSignedInt test:",FromSignedInt(0x7F),FromSignedInt(0xFF),FromSignedInt(0x01),FromSignedInt(0x80))
	print("ToSignedByte test:",hex(ToSignedByte(-100)),hex(ToSignedByte(-120)),hex(ToSignedByte(100)),hex(ToSignedByte(120)))
	print("FromSignedInt(ToSignedByte()) test:",FromSignedInt(ToSignedByte(-100)))
	print("i24 test:", i24(0,20,123456,654321,16777215,0x434241))
	print("u24 test:", u24(0,20,123456,654321,16777215,0x434241))
	print("i16 test:", i16(0,20,65535,33))
	print("u16 test:", i16(0,20,65535,33))
	print("i8 test:", i8(0,2,7,123))
	print("u8 test:", u8(0,2,7,123))
	print("string padding test:", PaddedString("Hello World!", 20),":)")

