#!/usr/bin/env python


def read_attr(data,attr):
	name=None
	i=0
	while name!=attr:
		if i>=len(data):
			raise NotFoundErr
		name,val,i=_next_attr(data,i)
	return val
def write_attr(data,attr,value=None):
	name=None
	i=0
	o=attr+"="+str(value)+";\n"
	while name!=attr:
		if i>=len(data):
			return data+o
		j=i
		name,val,i=_next_attr(data,i)
	return data[:j]+o+data[j:]
	
def f_read_attr(fname,attr):
	with open(fname) as f:
		return self.read_attr(f.read(),attr)
def f_write_attr(fname,attr,value=None):
	f=open(fname,"r")
	data=self.write_attr(f.read(),attr,value)
	f.close()
	with open(fname,"w") as f:
		f.write(data)

def _next_attr(data,i):
	val=[]
	cur=name=[]
	while i<len(data):
		c=data[i]; i+=1
		if c in "\n\t ":
			continue
		elif c==";":
			return "".join(name),"".join(val),i
		elif c=="=":
			if cur is val:
				raise SyntaxErr
			else:
				cur=val
		else:
			cur.append(c)

if __name__=='__main__':
	data="""
	string="Hello World!";
	value=0x10;
	A="A";
	Array=[1,2,3,4];
	"""
	attrs=["string","value","A","Array"]
	for s in attrs:
		print(read_attr(data,s))
	for i in attrs:
		data=write_attr(data,i,1000);
		for s in attrs:
				print(read_attr(data,s))
