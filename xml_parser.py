alphaNumericCharacters="0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz_"
numericCharacters="0123456789.-"

class BNodeValue:
	def __init__(self,name="anon",value=None):
		self.name=name
		self.value=value
		self._parents=[]
	def __str__(self):
		return " ".join([str(self.name)+"=\""+str(self.value)+"\""])
	def parent(self,parent=None):
		if parent==None:
			return self._parents
		else:
			self._parents.append(parent)
			parent.child(self)
	def clearParent(self,name=None):
		if name==None:
			self._parents.clear()
		else:
			for parent in self._parents:
				if parent.name==name:
					self._parents.remove(parent)

class BNode:
	def __init__(self,name="anon"):
		self.name=name
		self._args=[]
		self._parents=[]
		self._children=[]
		self.content=None
		self.endtag=None
	def pretty(self,i):
		o=["","<"+str(self.name)+">: "+str(len(self._args))+" args, "+str(len(self._children))+\
		" children, "+str(len(self._parents))+" parents"]
		for arg in self._args:
			o.append("\\ "+str(arg))
		for child in self._children:
			o.append(child.pretty(i+1))
		if self.content!=None:
			o.append(str(self.content))
		if self.endtag!=None:
			o.append("</"+str(self.endtag)+">")
		return ("\n"+"  "*i).join(o)
	def dict(self):
		return {'name':self.name,'args':self._args,'parents':self._parents,
		'children':self._children,'content':self.content,'endtag':self.endtag}
	def arg(self,arg=None):
		if arg==None:
			return self._args
		else:
			self._args.append(arg)
			arg._parents.append(self)
	def parent(self,parent=None):
		if parent==None:
			return self._parents
		else:
			self._parents.append(parent)
			parent._children.append(self)
	def child(self,child=None):
		if child==None:
			return self._children
		else:
			self._children.append(child)
			child._parents.append(self)
	def clearArg(self,name=None):
		if name==None:
			self._args.clear()
		else:
			for arg in self._args:
				if arg.name==name:
					self._args.remove(arg)
	def clearParent(self,name=None):
		if name==None:
			self._parents.clear()
		else:
			for parent in self._parents:
				if parent.name==name:
					self._parents.remove(parent)
	def clearChild(self,name=None):
		if name==None:
			self._children.clear()
		else:
			for child in self._children:
				if child.name==name:
					self._children.remove(child)
	def walk(self):
		return self.pretty(0)

def parse_XML_data(data,i,name=""):
	myNode=BNode(name)
	while i<len(data):
		dt,i=parse_XML_tag(data,i+1)
		if dt!=None:
			myNode.child(dt)
	myNode.endtag=name
	return myNode,i

def parse_XML_tag(data,i,parent=None):
	dt,i=parse_XML_word(data,i)
	myNode=BNode(dt)
	myNode.parent(parent)
	while i<len(data):
		if data[i]==">":
			myNode.content,i=parse_XML_content(data,i+1,myNode)
		elif data[i]=="\\":
			i+=2
		elif data[i]=="<":
			if data[i+1]=="/":
				dt,i=parse_XML_word(data,i+2)
				myNode.endtag = dt
				return myNode,i
			else:
				dt,i=parse_XML_tag(data,i+1,myNode)
		elif data[i] in alphaNumericCharacters:
			w,i=parse_XML_word(data,i)
			if data[i]=="=":
				v,i=parse_XML_value(data,i+1)
			else:
				v=True
			myNode.arg(BNodeValue(w,v))
		elif data[i]=="/":
			if data[i+1]==">":
				i+=2
				return myNode,i
		else:
			i+=1
	return None,i

def parse_XML_content(data,i,myNode):
	o=[]
	while i<len(data):
		if data[i]=="<":
			break
		else:
			o.append(data[i])
		i+=1
	return "".join(o),i

def parse_XML_value(data,i):
	c=data[i]
	if c in "'\"":
		i+=1; o=[]
		while i<len(data):
			if data[i]==c:
				break
			elif data[i]=="\\":
				i+=1
			o.append(data[i])
			i+=1
		return "".join(o),i+1
	elif c in numericCharacters:
		j=get_next_breaking(data,i,numericCharacters)
		if "." in data[i:j]:
			v=float(data[i:j])
		else:
			v=int(data[i:j])
	elif data[i].startswith("true"):
		return True,i+4
	elif data[i].startswith("false"):
		return False,i+5
	elif data[i].startswith("null"):
		return None,i+4
	else:
		return None,i

def get_next_breaking(data,i,do=alphaNumericCharacters):
	while i<len(data) and data[i] in do:
		i+=1
	return i

def parse_XML_word(data,i):
	o=[]
	while i<len(data) and data[i] in alphaNumericCharacters:
		o.append(data[i])
		i+=1
	return "".join(o),i

if __name__=='__main__':
	data="""<main name="Hello World!"
executable not_a_drill hidden nou="your Mom"><draw>print("Hello World!")</draw></main>"""
	data,i=parse_XML_data(data,0)
	print(data.walk())
